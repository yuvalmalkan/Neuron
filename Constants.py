import logging

#todo DEBUG MODE

debug = True





log_level = logging.DEBUG if debug else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)





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



#אימות ושחזור סיסמה
RESP_OTP_SENT = "OTPOK"
RESP_VERIFY_OK = "OKVRF"
RESP_RESET_OK = "OKRST"




"""
#החלפת מפתחות והצפנה
RESP_KEY_SUP = "OKKEY"
RESP_KEY_NSUP = "NOKEY"
RESP_PUBKEY = "PUBKY"
RESP_AES_OK = "AESOK"

"""