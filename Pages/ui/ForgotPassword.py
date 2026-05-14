__author__ = "Yuval Malkan"

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from Pages.ui.uiElements import GlowInput, GlowingButton
import logging
import pickle
from Constants import *
from UserDatabase import UserDatabase
from Pages.logic.ForgotPasswordLogic import HandleSendOTPClicked, HandleOTPSubmit


class ForgotPasswordForm(QWidget):
    #fixme write forgot password form, with a 5 minute code sent to email and input field to enter code and new password

    #todo add new password input and submit button
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)


        self.email_input = GlowInput("Email Address")

        self.sendOTP_btn = GlowingButton("SEND VERIFICATION CODE", "primary")

        self.OTP_input = GlowInput("Password Reset Code")


        self.Submit_OTP_btn = GlowingButton("SUBMIT CODE", "primary")



        self.switch_btn = GlowingButton("SWITCH BACK TO LOGIN", "danger")



        self.switch_btn.clicked.connect(lambda: self.window().show_login())
        self.sendOTP_btn.clicked.connect(lambda: HandleSendOTPClicked(self))
        self.Submit_OTP_btn.clicked.connect(lambda: HandleOTPSubmit(self))
        #todo connect Submit_OTP_btn to function



        layout.addWidget(self.email_input)
        layout.addSpacing(30)
        layout.addWidget(self.sendOTP_btn)
        layout.addWidget(self.OTP_input)
        layout.addWidget(self.Submit_OTP_btn)
        layout.addStretch()

        layout.addWidget(self.switch_btn)


        #todo make it so when the send code is clicked a text will appear saying "Verification code sent to email" and then show the input fields for the code and new password, and a button to submit the new password








