import json
from werkzeug import Response
from sqlalchemy.exc import IntegrityError

def get_connection():
	from src.cargo.connection import Connection
	return Connection

def query(model, **kwargs):
	result = get_connection().Session.query(model).filter_by(**kwargs)
	return result

def exists(model, **kwargs):
	result = query(model, **kwargs).first()
	if result == None:
		return False
	return True

def find_or_404(model, response_format="html", **kwargs):
	result = query(model, **kwargs).first()

	if result is None:
		if response_format == "json":
			error_message = {
				"error": "404 Not Found",
				"details": f"{model.__name__} not found with {kwargs}"
			}
			response_body = json.dumps(error_message)
			return Response(response_body, status=404, mimetype='application/json')
		else:  # Default to HTML
			error_message = f"<h1>404 Not Found</h1><p>{model.__name__} not found with {kwargs}</p>"
			return Response(error_message, status=404, mimetype='text/html')
	
	return result

def expires_in(seconds: int):
	import time
	return int(time.time())+seconds

def object_to_json(model, exclude=None):
    """Converts a SQLAlchemy model instance to a JSON string, with optional exclusion of specified fields."""
    if exclude is None:
        exclude = []

    def model_to_dict(obj):
        """Converts a SQLAlchemy model instance to a dictionary, excluding specified fields."""
        return {
            c.name: getattr(obj, c.name)
            for c in obj.__table__.columns
            if c.name not in exclude
        }

    model_dict = model_to_dict(model)
    return json.dumps(model_dict)

def json_to_object(json_dict, model_class):
	"""Converts a JSON string to a SQLAlchemy model instance, excluding the primary key.

	Args:
		json_str (str): The JSON string representing the model data.
		model_class (SQLAlchemy Model): The SQLAlchemy model class to instantiate.

	Returns:
		object or dict: The SQLAlchemy model instance if successful, or a dictionary with an error message.
	"""
	try:
		# Parse the JSON string
		data = json_dict
		# Get the primary key column name
		primary_key_column = model_class.__table__.primary_key.columns.keys()[0]
		
		# Ensure the primary key is not included in the JSON
		if primary_key_column in data:
			raise ValueError(f"Primary key '{primary_key_column}' should not be provided in the JSON.")
		
		# Instantiate the model using the remaining data
		instance = model_class(**data)
		return instance

	except json.JSONDecodeError as e:
		# Handle JSON parsing errors
		return {"error": "Invalid JSON format", "details": str(e)}

	except ValueError as e:
		# Handle missing or invalid primary key
		return {"error": "Validation error", "details": str(e)}

	except TypeError as e:
		# Handle errors where JSON keys don't match model attributes
		return {"error": "Type error", "details": str(e)}

	except IntegrityError as e:
		# Handle SQLAlchemy integrity errors
		return {"error": "Integrity error", "details": str(e)}

	except Exception as e:
		# Handle any other exceptions
		return {"error": "Unexpected error", "details": str(e)}

def update_object(object, updates):
	session = get_connection().Session
	"""Update an SQLAlchemy object with the provided dictionary of changes.
	
	Args:
		object (SQLAlchemy model instance): The object to update.
		updates (dict): Dictionary of field updates.

	Returns:
		werkzeug.wrappers.Response: A response object indicating success or error.
	"""
	# Get the primary key and unique columns
	primary_key_column = object.__table__.primary_key.columns.keys()[0]
	unique_columns = [c.name for c in object.__table__.columns if c.unique]

	# Check if ID or unique fields are being changed
	for key in updates:
		if key == primary_key_column or key in unique_columns:
			error_message = {
				"error": "Invalid update attempt",
				"details": f"Cannot change '{key}' field."
			}
			return Response(
				json.dumps(error_message),
				status=400,
				mimetype='application/json'
			)

	# Apply updates to the object
	for key, value in updates.items():
		setattr(object, key, value)

	# Commit the changes
	try:
		session.commit()
		success_message = {
			"success": "Update successful",
			"details": f"Updated {object.__class__.__name__} with ID {getattr(object, primary_key_column)}."
		}
		return Response(
			json.dumps(success_message),
			status=200,
			mimetype='application/json'
		)
	except IntegrityError as e:
		session.rollback()
		error_message = {
			"error": "Database error",
			"details": str(e.orig)	# You might need to adjust based on your DB errors
		}
		return Response(
			json.dumps(error_message),
			status=400,
			mimetype='application/json'
		)
	except Exception as e:
		session.rollback()
		error_message = {
			"error": "Unexpected error",
			"details": str(e)
		}
		return Response(
			json.dumps(error_message),
			status=500,
			mimetype='application/json'
		)

