from colorama import Fore, Style
import re
def gen_log(msg):
	print(f"{Fore.CYAN}[Generator]{Style.RESET_ALL} {msg}")

def parse_input(input_string) -> dict:
	"""
	Given a single input string, process it to convert into a dictionary format:
	"generate model:user username:string:10 password:string salt:string set_password:setter:password, salt check_password=setter:password, salt"
	
	Converts it into a dictionary like so:
	{"method":"model", "name":"user", "fields":{"username":"string(10)", "password":"string", "salt":"string", "set_password":"setter(password, salt)", "check_password":"setter(password, salt)"}}
	"""
	# Remove unnecessary whitespace around commas and colons
	cleaned_input = re.sub(r"\s*,\s*", ",", input_string)
	cleaned_input = re.sub(r"\s*:\s*", ":", cleaned_input)
	
	# Split the cleaned input string into parts
	parts = cleaned_input.split(" ")
	
	# Initialize the resulting dictionary
	result = {"method": "", "name": "", "fields": {}}
	
	# Extract the method and name
	if len(parts) > 1:
		method_name = parts[1].split(":")
		if len(method_name) == 2:
			result["method"] = method_name[0].strip()
			result["name"] = method_name[1].strip()
		else:
			raise ValueError("Invalid method:name format")

	# Process remaining parts for fields and special cases
	for field in parts[2:]:
		if "=" in field:
			# Handle special fields with "="
			field_name, field_value = field.split("=", 1)
			result["fields"][field_name.strip()] = field_value.strip()
		else:
			# Handle regular fields
			field_parts = field.split(":")
			if len(field_parts) < 2:
				continue  # Skip fields that don"t have enough parts

			field_name = field_parts[0].strip()
			field_type = field_parts[1].strip()
			field_size = field_parts[2].strip() if len(field_parts) > 2 else ""
			if field_size:
				result["fields"][field_name] = f"{field_type}({field_size})"
			else:
				result["fields"][field_name] = field_type
	
	# Special handling for setter functions
	for key in result["fields"]:
		value = result["fields"][key]
		if value.startswith("setter"):
			# Extract parameters inside the setter
			params = value[7:]	# Remove "setter:"
			result["fields"][key] = f"setter({params.strip()})"
	return result

def gen_aio(parsed_data, cli):
	name = parsed_data["name"]
	gen_log(f"Generating aio {name}")

def gen_model(parsed_data, cli):
	name = parsed_data["name"]
	gen_log(f"Generating model {name}")
	
	fields = parsed_data["fields"]
	
	# Step 1: Create lists for SQLAlchemy columns and dynamically generated methods
	columns = []
	methods = []
	used_types = set()
	used_types.add("Column")
	used_types.add("Integer")

	# Step 2: Iterate through fields and separate columns and setter/checker functions
	for field_name, field_value in fields.items():
		if "setter" in field_value:
			# Extract the setter function parameters (e.g., password and salt)
			params = field_value[field_value.index("(")+1:field_value.index(")")].split(",")
			params = [param.strip() for param in params]
			password_field, salt_field = params

			# Use the user-specified function name (e.g., set_password or check_password)
			func_name = field_name

			# Dynamically generate the setter/checker function using the user-specified name and fields
			set_func = f"""
	def {func_name}(self, {password_field}: str):
		self.{salt_field} = base64.b64encode(generate_salt()).decode("utf-8")
		self.{password_field} = hash_password({password_field}, base64.b64decode(self.{salt_field}))
"""
			if func_name.startswith("check_"):
				check_func = f"""
	def {func_name}(self, {password_field}: str) -> bool:
		return verify_password(self.{password_field}, {password_field}, base64.b64decode(self.{salt_field}))
"""
				methods.append(check_func)
			else:
				methods.append(set_func)
		else:
			type_mappings = {
				"string": "String",
				"integer": "Integer",
				"smallinteger": "SmallInteger",
				"bigint": "BigInteger",
				"float": "Float",
				"boolean": "Boolean",
				"unicode": "Unicode",
				"unicodetext": "UnicodeText",
				"date": "Date",
				"datetime": "DateTime",
				"time": "Time",
				"enum": "Enum",
				"numeric": "Numeric",
				"decimal": "DECIMAL",
				"real": "REAL",
				"interval": "Interval",
				"json": "JSON",
				"largebinary": "LargeBinary",
				"pickle": "PickleType",
				"char": "CHAR",
				"nchar": "NCHAR",
				"text": "Text",
				"varchar": "VARCHAR",
				"varbinary": "VARBINARY",
				"clob": "CLOB",
				"blob": "BLOB",
				"array": "ARRAY",
				"tupletype": "TupleType",
				"typedecorator": "TypeDecorator",
				"foreignkey": "ForeignKey"
			}
			for field_type, sqlalchemy_type in type_mappings.items():
				if field_type in field_value:
					used_types.add(sqlalchemy_type)
					size = field_value.split("(")[1][:-1] if "(" in field_value else None
					if sqlalchemy_type == "ForeignKey" and size:
						columns.append(f"{field_name} = Column(ForeignKey('{size}'))")
					elif size:
						columns.append(f"{field_name} = Column({sqlalchemy_type}({size}))")
					else:
						columns.append(f"{field_name} = Column({sqlalchemy_type})")

	# Step 2: Create the model file
	c = cli([None, "create", "model", name])
	c.execute()
	with open(f"src/cargo/{name}Model.py", "w") as f:
		f.write(f"""from libmercury.db import {", ".join(used_types)}\n""")
		if len(methods) > 0:
			f.write("""from libmercury.security import hash_password, verify_password, generate_salt
import base64\n""")
		f.write(f"""
class {name}(Base):
	__tablename__ = "{name}"
	id = Column(Integer, primary_key=True)\n""")

		for col in columns:
			f.write(f"\t{col}\n")
		for method in methods:
			f.write(method)

def generate(input_string, cli):
	#Step 1: Parse the input string
	result = parse_input(input_string)

	#Step 2: Figure out the method, then execute its generator
	methods = {
		"model": gen_model,
		"aio": gen_aio
	}
	methods[result["method"]](result, cli)
