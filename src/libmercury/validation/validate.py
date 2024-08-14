from werkzeug import Response

def validate(validator, error, data):
	class_vars = {}
	for name, value in validator.__dict__.items():
		if not name.startswith("__"):
			if getattr(value, "__exclude_from_validation", False):
				continue  # Skip this field if marked as excluded
			class_vars[name] = value

	class_fields = list(class_vars.keys())
	request_fields = list(data.keys())

	for field in class_fields:
		if field not in request_fields:
			if error:
				return error()
			rsp = Response(f"Error: Missing field '{field}'")
			rsp.status_code = 400
			return rsp
		else:
			value = data[field]
			field_validator = class_vars[field]
			if hasattr(field_validator,  "__nested_validator"):
				if type(value) != dict:
					rsp = Response(f"Error: type mismatch in field '{field}'")
					rsp.status_code = 400
					return rsp
				nested_result = validate(field_validator, error, value) 
				if nested_result:
					return nested_result
			elif not field_validator.validate(value):
				if error:
					return error()
				rsp = Response(f"Error: type mismatch in field '{field}'")
				rsp.status_code = 400
				return rsp
