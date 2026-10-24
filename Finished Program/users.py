# Users (ABSTRACTION and INHERITANCE and POLYMORPHISM) and the login lockout.
from __future__ import annotations

import hashlib
import hmac
import math
import os
import time
from abc import ABC, abstractmethod

from config import LOCKOUT_SECONDS, MAX_LOGIN_ATTEMPTS, MIN_PASSWORD_LENGTH
from errors import AccountLockedError, AuthenticationError, PermissionDeniedError, ValidationError
from validators import validate_contact, validate_email, validate_username

_ITERATIONS = 100_000


# base class for all accounts, can't be used directly
class User(ABC):
    # role name that is saved in users.csv
    ROLE = "user"
    # what this role is allowed to do
    PERMISSIONS: frozenset = frozenset()

    def __init__(self, username, password_hash, full_name="", email="", contact=""):
        # attributes start with _ so they are only changed through the methods
        self._username = validate_username(username)
        self._password_hash = password_hash
        self._full_name = str(full_name or "").strip()
        self._email = validate_email(email)
        self._contact = validate_contact(contact)

    # read-only info (ENCAPSULATION)
    @property
    def username(self) -> str:
        return self._username

    @property
    def full_name(self) -> str:
        return self._full_name or self._username

    @property
    def email(self) -> str:
        return self._email

    @property
    def contact(self) -> str:
        return self._contact

    @property
    def password_hash(self) -> str:
        return self._password_hash

    # ABSTRACTION: every role MUST say what its screen is called
    @abstractmethod
    def dashboard_title(self) -> str:
        # Title the GUI shows for this role.
        pass

    # POLYMORPHISM: same call, different answer per role
    def greeting(self) -> str:
        return f"Welcome, {self.full_name}!"

    # passwords
    @staticmethod
    def hash_password(password: str) -> str:
        # Salted PBKDF2. Stored as 'salt$hash'; the real password is never saved.
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        # random salt so the same password gives a different hash
        salt = os.urandom(16)
        # slow hash on purpose so guessing passwords is hard
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
        return f"{salt.hex()}${digest.hex()}"

    def verify_password(self, password: str) -> bool:
        try:
            salt_hex, digest_hex = self._password_hash.split("$")
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", str(password).encode(), salt, _ITERATIONS)
        # safe way to compare the two hashes
        return hmac.compare_digest(digest.hex(), digest_hex)

    def change_password(self, old_password: str, new_password: str):
        if not self.verify_password(old_password):
            raise AuthenticationError("Current password is incorrect.")
        if old_password == new_password:
            raise ValidationError("New password must be different from the current one.")
        self._password_hash = self.hash_password(new_password)

    def reset_password(self, new_password: str):
        # Admin reset: no old password needed.
        self._password_hash = self.hash_password(new_password)

    def restore_hash(self, old_hash: str):
        # Undo a password change when the file could not be saved.
        self._password_hash = old_hash

    # permissions
    # true if this role is allowed to do the action
    def can(self, action: str) -> bool:
        return action in self.PERMISSIONS

    # stops the action with an error if the role is not allowed
    def require(self, action: str):
        if not self.can(action):
            raise PermissionDeniedError(f"{self.ROLE.title()} accounts are not allowed to do that.")

    def to_row(self) -> dict:
        return {"username": self._username, "password_hash": self._password_hash,
                "role": self.ROLE, "full_name": self._full_name,
                "email": self._email, "contact": self._contact}


# cashier can only sell
class Cashier(User):
    ROLE = "cashier"
    PERMISSIONS = frozenset({"sell"})

    def dashboard_title(self) -> str:
        return "Cashier Terminal"

    def greeting(self) -> str:
        return f"Ready to sell, {self.full_name}!"


# manager can also manage items, restock and see reports
class Manager(User):
    ROLE = "manager"
    PERMISSIONS = frozenset({"sell", "manage_items", "restock", "view_reports"})

    def dashboard_title(self) -> str:
        return "Manager Dashboard"

    def greeting(self) -> str:
        return f"Welcome back, Manager {self.full_name}."


# admin can do everything, including void and manage users
class Admin(User):
    ROLE = "admin"
    PERMISSIONS = frozenset({"sell", "manage_items", "restock", "view_reports",
                             "manage_users", "void_sales"})

    def dashboard_title(self) -> str:
        return "Admin Dashboard"

    def greeting(self) -> str:
        return f"Administrator {self.full_name} signed in."


# turns the role text from the csv into the right class
ROLE_CLASSES = {c.ROLE: c for c in (Cashier, Manager, Admin)}


class LoginGuard:
    # Locks a username for a while after too many wrong passwords.
    # Kept in memory, so restarting the program clears all locks. `clock` can be
    # replaced in tests so we don't have to wait a real 60 seconds.

    def __init__(self, max_attempts=MAX_LOGIN_ATTEMPTS, lock_seconds=LOCKOUT_SECONDS,
                 clock=time.monotonic):
        self._max = max_attempts
        self._lock_seconds = lock_seconds
        self._clock = clock
        self._failures: dict[str, int] = {}
        self._locked_until: dict[str, float] = {}

    @staticmethod
    def _key(username) -> str:
        return str(username).strip().lower()

    def check(self, username):
        # Raise AccountLockedError if this username is currently locked.
        key = self._key(username)
        until = self._locked_until.get(key)
        if until is None:
            return
        remaining = until - self._clock()
        if remaining > 0:
            raise AccountLockedError(
                f"Too many failed attempts. Try again in {math.ceil(remaining)} seconds."
            )
        del self._locked_until[key]       # lock expired
        self._failures.pop(key, None)

    def record_failure(self, username):
        key = self._key(username)         # unknown usernames are counted too,
        count = self._failures.get(key, 0) + 1   # so locks don't reveal which exist
        if count >= self._max:
            self._locked_until[key] = self._clock() + self._lock_seconds
            self._failures.pop(key, None)
        else:
            self._failures[key] = count

    def reset(self, username):
        key = self._key(username)
        self._failures.pop(key, None)
        self._locked_until.pop(key, None)