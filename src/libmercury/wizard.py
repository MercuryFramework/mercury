from json import loads, dumps
from colorama import Fore, Style
from libmercury.db.setup_db import * 
from libmercury.security import keygen 
from libmercury.db import MigrationSystem
from libmercury.generation import generate
from .version import version
import os
import importlib.util
class CLI:
	def __init__(self, arguments) -> None:
		self.arguments = arguments

	def execute(self):
		try:
			with open(".mercury", "r") as f:
				os.chdir(f.read())
		except:
			pass
		del self.arguments[0]
		commands = {
			"init": self.init,
			"create": self.create,
			"migrate": self.migrate,
			"generate": self.generate,
			"run": self.run,
		}
		if len(self.arguments) < 1:
			self.version_display()
			return
		try:
			commands[self.arguments[0]]()
		except KeyError:
			self.unknown_command()

	def init(self):
		print(f"{Fore.BLUE}[Initializer]{Style.RESET_ALL} Launching Mercury {version} initializer...")
		directory = input(f"{Fore.BLUE}[Initializer]{Style.RESET_ALL} Name of directory to use: ")
		interpreter = input(f"{Fore.BLUE}[Initializer]{Style.RESET_ALL} Please provide your python interpreter(python, python3, etc): ")

		#Create project file structure
		os.mkdir(directory) 
		os.mkdir(f"{directory}/src")
		os.mkdir(f"{directory}/src/templates")
		os.mkdir(f"{directory}/src/static")
		os.mkdir(f"{directory}/src/controllers")
		os.mkdir(f"{directory}/src/validators")
		os.mkdir(f"{directory}/src/cargo")
		os.mkdir(f"{directory}/src/cargo/migrations")
		os.mkdir(f"{directory}/src/security")
		os.mkdir(f"{directory}/src/.vault")
		
		#Create files
		with open(f"{directory}/map.json", "w") as f:
			f.write(dumps({
				"interpreter": interpreter,
				"version": version,
				"controllers": [],
				"models": [],
				"validators": [],
				"security": []
			}))

		with open(f"{directory}/src/cargo/dev.db", "w") as f:
			f.write("")

		with open(f"{directory}/src/cargo/connection.py", "w") as f:
			f.write("""from libmercury.db import connection
Connection = connection("sqlite:///src/cargo/dev.db", echo=False)
#Connection.Engine - The engine
#Connection.Session - The session connected to the db""")
		with open(f"{directory}/app.py", "w") as f:
			f.write("""from libmercury.wsgi import WSGIApp
from werkzeug.serving import run_simple
app = WSGIApp()
run_simple("localhost", 8000, app)
					""")

		#Create .mercury files that allow us to run commands from anywhere in the file structure
		directories = [
			"src",
			"src/controllers",
			"src/validators",
			"src/security",
			"src/cargo",
			"src/cargo/migrations",
			"src/templates",
			"src/static"
		]
		for i in directories:
			with open(f"{directory}/{i}/.mercury", "w") as f:
				f.write(f"{os.getcwd()}/{directory}")
		
		create_mercury_table(f"sqlite:///{directory}/src/cargo/dev.db")
		print(f"{Fore.BLUE}[Initializer]{Style.RESET_ALL} Initialized project in directory: '{directory}'")

	def _import_module(self, file_path):
		module_name = os.path.splitext(os.path.basename(file_path))[0]
		spec = importlib.util.spec_from_file_location(module_name, file_path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module

	def create(self):
		if len(self.arguments) < 2:
			print(f"{Fore.RED}Error:{Style.RESET_ALL} Command 'create' requires at least 2 parameters")
			print("Usage:")
			print("create <thing> <named>")
		
		thing = self.arguments[1]
		named = self.arguments[2]

		things = {
			"controller": self._create_controller,
			"validator": self._create_validator,
			"model": self._create_model,
			"jwt": self._create_jwt,
			"migration": self._create_migration
		}
		try:
			things[thing](named)
		except KeyError as e:
			print(f"{Fore.RED}Error:{Style.RESET_ALL} Unknown createable {thing}")
			print("Usage:")
			print("create <thing> <named>")
	
	def _create_controller(self, name):
		#Create placeholder
		with open(f"src/controllers/{name}Controller.py", "w") as f:
			f.write(f"""from libmercury import GETRoute, Request, Response
class {name}Controller:
	@staticmethod
	@GETRoute("/example")
	def example(request: Request) -> Response:
		response = Response("<h1>Example Page</h1>")
		response.headers['Content-Type'] = 'text/html'
		return response""")
		
		#Update Map.json
		with open("map.json", "r") as f:
			map_json = loads(f.read())
			map_json["controllers"].append(f"src/controllers/{name}Controller.py")
			map_json["controllers"] = list(set(map_json["controllers"]))
			map_json["validators"] = list(set(map_json["validators"]))
			map_json["models"] = list(set(map_json["models"]))
			map_json["security"] = list(set(map_json["security"]))
		with open("map.json", "w") as f:
			f.write(dumps(map_json))

		print(f"{Fore.BLUE}[CODEGEN]{Style.RESET_ALL} Successfully created src/controllers/{name}Controller.py")

	def _create_validator(self, name):
		with open(f"src/validators/{name}Validator.py", "w") as f:
			f.write(f"""from libmercury import Validator 
class {name}Validator:
	pass
		""")
		
		#Update Map.json
		with open("map.json", "r") as f:
			map_json = loads(f.read())
			map_json["validators"].append(f"src/validators/{name}Validator.py")
			map_json["controllers"] = list(set(map_json["controllers"]))
			map_json["validators"] = list(set(map_json["validators"]))
			map_json["models"] = list(set(map_json["models"]))
			map_json["security"] = list(set(map_json["security"]))
		with open("map.json", "w") as f:
			f.write(dumps(map_json))

		print(f"{Fore.BLUE}[CODEGEN]{Style.RESET_ALL} Successfully created src/validators/{name}Validator.py")

	def _create_migration(self, message):
		#Get all models
		with open("map.json", "r") as f:
			map_json = loads(f.read())
			model_paths = map_json["models"]
			map_json["controllers"] = list(set(map_json["controllers"]))
			map_json["validators"] = list(set(map_json["validators"]))
			map_json["models"] = list(set(map_json["models"]))
			map_json["security"] = list(set(map_json["security"]))

		#Run migrator
		print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Starting Migrator")
		migrator = MigrationSystem("src/cargo/connection.py", model_paths)
		migrator._create_migration()

	def _create_model(self, name):
		with open(f"src/cargo/{name}Model.py", "w") as f:
			f.write(f"""from libmercury.db import Column, Integer, Base

class {name}(Base):
	__tablename__ = "{name}"
	id = Column(Integer, primary_key=True)""")
		with open("map.json", "r") as f:
			map_json = loads(f.read())
			map_json["models"].append(f"src/cargo/{name}Model.py")
			map_json["controllers"] = list(set(map_json["controllers"]))
			map_json["validators"] = list(set(map_json["validators"]))
			map_json["models"] = list(set(map_json["models"]))
			map_json["security"] = list(set(map_json["security"]))

		with open("map.json", "w") as f:
			f.write(dumps(map_json))
		print(f"{Fore.BLUE}[CODEGEN]{Style.RESET_ALL} Successfully created src/cargo/{name}Model.py")

	def _create_jwt(self, name):
		key_type = keygen.main(name)
		public_key = f"{name}Public_key.pem"
		private_key = f"{name}Private_key.pem"
		if key_type == "HMAC":
			public_key = f"{name}Hmac_secret.key"
			private_key = f"{name}Hmac_secret.key"
		with open(f"src/security/{name}Jwt.py", "w") as f:
			f.write(f"""from libmercury.security import JWT
class {name}Jwt:
	@staticmethod
	def _makeJwt(body:dict):
		jwt = JWT("")
		jwt.payload = body
		return jwt.sign("src/.vault/{private_key}", "{key_type}")

	@staticmethod
	def _verify(jwt):
		try:
			jwt = JWT(jwt)
			return jwt.verify_signature("src/.vault/{public_key}")
		except ValueError:
			return False""")
		with open("map.json", "r") as f:
			map_json = loads(f.read())
			map_json["security"].append(f"src/secuirty/{name}Jwt.py")
			map_json["controllers"] = list(set(map_json["controllers"]))
			map_json["validators"] = list(set(map_json["validators"]))
			map_json["models"] = list(set(map_json["models"]))
			map_json["security"] = list(set(map_json["security"]))

		with open("map.json", "w") as f:
			f.write(dumps(map_json))
		
		print(f"{Fore.BLUE}[CODEGEN]{Style.RESET_ALL} Successfully created src/cargo/{name}Jwt.py")

	def migrate(self):
		# Extract the database URL from the `Connection` object
		module = self._import_module("src/cargo/connection.py")
		if hasattr(module, 'Connection'):
			connection = module.Connection
			# Extracting the database URL from the connection object
			# This depends on the actual implementation of `connection` in `libmercury.db`
			if hasattr(connection, 'Engine'):
				db_url = connection.Engine.url
			else:
				raise AttributeError("The 'Connection' object does not have an 'engine' or 'url' attribute.")
		else:
			raise AttributeError("The module does not have a 'Connection' object.")

		if find_mercury_table(db_url) is None:
			create_mercury_table(db_url)
			create_version(db_url, 0)	
		db_version = get_version(db_url)
		latest_migration_id = 0
		migrations = []

		#Get all non-runned migrations
		for file in os.listdir("src/cargo/migrations"):
			if file.endswith('.py') and os.path.isfile(os.path.join("src/cargo/migrations", file)):
				try:
					if int(file[:-3]) > db_version:
						if int(file[:-3]) > latest_migration_id:
							latest_migration_id = int(file[:-3])
						migrations.append(os.path.join("src/cargo/migrations", file))
				except ValueError:
					pass
		migrations.sort(key=lambda x: int(os.path.basename(x)[:-3]))
		
		for migration in migrations:
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Running migration {migration}")
			try:
				module = self._import_module(migration).upgrade(db_url)
				print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} '{migration}' passed with no errors")
			except Exception as e:
				print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Migration: '{migration}' failed with error:")
				print(e)

		#Update map
		map = loads(open("map.json", "r").read())
		if not latest_migration_id == 0:
			update_version(db_url, latest_migration_id)

		with open("map.json", "w") as f:
			map["controllers"] = list(set(map["controllers"]))
			map["validators"] = list(set(map["validators"]))
			map["models"] = list(set(map["models"]))
			map["security"] = list(set(map["security"]))
			f.write(dumps(map))

	def run(self):
		with open("map.json", "r") as f:
			map = loads(f.read())
		os.system(f"{map['interpreter']} app.py")

	def generate(self):
		if len(self.arguments) < 2:
			print(f"{Fore.RED}Error:{Style.RESET_ALL} Command 'generate' requires at least 1 parameters")
			print("Usage:")
			print("generate <name>")
			return
		
		result = generate(self.arguments[1], CLI)

	def unknown_command(self):
		print(f"{Fore.RED}Error:{Style.RESET_ALL} Unknown Command")

	def version_display(self):
		print(r""" /$$		/$$															   
| $$$	 /$$$															 
| $$$$	/$$$$  /$$$$$$	 /$$$$$$   /$$$$$$$ /$$   /$$  /$$$$$$	/$$   /$$
| $$ $$/$$ $$ /$$__  $$ /$$__  $$ /$$_____/| $$  | $$ /$$__  $$| $$  | $$
| $$  $$$| $$| $$$$$$$$| $$  \__/| $$	   | $$  | $$| $$  \__/| $$  | $$
| $$\  $ | $$| $$_____/| $$		 | $$	   | $$  | $$| $$	   | $$  | $$
| $$ \/  | $$|	$$$$$$$| $$		 |	$$$$$$$|  $$$$$$/| $$	   |  $$$$$$$
|__/	 |__/ \_______/|__/		  \_______/ \______/ |__/		\____  $$
																/$$  | $$
															   |  $$$$$$/
																\______/ """)
		print(version)
