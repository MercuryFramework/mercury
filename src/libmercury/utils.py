import json
from werkzeug import Response

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

def object_to_json(model):
    """Converts a SQLAlchemy model instance to a JSON string."""
    def model_to_dict(obj):
        """Converts a SQLAlchemy model instance to a dictionary."""
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

    model_dict = model_to_dict(model)
    return json.dumps(model_dict)

def json_to_object(json_str, model_class):
    """Converts a JSON string to a SQLAlchemy model instance, excluding the primary key.

    Args:
        json_str (str): The JSON string representing the model data.
        model_class (SQLAlchemy Model): The SQLAlchemy model class to instantiate.

    Returns:
        object or dict: The SQLAlchemy model instance if successful, or a dictionary with an error message.
    """
    try:
        # Parse the JSON string
        data = json.loads(json_str)
        
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
