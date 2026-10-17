from decimal import Decimal

# placeholder settings so the program can run, change them to your group's real ones
STORE_NAME = "Group 1 Grocery"
STORE_ADDRESS = "Quezon City"

# these have to be Decimal, not float, because the money math uses Decimal
VAT_RATE = Decimal("0.12")
SENIOR_PWD_RATE = Decimal("0.20")

MAX_QTY = 99
MIN_PASSWORD_LENGTH = 6

# 3 wrong passwords locks the username for 60 seconds
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_SECONDS = 60

# how many characters wide the receipt is
RECEIPT_WIDTH = 40
