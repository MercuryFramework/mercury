from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import json
import hmac
import hashlib
import time
import base64
class JWT:
	def __init__(self, token):
		self.token = token
		self.header = {} 
		self.payload = {} 
		self.signature = "" 
		if token != "" and token != None:
			self._parse_token()

	def _parse_token(self):
		parts = self.token.split('.')
		if len(parts) != 3:
			raise ValueError("Invalid JWT token format")

		self.header = self._base64_url_decode(parts[0])
		self.payload = self._base64_url_decode(parts[1])
		self.signature = parts[2]

	def _base64_url_decode(self, input_str):
		# Add padding if needed
		input_str += '=' * (4 - len(input_str) % 4)
		decoded_bytes = base64.urlsafe_b64decode(input_str)
		return json.loads(decoded_bytes)

	def _base64_url_encode(self, data):
		encoded = base64.urlsafe_b64encode(data).decode('utf-8')
		return encoded.rstrip('=')

	def get_header(self):
		return self.header

	def get_payload(self):
		return self.payload

	def get_signature(self):
		return self.signature

	def verify_signature(self, pem_file_path):
		if self.token == None or self.token == "":
			return False

		#Check to see if the token is valid
		try:
			if self.payload.get("exp") and int(time.time()) > int(self.payload.get("exp")):
				return False
		except ValueError:
			return False

		with open(pem_file_path, 'rb') as pem_file:
			key_data = pem_file.read()

		header_encoded, payload_encoded, signature_encoded = self.token.split('.')
		
		if self.header['alg'] == 'HS256':
			expected_signature = hmac.new(
				key_data,
				f'{header_encoded}.{payload_encoded}'.encode(),
				hashlib.sha256
			).digest()
			
			# Decode the JWT signature
			decoded_signature = base64.urlsafe_b64decode(self.signature + '=' * (4 - len(self.signature) % 4))

			return hmac.compare_digest(decoded_signature, expected_signature)
		
		elif self.header['alg'] == 'RS256':
			message = f'{header_encoded}.{payload_encoded}'.encode()
			decoded_signature = base64.urlsafe_b64decode(self.signature + '=' * (4 - len(self.signature) % 4))
			rsa_key = RSA.import_key(key_data)
			h = SHA256.new(message)
			try:
				pkcs1_15.new(rsa_key).verify(h, decoded_signature)
				return True
			except (ValueError, TypeError):
				return False

		else:
			return False

	def to_string(self):
		header_encoded = self._base64_url_encode(json.dumps(self.header).encode())
		payload_encoded = self._base64_url_encode(json.dumps(self.payload).encode())
		return f"{header_encoded}.{payload_encoded}.{self.signature}"

	def sign(self, private_key_path, key_type):
		if key_type.upper() == "RSA":
			key_type = "RS256"
		else:
			key_type = "HS256"

		if self.header == {}:
			self.header = {"alg": key_type, "typ": "JWT"}

		with open(private_key_path, 'rb') as pem_file:
			key_data = pem_file.read()

		header_encoded = self._base64_url_encode(json.dumps(self.header).encode())
		payload_encoded = self._base64_url_encode(json.dumps(self.payload).encode())
		message = f"{header_encoded}.{payload_encoded}".encode()

		if key_type == 'HS256':
			new_signature = hmac.new(key_data, message, hashlib.sha256).digest()
		elif key_type == 'RS256':
			rsa_key = RSA.import_key(key_data)
			h = SHA256.new(message)
			new_signature = pkcs1_15.new(rsa_key).sign(h)
		else:
			raise ValueError(f"Unsupported algorithm: {key_type}")
		self.signature = self._base64_url_encode(new_signature)
		return self.to_string()
