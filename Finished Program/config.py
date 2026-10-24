# settings for the whole program, change the store details here
from decimal import Decimal
from pathlib import Path

# folders and files 
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGO_PATH = BASE_DIR / "logo.jpg"

# store details shown on the receipt and the login page
STORE_NAME = "EcoBasket Supermarket"
STORE_ADDRESS = " 938 Aurora Blvd., Cubao, Quezon City, 1109 Metro Manila, Philippines"
RECEIPT_WIDTH = 40

# rates must be Decimal
VAT_RATE = Decimal("0.12")
FIXED_DISCOUNT_RATE = Decimal("0.20")

# limits
MAX_QTY = 999
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_SECONDS = 60
MIN_PASSWORD_LENGTH = 6

# first-run admin account, change the password after logging in
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"