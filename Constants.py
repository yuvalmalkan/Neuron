import logging
from UserDatabase import UserDatabase
import os


debug = True





log_level = logging.DEBUG if debug else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)




root_dir = os.path.dirname(os.path.abspath(__file__))  # Current directory
db_path = os.path.join(root_dir, 'Databases', 'users.pkl')
user_db = UserDatabase(db_path)

port = 34401
serverIp = "0.0.0.0"



#todo שרת ללקוח
#התחברות רישום והודעות
CMD_LOGIN = "LOGIN"
CMD_SIGNUP = "SGNUP"
CMD_EXIT = "EXITT"


#אימות ושחזור סיסמה
CMD_VERIFY = "VRIFY"
CMD_RESEND = "RSEND"
CMD_FORGOT = "FRGOT"
CMD_RESET = "RESET"


"""
#החלפת מפתחות והצפנה
CMD_CHOOSE_KEY = "CHKEY"
CMD_REQ_PUBKEY = "RQPUB"
CMD_SEND_AES = "SDAES"

"""





#todo שרת ללקוח
#תשובות כלליות והתחברות
RESP_LOGIN_OK = "OKLOG"
RESP_SIGNUP_OK = "OKSNP"
RESP_ERROR = "ERROR"

# Signup response codes
RESP_SIGNUP_USER_EXISTS = "EUSER"
RESP_SIGNUP_EMAIL_EXISTS = "EEML"
RESP_SIGNUP_INVALID_USERNAME = "EUNAM"
RESP_SIGNUP_INVALID_EMAIL = "EINML"
RESP_SIGNUP_INVALID_PASSWORD = "EPWD"

# Login response codes
RESP_LOGIN_FAIL = "FLOG"
RESP_LOGIN_USER_NOT_FOUND = "UFND"






#אימות ושחזור סיסמה
RESP_OTP_SENT = "OTPOK"
RESP_VERIFY_OK = "OKVRF"
RESP_RESET_OK = "OKRST"
RESP_ERROR_EMAIL_EXISTS = "EREML"




"""
#החלפת מפתחות והצפנה
RESP_KEY_SUP = "OKKEY"
RESP_KEY_NSUP = "NOKEY"
RESP_PUBKEY = "PUBKY"
RESP_AES_OK = "AESOK"

"""