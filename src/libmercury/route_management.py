from functools import wraps
from jinja2 import Environment, FileSystemLoader
from .security import JWT
from werkzeug import Response

def useAuthorization(auth, **kwargs):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)
		wrapper._auth = auth 
		wrapper._auth_cookie = kwargs.get("cookie")
		wrapper._error = kwargs.get("error")
		wrapper._negative_auth = kwargs.get("negative_auth")
		wrapper._jwt_validator = kwargs.get("validator")
		wrapper._jwt_require = kwargs.get("jwt_require")
		return wrapper
	return decorator

def useValidator(validator, **kwargs):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)
		wrapper._validator = validator
		wrapper._error = kwargs.get("error")
		wrapper._mimetypes = kwargs.get("mimetypes")
		return wrapper
	return decorator

def useJWTValidator(validator, **kwargs):
	def decorator(func):
		@wraps(func)
		def wrapped_function(*args, **kwargs):
			from libmercury.validation import validate
			jwt = args[0]  # Assuming the JWT is the first argument
			error = kwargs.get('error')  # Get the error handler or message from kwargs
			func_result = func(*args, **kwargs)
			if func_result == False:
				return False
			validation_result = validate(validator, error, JWT(jwt).payload)
			if not validation_result:
				return True
			else:
				return False
		return wrapped_function
	return decorator

def route(method: str, url: str):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)
		wrapper._route_method = method
		wrapper._route_url = url
		return wrapper
	return decorator
# HTTP method specific decorators
def GETRoute(url: str):
	return route('GET', url)

def POSTRoute(url: str):
	return route('POST', url)

def DELETERoute(url: str):
	return route('DELETE', url)

def PATCHRoute(url: str):
	return route('PATCH', url)

def PUTRoute(url: str):
	return route('PUT', url)

def OPTIONSRoute(url: str):
	return route('OPTIONS', url)

def HEADRoute(url: str):
	return route('HEAD', url)

def CONTROLRoute(url: str):
	return route('CONTROL', url) 

def TRACERoute(url: str):
	return route('TRACE', url)

class Route:
	def __init__(self, method: str, url: str, handler):
		self.method = method
		self.url = url
		self.handler = handler

	def __repr__(self):
		return f"Route(method={self.method}, url='{self.url}', handler={self.handler})"

def use_template(template_name: str, **kwargs) -> Response:
	enviroment = Environment(loader=FileSystemLoader("src/templates"))
	template = enviroment.get_template(template_name)
	response = Response(template.render(kwargs))
	response.headers["Content-Type"] = "text/html"
	return response
