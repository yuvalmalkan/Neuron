__author__ = "Yuval Malkan"

"""
REQUIREMENTS:
    pip install telethon

"""

import asyncio
import json
import os
import base64
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact
from telethon.errors import FloodWaitError

load_dotenv()

API_ID   = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION  = "neuron"


async def _lookup_phone(client: TelegramClient, phone: str) -> dict:
    contact = InputPhoneContact(
        client_id=0,
        phone=phone,
        first_name="OSINT",
        last_name="Query"
    )

    result = {
        "source": "telegram",
        "phone": phone,
        "registered": False
    }

    try:
        imported = await client(ImportContactsRequest([contact]))
        users = imported.users

        if not users:
            return result

        user = users[0]


        first = (user.first_name or "").strip()
        last  = (user.last_name  or "").strip()
        full  = " ".join(filter(None, [first, last])).strip()

        result["registered"]    = True
        result["telegram_id"]   = user.id
        result["username"]      = f"@{user.username}" if user.username else None
        result["first_name"]    = first or None
        result["last_name"]     = last  or None
        result["full_name"]     = full  or None
        result["phone_visible"] = getattr(user, "phone", None)
        result["is_bot"]        = user.bot
        result["is_verified"]   = user.verified
        result["is_scam"]       = user.scam
        result["is_fake"]       = user.fake
        result["is_premium"]    = getattr(user, "premium", False)
        result["profile_url"]   = f"https://t.me/{user.username}" if user.username else None
        result["lang_code"]     = getattr(user, "lang_code", None)

        # Download profile photo and convert to base64
        if user.photo:
            result["has_profile_photo"] = True
            result["photo_id"] = user.photo.photo_id
            try:
                # Download to bytes in memory
                import io
                buf = io.BytesIO()
                await client.download_profile_photo(user, file=buf)
                buf.seek(0)
                photo_bytes = buf.read()
                if photo_bytes:
                    result["profile_photo_base64"] = base64.b64encode(photo_bytes).decode()
                    result["profile_photo_size_kb"] = round(len(photo_bytes) / 1024, 1)

                    # Also save to disk as jpeg
                    photo_filename = f"tg_photo_{user.id}.jpg"
                    with open(photo_filename, "wb") as f:
                        f.write(photo_bytes)
                    result["profile_photo_saved"] = photo_filename
            except Exception as e:
                result["photo_download_error"] = str(e)
        else:
            result["has_profile_photo"] = False

        # clean up
        await client(DeleteContactsRequest([user]))

    except FloodWaitError as e:
        result["error"] = f"Flood wait: {e.seconds}s. Try again later."
    except Exception as e:
        result["error"] = str(e)

    return result


async def telegram_lookup_phone(phone: str) -> dict:
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        return await _lookup_phone(client, phone)


async def telegram_bulk_lookup(phones: list) -> list:
    results = []
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        for phone in phones:
            result = await _lookup_phone(client, phone)
            results.append(result)
            await asyncio.sleep(2)
    return results


def lookup_phone_sync(phone: str) -> dict:
    return asyncio.run(telegram_lookup_phone(phone))

def bulk_lookup_sync(phones: list) -> list:
    return asyncio.run(telegram_bulk_lookup(phones))


if __name__ == "__main__":
    PHONE = ""
    result = lookup_phone_sync(PHONE)


    display = {k: v for k, v in result.items() if k != "profile_photo_base64"}
    print(json.dumps(display, indent=2, ensure_ascii=False))
    if result.get("profile_photo_saved"):
        print(f"\nProfile photo saved to: {result['profile_photo_saved']}")
