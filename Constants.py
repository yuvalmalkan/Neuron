__author__ = "Yuval Malkan"
import logging
from UserDatabase import UserDatabase
import os

debug = True

log_level = logging.DEBUG if debug else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

root_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(root_dir, 'Databases', 'users.pkl')
user_db = UserDatabase(db_path)

port = 34401
serverIp = "0.0.0.0"

# ── GENERAL & AUTH COMMANDS ──
CMD_LOGIN = "LOGIN"         # Client request to authenticate an existing user session
CMD_SIGNUP = "SGNUP"        # Client request to register and create a new user account
CMD_EXIT = "EXITT"          # Client notification to the server that it is disconnecting

CMD_VERIFY = "VRIFY"        # Client request to verify a user's account (e.g., OTP submission)
CMD_RESEND = "RSEND"        # Client request to resend an OTP or verification code
CMD_FORGOT = "FRGOT"        # Client request to initiate the forgot-password recovery flow
CMD_RESET = "RESET"         # Client request to submit a new password using a recovery token

# ── CHAT COMMANDS ──
CMD_CHAT_INIT = "CINIT"     # Registers the client's chat socket with the server for P2P routing
CMD_FETCH_USERS = "FUSRS"   # Requests the list of all currently online users
CMD_CHAT_REQUEST = "CREQU"  # Sends a P2P chat session request to a target peer
CMD_CHAT_ACCEPT = "CACCP"   # Accepts an incoming P2P chat session request
CMD_CHAT_DECLINE = "CDECL"  # Declines an incoming P2P chat session request
CMD_DIRECT_MSG = "DMSGS"    # Routes a direct text message to the active peer through the server
CMD_END_SESSION = "ESESS"   # Notifies the server and peer that the current chat session is ending

# ── RESPONSES ──
RESP_LOGIN_OK = "OKLOG"                   # Server response: User successfully logged in
RESP_SIGNUP_OK = "OKSNP"                  # Server response: User account successfully created
RESP_ERROR = "ERROR"                      # Server response: A general or malformed request error occurred

RESP_SIGNUP_USER_EXISTS = "EUSER"         # Server response: Signup failed because the username is already taken
RESP_SIGNUP_EMAIL_EXISTS = "EEMAI"        # Server response: Signup failed because the email is already registered
RESP_SIGNUP_INVALID_USERNAME = "EUNAM"    # Server response: Signup failed due to an invalid username format
RESP_SIGNUP_INVALID_EMAIL = "EINML"       # Server response: Signup failed due to an invalid email format
RESP_SIGNUP_INVALID_PASSWORD = "EPWDS"    # Server response: Signup failed due to a weak or invalid password

RESP_LOGIN_FAIL = "FLOGN"                 # Server response: Login failed (incorrect password)
RESP_LOGIN_USER_NOT_FOUND = "UFNDS"       # Server response: Login failed (username does not exist in DB)

RESP_OTP_SENT = "OTPOK"                   # Server response: One-Time Password sent successfully
RESP_VERIFY_OK = "OKVRF"                  # Server response: Account verification successful
RESP_RESET_OK = "OKRST"                   # Server response: Password successfully reset
RESP_ERROR_EMAIL_EXISTS = "EREML"         # Server response: Error, email already linked to another account

#OSINT COMMANDS
CMD_OSINT_USCAN = "USCAN"   # Client request to initiate a background Username OSINT scan
CMD_OSINT_ESCAN = "ESCAN"   # Client request to initiate a background Email OSINT scan
CMD_OSINT_PSCAN = "PSCAN"   # Client request to initiate a background Phone OSINT scan

#OSINT RESPONSES
RESP_OSINT_RESULT = "ORSLT"       # Server response: Email/Username scan completed successfully with data
RESP_OSINT_ERROR = "OERRS"        # Server response: OSINT scan failed, crashed, or timed out
RESP_OSINT_PHONE_RESULT = "OPLTS" # Server response: Phone scan completed successfully with data