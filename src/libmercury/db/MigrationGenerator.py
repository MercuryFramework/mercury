from colorama import Fore, Style
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
import importlib.util
import os
import inspect

class MigrationSystem:
	def __init__(self, db_connection_path, model_paths) -> None:
		self.db_connection_path = db_connection_path
		self.model_paths = model_paths

	def _extract_db_url_from_connection(self, file_path) -> None:
		# Load the module from the file path
		module_name = os.path.splitext(os.path.basename(file_path))[0]
		spec = importlib.util.spec_from_file_location(module_name, file_path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		
		# Extract the database URL from the `Connection` object
		if hasattr(module, 'Connection'):
			connection = module.Connection
			# Extracting the database URL from the connection object
			# This depends on the actual implementation of `connection` in `libmercury.db`
			if hasattr(connection, 'Engine'):
				db_url = connection.Engine.url
				return str(db_url)
			else:
				raise AttributeError("The 'Connection' object does not have an 'engine' or 'url' attribute.")
		else:
			raise AttributeError("The module does not have a 'Connection' object.")

	def _generate_file(self) -> None:
		python_files = []
		for file in os.listdir("src/cargo/migrations"):
			if file.endswith('.py') and os.path.isfile(os.path.join("src/cargo/migrations", file)):
				try:
					python_files.append(int(file[:-3]))
				except ValueError:
					pass
		if len(python_files) == 0:
			name = 1
		else:
			name = max(python_files)+1
		with open(f"src/cargo/migrations/{name}.py", "w") as f:
			f.write(f"""from libmercury.db import MigrationWrapper 

_version = '{name}'
_prev_version = None

def upgrade(url):
	wrapper = MigrationWrapper(url)

def downgrade(url):
	wrapper = MigrationWrapper(url)""")
		print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Generated file: src/cargo/migrations/{name}.py")

	def _create_migration(self) -> None:
		# Step 1: Load ORM models
		print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Loading ORM models")
		orm_models = self.load_orm_models(self.model_paths)
		
		# Step 2: Get the database schema
		print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Loading database schema")
		db_metadata = self.get_database_schema(self._extract_db_url_from_connection(self.db_connection_path))
		
		# Step 3: Compare schemas
		print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Finding discrepancies...")
		discrepancies = self.compare_schemas(orm_models, db_metadata)
		
		# Output discrepancies
		print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Loading discrepancies")
		if discrepancies:
			for discrepancy in discrepancies:
				print(discrepancy)
			self._generate_file()
		else:
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} ORM models perfectly match the database schema, no migrations are required")

	def load_orm_models(self, model_paths) -> list:
		models = []
		for path in model_paths:
			module_name = os.path.splitext(os.path.basename(path))[0]
			spec = importlib.util.spec_from_file_location(module_name, path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			for name, obj in inspect.getmembers(module, inspect.isclass):
				if hasattr(obj, '__table__'):
					models.append(obj)
		return models

	def get_database_schema(self, engine_url) -> MetaData:
		engine = create_engine(engine_url)
		metadata = MetaData()
		metadata.reflect(bind=engine)
		return metadata

	def compare_schemas(self, orm_models, db_metadata) -> list:
		discrepancies = []
		orm_tables = {}
		for model in orm_models:
			table = model.__table__
			orm_tables[table.name] = {col.name: col.type for col in table.columns}

		db_tables = {table.name: {col.name: col.type for col in table.columns} for table in db_metadata.sorted_tables}

		for table_name, orm_columns in orm_tables.items():
			if table_name not in db_tables:
				discrepancies.append(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Table '{table_name}' is missing in the database.")
				continue

			db_columns = db_tables[table_name]

			for col_name, col_type in orm_columns.items():
				if col_name not in db_columns:
					discrepancies.append(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Column '{col_name}' in table '{table_name}' is missing in the database.")
				elif str(col_type) != str(db_columns[col_name]):
					print(str(col_type))
					print(db_columns)
					print(col_name)
					discrepancies.append(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Column '{col_name}' in table '{table_name}' has type mismatch.")

			for col_name in db_columns:
				if col_name not in orm_columns:
					discrepancies.append(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Column '{col_name}' in table '{table_name}' is extra in the database.")

		return discrepancies

class MigrationWrapper:
	def __init__(self, connection_string) -> None:
		self.engine = create_engine(connection_string)
		self.metadata = MetaData(bind=self.engine)

	def create_table(self, table_name, columns) -> None:
		"""
		Create a new table with specified columns.
		
		:param table_name: Name of the table to create
		:param columns: List of Column definitions
		"""
		self.metadata.reflect(bind=self.engine)
		try:
			table = Table(table_name, self.metadata, *columns)
			table.create(self.engine)
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Table '{table_name}' created successfully.")
		except SQLAlchemyError as e:
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Error creating table: {e}")

	def delete_table(self, table_name) -> None:
		"""
		Delete an existing table.
		
		:param table_name: Name of the table to delete
		"""
		try:
			table = Table(table_name, self.metadata, autoload_with=self.engine)
			table.drop(self.engine)
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Table '{table_name}' deleted successfully.")
		except SQLAlchemyError as e:
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Error deleting table: {e}")

	def add_column(self, table_name, column) -> None:
		"""
		Add a new column to an existing table.
    
		:param table_name: Name of the table
		:param column: Column definition
		"""
		try:
			table = Table(table_name, self.metadata, autoload_with=self.engine)
			with self.engine.connect() as conn:
				# Manually construct the column definition with type, nullable, and default value
				column_sql = f"{column.name} {column.type.compile(self.engine.dialect)}"
            
				if not column.nullable:
					column_sql += " NOT NULL"
				else:
					column_sql += " NULL"
            
				if column.default is not None:
					# Extract the default value, accounting for SQL expressions or callable defaults
					if callable(column.default.arg):
						default_value = column.default.arg()
					else:
						default_value = column.default.arg
					column_sql += f" DEFAULT {default_value}"
            
				conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_sql}')
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Column '{column.name}' added to table '{table_name}'.")
		except SQLAlchemyError as e:
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Error adding column: {e}")

	def drop_column(self, table_name, column_name) -> None:
		"""
		Drop an existing column from a table.
		
		:param table_name: Name of the table
		:param column_name: Name of the column to drop
		"""
		try:
			table = Table(table_name, self.metadata, autoload_with=self.engine)
			with self.engine.connect() as conn:
				conn.execute(f'ALTER TABLE {table_name} DROP COLUMN {column_name}')
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Column '{column_name}' dropped from table '{table_name}'.")
		except SQLAlchemyError as e:
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Error dropping column: {e}")

	def modify_column(self, table_name, old_column_name, new_column) -> None:
		"""
		Modify an existing column in a table.
		
		:param table_name: Name of the table
		:param old_column_name: Name of the column to modify
		:param new_column: New Column definition
		"""
		try:
			table = Table(table_name, self.metadata, autoload_with=self.engine)
			with self.engine.connect() as conn:
				conn.execute(f'ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO temp_{old_column_name}')
				conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {new_column.compile(conn.dialect)}')
				conn.execute(f'UPDATE {table_name} SET {new_column.name} = temp_{old_column_name}')
				conn.execute(f'ALTER TABLE {table_name} DROP COLUMN temp_{old_column_name}')
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Column '{old_column_name}' modified to '{new_column.name}' in table '{table_name}'.")
		except SQLAlchemyError as e:
			print(f"{Fore.GREEN}[Migrator]{Style.RESET_ALL} Error modifying column: {e}")

