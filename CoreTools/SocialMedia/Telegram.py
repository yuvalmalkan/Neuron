__author__ = 'Yuval Malkan'

import asyncio
import json
import os
import io
import base64
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.contacts import (
    ImportContactsRequest,
    DeleteContactsRequest,
    SearchRequest,
    GetContactsRequest
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputPhoneContact
from telethon.errors import FloodWaitError, UsernameNotOccupiedError, UsernameInvalidError

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neuron")

# Setup temp folder
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TEMP_FOLDER = os.path.join(BASE_DIR, "CoreTools", "temp")
os.makedirs(TEMP_FOLDER, exist_ok=True)


#helper functions

def _clean_name(first, last):
    first = (first or "").strip()
    last = (last or "").strip()
    full = " ".join(filter(None, [first, last])).strip()
    # Ignore placeholder names like ". ."
    if all(c in ". " for c in full):
        return None
    return full or None


async def _download_photo(client, user, user_id) -> dict:
    """Download profile photo to disk + base64. Saves to temp folder with user_id as filename."""
    photo_info = {}
    try:
        buf = io.BytesIO()
        await client.download_profile_photo(user, file=buf)
        buf.seek(0)
        photo_bytes = buf.read()
        if photo_bytes:
            filename = f"{user_id}.jpg"  # Just use user_id as filename
            filepath = os.path.join(TEMP_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(photo_bytes)
            photo_info["profile_photo_saved"] = filename
            photo_info["profile_photo_path"] = filepath
            photo_info["profile_photo_size_kb"] = round(len(photo_bytes) / 1024, 1)
            photo_info["profile_photo_base64"] = base64.b64encode(photo_bytes).decode()
    except Exception as e:
        photo_info["photo_download_error"] = str(e)
    return photo_info


def _extract_user_info(user) -> dict:
    """Extract all available info from a Telegram user object."""
    return {
        "telegram_id": user.id,
        "username": f"@{user.username}" if user.username else None,
        "first_name": (user.first_name or "").strip() or None,
        "last_name": (user.last_name or "").strip() or None,
        "full_name": _clean_name(user.first_name, user.last_name),
        "is_bot": user.bot,
        "is_verified": user.verified,
        "is_scam": user.scam,
        "is_fake": user.fake,
        "is_premium": getattr(user, "premium", False),
        "is_deleted": getattr(user, "deleted", False),
        "lang_code": getattr(user, "lang_code", None),
        "profile_url": f"https://t.me/{user.username}" if user.username else None,
        "has_profile_photo": bool(user.photo),
        "photo_id": user.photo.photo_id if user.photo else None,
        # Phone only visible if user made it public
        "phone_visible": getattr(user, "phone", None),
    }


async def _get_full_user_bio(client, user) -> str | None:
    """Fetch bio/about from full user profile."""
    try:
        full = await client(GetFullUserRequest(user))
        return getattr(full.full_user, "about", None)
    except Exception:
        return None


def _save_result_json(result: dict, filename: str) -> str:
    """Save result to JSON file in temp folder."""
    filepath = os.path.join(TEMP_FOLDER, filename)
    # Don't save base64 to disk (it's huge)
    result_clean = dict(result)
    result_clean.pop("profile_photo_base64", None)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_clean, f, indent=2, ensure_ascii=False)
    return filepath


# ─── 1. LOOKUP BY PHONE ───────────────────────────────────────────────────────

async def lookup_by_phone(client: TelegramClient, phone: str) -> dict:
    """
    Look up a Telegram user by phone number.
    Temporarily adds as contact, extracts info, then removes.
    """
    contact = InputPhoneContact(
        client_id=0, phone=phone,
        first_name="OSINT", last_name="Query"
    )
    result = {"source": "telegram", "method": "phone", "phone": phone, "registered": False}

    try:
        imported = await client(ImportContactsRequest([contact]))
        users = imported.users
        if not users:
            return result

        user = users[0]
        result["registered"] = True
        result.update(_extract_user_info(user))
        result["bio"] = await _get_full_user_bio(client, user)

        if user.photo:
            result.update(await _download_photo(client, user, user.id))

        await client(DeleteContactsRequest([user]))

        # Save to temp folder
        safe_phone = phone.replace("+", "").replace(" ", "_")
        _save_result_json(result, f"telegram_phone_{safe_phone}.json")

    except FloodWaitError as e:
        result["error"] = f"Flood wait: {e.seconds}s"
    except Exception as e:
        result["error"] = str(e)

    return result


# ─── 2. LOOKUP BY USERNAME ────────────────────────────────────────────────────

async def lookup_by_username(client: TelegramClient, username: str) -> dict:
    """
    Look up a Telegram user by @username.
    Username can be with or without @.
    """
    username = username.lstrip("@")
    result = {"source": "telegram", "method": "username", "username": f"@{username}", "found": False}

    try:
        user = await client.get_entity(f"@{username}")
        result["found"] = True
        result.update(_extract_user_info(user))
        result["bio"] = await _get_full_user_bio(client, user)

        if user.photo:
            result.update(await _download_photo(client, user, user.id))

        # Save to temp folder
        _save_result_json(result, f"telegram_username_{username}.json")

    except (UsernameNotOccupiedError, UsernameInvalidError):
        result["error"] = "Username not found"
    except FloodWaitError as e:
        result["error"] = f"Flood wait: {e.seconds}s"
    except Exception as e:
        result["error"] = str(e)

    return result


# ─── 3. SEARCH BY NAME ────────────────────────────────────────────────────────

async def search_by_name(client: TelegramClient, name: str, limit: int = 10) -> dict:
    """
    Search Telegram's global search for a name.
    Returns public profiles that match.
    Only finds users who have made their profile discoverable.
    """
    result = {
        "source": "telegram",
        "method": "name_search",
        "query": name,
        "results": []
    }

    try:
        search = await client(SearchRequest(q=name, limit=limit))
        for user in search.users:
            info = _extract_user_info(user)
            result["results"].append(info)

        # Save to temp folder
        safe_name = name.replace(" ", "_").lower()
        _save_result_json(result, f"telegram_search_{safe_name}.json")

    except FloodWaitError as e:
        result["error"] = f"Flood wait: {e.seconds}s"
    except Exception as e:
        result["error"] = str(e)

    return result


# ─── 4. GET MUTUAL CONTACTS ───────────────────────────────────────────────────

async def get_mutual_contacts(client: TelegramClient) -> dict:
    """
    Get all Telegram users who are in your contacts AND have you in theirs.
    Useful for mapping social connections.
    """
    result = {
        "source": "telegram",
        "method": "mutual_contacts",
        "contacts": []
    }

    try:
        contacts = await client(GetContactsRequest(hash=0))
        for user in contacts.users:
            info = _extract_user_info(user)
            result["contacts"].append(info)
        result["total"] = len(result["contacts"])

        # Save to temp folder
        _save_result_json(result, "telegram_contacts.json")

    except Exception as e:
        result["error"] = str(e)

    return result


# ─── 5. DOWNLOAD PHOTO BY USERNAME ───────────────────────────────────────────

async def download_photo_by_username(client: TelegramClient, username: str) -> dict:
    """Download profile photo of any public Telegram user by username."""
    username = username.lstrip("@")
    try:
        user = await client.get_entity(f"@{username}")
        if not user.photo:
            return {"source": "telegram", "error": "User has no profile photo"}
        result = {
            "source": "telegram",
            "username": f"@{username}",
            **await _download_photo(client, user, user.id)
        }
        # Save metadata to temp folder
        _save_result_json(result, f"telegram_photo_{username}.json")
        return result
    except Exception as e:
        return {"source": "telegram", "error": str(e)}


# ─── 6. FIND PHONE BY USERNAME/NAME ──────────────────────────────────────────

async def find_phone_by_username(client: TelegramClient, username: str) -> dict:
    """
    Try to find the phone number of a user by their username.
    Only works if the user has set their phone to 'visible to everyone'
    in Telegram privacy settings — most users keep this private.
    """
    username = username.lstrip("@")
    result = {
        "source": "telegram",
        "method": "phone_from_username",
        "username": f"@{username}",
        "phone": None
    }

    try:
        user = await client.get_entity(f"@{username}")
        phone = getattr(user, "phone", None)

        if phone:
            result["phone"] = f"+{phone}"
            result["found"] = True
        else:
            result["found"] = False
            result["note"] = "Phone is private — user has restricted visibility"

        result.update(_extract_user_info(user))

        # Save to temp folder
        _save_result_json(result, f"telegram_findphone_{username}.json")

    except Exception as e:
        result["error"] = str(e)

    return result


async def find_phone_by_name(client: TelegramClient, name: str) -> dict:
    """
    Search by name and attempt to extract phone from each result.
    Phone will only appear if user made it public.
    """
    search_result = await search_by_name(client, name, limit=20)
    phones_found = []

    for user_info in search_result.get("results", []):
        if user_info.get("phone_visible"):
            phones_found.append({
                "name": user_info.get("full_name"),
                "username": user_info.get("username"),
                "phone": f"+{user_info['phone_visible']}",
                "id": user_info.get("telegram_id"),
            })

    result = {
        "source": "telegram",
        "method": "phone_from_name",
        "query": name,
        "phones_found": phones_found,
        "total_searched": len(search_result.get("results", [])),
        "note": "Only shows phones of users who set visibility to 'Everyone'"
    }

    # Save to temp folder
    safe_name = name.replace(" ", "_").lower()
    _save_result_json(result, f"telegram_findphone_{safe_name}.json")

    return result


# main async

async def telegram_lookup_phone(phone: str) -> dict:
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        return await lookup_by_phone(client, phone)


async def telegram_lookup_username(username: str) -> dict:
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        return await lookup_by_username(client, username)


async def telegram_search_name(name: str, limit: int = 10) -> dict:
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        return await search_by_name(client, name, limit)


async def telegram_get_contacts() -> dict:
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        return await get_mutual_contacts(client)


async def telegram_find_phone(username: str = None, name: str = None) -> dict:
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        if username:
            return await find_phone_by_username(client, username)
        if name:
            return await find_phone_by_name(client, name)
        return {"error": "Provide username or name"}


# sync wrappers

def lookup_phone_sync(phone: str) -> dict:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(telegram_lookup_phone(phone))
    finally:
        loop.close()

def lookup_username_sync(username: str) -> dict:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(telegram_lookup_username(username))
    finally:
        loop.close()




def search_name_sync(name: str, limit: int = 10) -> dict:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(telegram_search_name(name, limit))
    finally:
        loop.close()

def get_contacts_sync() -> dict:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(telegram_get_contacts())
    finally:
        loop.close()

def find_phone_sync(username: str = None, name: str = None) -> dict:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(telegram_find_phone(username=username, name=name))
    finally:
        loop.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 Telegram.py phone +972501234567")
        print("  python3 Telegram.py username @someone")
        print("  python3 Telegram.py name 'Ophir Shavit'")
        print("  python3 Telegram.py findphone @someone")
        print(f"\nSaving to: {TEMP_FOLDER}")
        sys.exit(0)

    mode = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else ""

    if mode == "phone":
        result = lookup_phone_sync(arg)
    elif mode == "username":
        result = lookup_username_sync(arg)
    elif mode == "name":
        result = search_name_sync(arg)
    elif mode == "findphone":
        result = find_phone_sync(username=arg)
    else:
        result = {"error": f"Unknown mode: {mode}"}

    # Don't print base64
    display = {k: v for k, v in result.items() if k != "profile_photo_base64"}
    print(json.dumps(display, indent=2, ensure_ascii=False))
    print(f"\n✓ Results saved to: {TEMP_FOLDER}")
