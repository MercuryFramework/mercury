import os
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from colorama import Fore, Style

def save_key_to_file(path, filename, key_data):
	os.makedirs(path, exist_ok=True)
	with open(os.path.join(path, filename), 'wb') as file:
		file.write(key_data)

def generate_hmac_key(name, path):
	secret_key = get_random_bytes(32)  # 256-bit key
	save_key_to_file(path, f'{name}Hmac_secret.key', secret_key)
	print(f"{Fore.MAGENTA}[KEYGEN]{Style.RESET_ALL} HMAC secret key saved to {os.path.join(path, f'{name}Hmac_secret.key')}")

def generate_rsa_keys(name, path):
	key = RSA.generate(2048)
	private_key = key.export_key()
	public_key = key.publickey().export_key()
	save_key_to_file(path, f'{name}Private_key.pem', private_key)
	save_key_to_file(path, f'{name}Public_key.pem', public_key)
	print(f"{Fore.MAGENTA}[KEYGEN]{Style.RESET_ALL} RSA private key saved to {os.path.join(path, f'{name}Public_key.pem')}")
	print(f"{Fore.MAGENTA}[KEYGEN]{Style.RESET_ALL} RSA public key saved to {os.path.join(path, f'{name}Private_key.pem')}")

def main(name):
	path = 'src/.vault'
	key_type = input("What kind of key do you want to generate? (HMAC/RSA): ").strip().upper()

	if key_type == 'HMAC':
		generate_hmac_key(name, path)
		return "HMAC"
	elif key_type == 'RSA':
		generate_rsa_keys(name, path)
		return "RSA"
	else:
		print("Invalid key type. Please choose either 'HMAC' or 'RSA'.")
