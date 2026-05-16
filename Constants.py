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
CMD_LOGIN = "LOGIN"
CMD_SIGNUP = "SGNUP"
CMD_EXIT = "EXITT"

CMD_VERIFY = "VRIFY"
CMD_RESEND = "RSEND"
CMD_FORGOT = "FRGOT"
CMD_RESET = "RESET"

# ── P2P CHAT COMMANDS ──
CMD_CHAT_INIT = "CINIT"     # Registers the chat socket with the server
CMD_FETCH_USERS = "FUSRS"   # Request list of online users
CMD_CHAT_REQUEST = "CREQ"   # Send request to a peer
CMD_CHAT_ACCEPT = "CACC"    # Accept incoming request
CMD_CHAT_DECLINE = "CDEC"   # Decline incoming request
CMD_DIRECT_MSG = "DMSG"     # Send actual message payload
CMD_END_SESSION = "ESESS"   # Notify peer the session is terminated

# ── RESPONSES ──
RESP_LOGIN_OK = "OKLOG"
RESP_SIGNUP_OK = "OKSNP"
RESP_ERROR = "ERROR"

RESP_SIGNUP_USER_EXISTS = "EUSER"
RESP_SIGNUP_EMAIL_EXISTS = "EEML"
RESP_SIGNUP_INVALID_USERNAME = "EUNAM"
RESP_SIGNUP_INVALID_EMAIL = "EINML"
RESP_SIGNUP_INVALID_PASSWORD = "EPWD"

RESP_LOGIN_FAIL = "FLOG"
RESP_LOGIN_USER_NOT_FOUND = "UFND"

RESP_OTP_SENT = "OTPOK"
RESP_VERIFY_OK = "OKVRF"
RESP_RESET_OK = "OKRST"
RESP_ERROR_EMAIL_EXISTS = "EREML"