from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import base64
def generate_salt() -> bytes:
	"""Generate a random salt."""
	return get_random_bytes(16)

# Function to hash a password with a given salt
def hash_password(password: str, salt: bytes) -> str:
	"""Hash a password with a given salt using PBKDF2."""
	key = PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)
	return base64.b64encode(key).decode('utf-8')

# Function to verify a password against the stored hash
def verify_password(stored_password: str, password: str, salt: bytes) -> bool:
	"""Verify a password against the stored hash."""
	hashed_password = hash_password(password, salt)
	return stored_password == hashed_password
