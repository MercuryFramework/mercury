from colorama import Fore, Style
from json import loads, dumps
from time import time
import os
import inspect
import importlib.util

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.sql.schema import Table

def gen_log(message):
	print(f"{Fore.CYAN}[GENERATOR]{Style.RESET_ALL} {message}")

def get_model_from_path(path: str) -> Table:
	module_name = os.path.splitext(os.path.basename(path))[0]
	spec = importlib.util.spec_from_file_location(module_name, path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	model = None
	for name, obj in inspect.getmembers(module, inspect.isclass):
		if hasattr(obj, '__table__'):
			model = obj.__table__
			break
	if not type(model) == Table:
		raise Exception("This is impossible... wth happend?")
	return model

def generate_user(cli):
	table_name = input("What should be the table's name: ")
	username_field = input("What should the username field be called: ")
	password_field = input("What should the password field be called: ") 
	isHashed = input("Is the password hashed? (y/n): ")
	isEmail = input("Is there an email field? (y/n): ")
	email_field = ""
	email_command = ""
	if isEmail.lower().strip() == "y":
		email_field = input("What should the email field be called: ")
		email_command = f"{email_field} = Column(String(318))"

	c = cli([None, "create", "model", table_name])
	c.execute()
	if isHashed.lower().strip() == "n":
		with open(f"src/cargo/{table_name}Model.py", "w") as f:
			f.write(f"""#Generated by libmercury at {int(time())}
from libmercury.db import Column, Integer, Base, String

class {table_name}(Base):
	__tablename__ = "{table_name}"
	id = Column(Integer, primary_key=True)
	{username_field} = Column(String(20))
	{password_field} = Column(String(50))
	{email_command}
""")	
	elif isHashed.lower().strip() == "y":
		salt_field = input("What should the salt be called: ")
		with open(f"src/cargo/{table_name}Model.py", "w") as f:
			f.write(f"""#Generated by libmercury at {int(time())} 
from libmercury.db import Column, Integer, Base, String
from libmercury.security import generate_salt, hash_password, verify_password
import base64

class {table_name}(Base):
	__tablename__ = "{table_name}"
	id = Column(Integer, primary_key=True)
	{username_field} = Column(String(20))
	{password_field} = Column(String(50))
	{salt_field} = Column(String, nullable=False)
	{email_command}

	def set_password(self, password: str):
		self.{salt_field} = base64.b64encode(generate_salt()).decode('utf-8')
		self.{password_field} = hash_password(password, base64.b64decode(self.salt))

	def check_password(self, password: str) -> bool:
		return verify_password(self.{password_field}, password, base64.b64decode(self.{salt_field}))""")

	gen_log("Successfully created model")

def generate_login(cli):
	controller_name = input("What should be the name of the controller: ")
	controller_route = input("What should be the route of the controller: ")
	controller_success_redirect = input("What should be the success redirect of the controller: ")

	validator_name = input("What should be the name of the validator: ")

	model_name = input("What is the name of the model to sign into(leave blank to make a new one): ")
	if model_name == "":
		generate_user(cli)
		model_name = input("What is the name of the model to sign into(leave blank to make a new one): ")

	model_password_field = input("What is the name of the model's password field: ")
	model_username_field = input("What is the name of the model's username field: ")

	isHashed = input("Is the password hashed? (y/n): ")
	password_checker = f"not query(user, {model_username_field}={model_username_field}).first().{model_password_field} == {model_password_field}"

	if isHashed.lower().strip() == "y":
		validate_function = input("What is the name of the validator function(check_password if you used this for the model): ") 
		password_checker = f"not query(user, {model_username_field}={model_username_field}).first().{validate_function}({model_password_field})"

	jwt_name = input("What should be the name of the JWT: ")
	c = cli([None, "create", "jwt", jwt_name])
	c.execute()

	c = cli([None, "create", "controller", controller_name])
	c.execute()

	c = cli([None, "create", "validator", validator_name])
	c.execute()    
	
	with open(f"src/validators/{validator_name}Validator.py", "w") as f:
		f.write(f"""#Generated by libmercury at {int(time())}
from libmercury import Validator 
class {validator_name}Validator:
	{model_username_field} = Validator.String(max=20, min=5)
	{model_password_field} = Validator.String(max=100, min=8)""")
	
	with open(f"src/controllers/{controller_name}Controller.py", "w") as f:
		f.write(f"""#Generated by libmercury at {int(time())}
from libmercury import POSTRoute, Request, Response, redirect, useValidator, query, exists
from libmercury.utils import expires_in
from src.cargo.{model_name}Model import {model_name} 
from src.validators.{validator_name}Validator import {validator_name}Validator 
from src.security.{jwt_name}Jwt import {jwt_name}Jwt

class {controller_name}Controller:
	@staticmethod
	@POSTRoute("{controller_route}")
	@useValidator({validator_name}Validator)
	def login(request: Request) -> Response:
		if {jwt_name}Jwt._verify(request.cookies.get("token")):
			return redirect("{controller_success_redirect}")

		#Check to see if the account exists
		{model_username_field} = request.form["{model_username_field}"]
		if not exists(user, {model_username_field}={model_username_field}):
			#In production, just redirect to where the request will come from, do not rely on the referer header.
			referer = request.headers.get("Referer")
			if referer:
				return redirect(f"{{referer}}?error=Account doesn't exist")
			else:
				return redirect("/login?error=Account doesn't exist") 

		#Check to see if the password is correct
		{model_password_field} = request.form["{model_password_field}"]
		if {password_checker}:
			#In production, just redirect to where the request will come from, do not rely on the referer header.
			referer = request.headers.get("Referer")
			if referer:
				return redirect(f"{{referer}}?error=Wrong password")
			else:
				return redirect("/login?error=Wrong password")

		response = redirect("{controller_success_redirect}")
		response.set_cookie("token", {jwt_name}Jwt._makeJwt({{"username": username, "exp": expires_in(2592000)}}))
		return response 
""")
	gen_log("Successfully created login controller")

def generate_register(cli):
	controller_name = input("What should be the name of the controller: ")
	controller_route = input("What should be the route of the controller: ")
	controller_success_redirect = input("What should be the success redirect of the controller: ")

	validator_name = input("What should be the name of the validator: ")

	model_name = input("What is the name of the model to register for(leave blank to make a new one): ")
	if model_name == "":
		generate_user(cli)
		model_name = input("What is the name of the model to register for(leave blank to make a new one): ")

	jwt_checker = input("Provide the name of your JWT to make sure that users are not signed in, leave blank to make a new one: ")
	if jwt_checker == "":
		jwt_name = input("What should be the name of the JWT: ")
		c = cli([None, "create", "jwt", jwt_name])
		c.execute()

	username_field = input("What is the name of the model's username field: ")
	isHashed = input("Is the password hashed? (y/n): ")
	password_field = input("What is the name of the model's password field: ")
	set_passsword = ""
	if isHashed.lower().strip() == "y":
		set_password_field = input("What is the name of the model's password setter field: ")
		set_passsword = f"new_user.{set_password_field}({password_field})"
	salt_field = input("What is the name of the model's salt field: ")
	signed_in_redirect = input("Where should the controller redirect if the user is already signed in: ")
	primary_key = input("What is the name of the model's primary key: ")

	model = get_model_from_path(f"src/cargo/{model_name}Model.py")	
	if model == None:
		print(f"{Fore.RED}Error:{Style.RESET_ALL} Could not find model in src/cargo/{model_name}Model.py")
		return

	table = {}
	for col in model.columns:
		table[col.name] = col.type

	rules_python = []
	for key, value in table.items():
		if key == salt_field or key == primary_key:
			continue
		translated = ""
		if hasattr(value, "length") and value.length:
			value.length = f"max={value.length}"
		else:
			value.length = ""
		if type(value) == String:
			translated = f"Validator.String({value.length})"
		elif type(value) == Integer:
			translated = f"Validator.Integer({value.length})"
		elif type(value) == Boolean:
			translated = f"Validator.Boolean({value.length})"
		elif type(value) == Float:
			translated = f"Validator.Float({value.length})"
		else:
			print(f"[WARNING] Unhandled type for {key}, please add this to the validator and controller manually")
		rules_python.append(f"{key} = {translated}")
	rules_python = "\n\t".join(rules_python)

	c = cli([None, "create", "validator", validator_name])
	c.execute()  

	c = cli([None, "create", "controller", controller_name])
	c.execute()

	with open(f"src/validators/{validator_name}Validator.py", "w") as f:
		f.write(f"""#Generated by libmercury at {int(time())}
from libmercury import Validator
class {validator_name}Validator:
	{rules_python}""")

	lines = []
	user = f"new_user = {model_name}("

	for col in list(table.keys()):
		if col == primary_key or col == salt_field:
			continue
		lines.append(f'{col} = request.form["{col}"]')
		user = f"{user}{col}={col}," 
	user = user+")"
	lines = '\n\t\t'.join(lines)

	with open(f"src/controllers/{controller_name}Controller.py", "w") as f:
		f.write(f"""#Generated by libmercury at {int(time())}
from libmercury import useValidator, POSTRoute, redirect, Request, Response, exists
from src.validators.{validator_name}Validator import {validator_name}Validator 
from src.cargo.{model_name}Model import {model_name} 
from src.cargo.connection import Connection
from src.security.{jwt_checker}Jwt import {jwt_checker}Jwt
class RegisterController:
	@staticmethod
	@POSTRoute("{controller_route}")
	@useValidator(RegisterValidator)
	def {controller_name}(request: Request) -> Response:
		if {jwt_checker}Jwt._verify(request.cookies.get("token")):
			return redirect("{signed_in_redirect}")

		#Check to see if an account exists
		{username_field} = request.form["username"]
		if exists(user, {username_field}={username_field}):
			#In production, just redirect to where the request will come from, do not rely on the referer header.
			referer = request.headers.get("referer")
			if referer:
				return redirect(f"{{referer}}?error=Account already exists")
			else:
				return redirect("{controller_route}?error=Account already exists") 

		#Create the account
		{lines}
		{user}
		{set_passsword}
		Connection.Session.add_all([new_user,])
		Connection.Session.commit()

		#Redirect to the login page
		return redirect("{controller_success_redirect}")""")

def generate_password_reset(cli):
	pass

def generate_crud(cli):
	model_name = input("What is the name of the model: ")
	primary_key = input("What is the name of the model's primary key: ")
	controller_name = input("What should be the name of the controller: ")
	controller_route = input("What should be the route of the controller: ")
	validator_name = input("What should be the name of the validator: ")
	c = cli([None, "create", "controller", controller_name])
	c.execute()
	
	c = cli([None, "create", "validator", validator_name])
	c.execute()

	#Get the model information
	model = get_model_from_path(f"src/cargo/{model_name}Model.py")
	table = {}
	for col in model.columns:
		if not col.name == primary_key:
			table[col.name] = col.type

	#Write to our validator:
	rules_python = []
	for key, value in table.items():
		if key == "id":
			continue
		translated = ""
		if hasattr(value, "length") and value.length:
			value.length = f"max={value.length}"
		else:
			value.length = ""
		if type(value) == String:
			translated = f"Validator.String({value.length})"
		elif type(value) == Integer:
			translated = f"Validator.Integer({value.length})"
		elif type(value) == Boolean:
			translated = f"Validator.Boolean({value.length})"
		elif type(value) == Float:
			translated = f"Validator.Float({value.length})"
		else:
			print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} Unhandled type for {key}, please add this to the validator and controller manually")
		rules_python.append(f"{key} = {translated}")

	rules_python = "\n\t".join(rules_python)
	with open(f"src/validators/{validator_name}Validator.py", "w") as f:
		f.write(f"""#Generated by libmercury at {int(time())}
from libmercury import Validator
class {validator_name}Validator:
	{rules_python}""")
	
	#Write the controller
	with open(f"src/controllers/{controller_name}Controller.py", "w") as f:
		f.write(f"""#Generated by libmercury at {int(time())}
from json import dumps
from libmercury import DELETERoute, GETRoute, PATCHRoute, POSTRoute, Request, Response, find_or_404, json_to_object, object_to_json, update_object, useValidator
from src.cargo.{model_name}Model import {model_name} 
from src.validators.{validator_name}Validator import {validator_name}Validator
from src.cargo.connection import Connection

class {controller_name}Controller:
	@staticmethod
	@POSTRoute("{controller_route}")
	@useValidator({validator_name}Validator)
	def create(request: Request) -> Response:
		jsonobject = json_to_object(request.json, post)
		if type(jsonobject) == dict:
			#Return the error message
			return Response(dumps(jsonobject), content_type="application/json", status=400)
		Connection.Session.add_all([jsonobject])
		Connection.Session.commit()
		return Response(dumps({{"status":"success"}}))

	@staticmethod
	@GETRoute("{controller_route}/{{id:int}}")
	def read(request: Request, id: int) -> Response:
		find = find_or_404(post, "json", {primary_key}=id)
		if type(find) == Response:
			return find
		else:
			return Response(object_to_json(find_or_404(post, "json", id=id))) 

	@staticmethod
	@PATCHRoute("{controller_route}/{{id:int}}")
	def update(request: Request, id: int) -> Response:
		find = find_or_404(post, {primary_key}=id)
		if type(find) == Response:
			return find 
		return update_object(find, request.json)

	@staticmethod
	@DELETERoute("{controller_route}/{{id:int}}")
	def delete(request: Request, id: int) -> Response:
		find = find_or_404(post, {primary_key}=id)
		if type(find) == Response:
			return find 
		find.delete()
		return Response(dumps({{"status":"success"}}))""")
	
def generate(name, cli):
	generatable = {
		"model:user": generate_user, #Generates a model User
		"control:login": generate_login, #Generates a login controller with JWT's and validation
		"control:register": generate_register, #Generates a signup controller with validation
		"control:password_reset": generate_password_reset, #Generates a password reset controller
		"control:crud": generate_crud, #Generates a CRUD controller for a model
	}
	function = generatable.get(name)
	if not function:
		print(f"{Fore.RED}Error:{Style.RESET_ALL} Function not found")
	else:
		gen_log("Starting generation task")
		function(cli)
