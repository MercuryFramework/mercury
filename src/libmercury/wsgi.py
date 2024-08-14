from colorama import Fore, Style
from werkzeug.utils import send_from_directory
from libmercury.validation import validate
from .route_management import Route
from werkzeug import Request, Response
from routes import Mapper
import importlib.util
import json
import os

class WSGIApp:
	def __init__(self):
		self.routes = []
		self.load_project()
		self.mapper = Mapper()
		self.load_mapper()

	def load_mapper(self):
		for route in self.routes:
			if type(route) == list:
				for r in route:
					if r.url[-1] == "/" and r.url != "/":
						r.url = r.url[:-1]
				#Just use the first url, if they are in a list they all have the same url
				self.mapper.connect(None, route[0].url, controller=lambda: route)

			else:
				if route.url[-1] == "/" and route.url != "/":
					route.url = route.url[:-1]
				self.mapper.connect(None, route.url, controller=route)

	def load_project(self):
		# Load the map.json file
		with open('map.json') as f:
			config = json.load(f)
		
		# Load and register routes from controllers
		for controller_path in config.get('controllers', []):
			self._load_controller(controller_path)

	def _load_controller(self, controller_path):
		# Import the module
		module_name = os.path.splitext(os.path.basename(controller_path))[0]
		spec = importlib.util.spec_from_file_location(module_name, controller_path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		
		# Get the controller class name (assuming it's the same as the module name)
		controller_class_name = module_name 
		
		# Get the controller class from the module
		controller_class = getattr(module, controller_class_name, None)
		if not controller_class:
			print(f"{Fore.YELLOW}[WARNING] Controller class {controller_class_name} not found in module {module_name}{Style.RESET_ALL}")
			return
	
		# Iterate over all attributes in the class
		for method_name in dir(controller_class):
			method = getattr(controller_class, method_name)
			
			# Check if the attribute is callable and has route attributes
			if callable(method) and hasattr(method, '_route_method') and hasattr(method, '_route_url'):
				route = Route(method._route_method, method._route_url, method)
				#Goes through the list of routes and sees if there is already a route that has the same url
				appended = False
				for idx, r in enumerate(self.routes):
					if r.url == route.url:
						#Makes the route be a list of the old route and the new route
						self.routes[idx] = [self.routes[idx]] + [route]
						appended = True
				if not appended:
					self.routes.append(route)

	def wsgi_handler(self, environ, start_response):
		# Create a Request object from WSGI environment
		request = Request(environ)
		
		method = request.method
		path = request.path
		if path.startswith('/static/'):
			# Serve the static file from the directory
			filename = path[len('/static/'):]
			try:
				response = send_from_directory("src/static", filename, environ, as_attachment=False)
			except:
				response = Response("<h1>404 Not Found</h1>", status=404, content_type='text/html')
				return response(environ, start_response)
		try:
			route = dict(self.mapper.match(path))
		except:
			response = Response('<h1>404 Not Found</h1>', status=404, content_type='text/html')
			return response(environ, start_response)
		
		controller = route.get("controller")
		if controller == None:
			raise Exception("Could not find controller in route")
		if callable(controller):
			#This gets the list of routes that matches the url
			#We use a function because at the moment the Routes package
			#Auto converts everything that is not a function to a string 
			controller = controller()

		if type(controller) == list:
			for c in controller:
				if c.method == method:
					controller = c.handler
					break
		else:
			controller = controller.handler

		if not controller:
			response = Response('<h1>404 Not Found</h1>', status=404, content_type='text/html')
			return response(environ, start_response)
		
		if type(controller) == list:
			#If the type is still a list, that means we did not find a method with the method we want
			rsp = Response("Error: Wrong Method", status=405, content_type='text/html')
			return rsp(environ, start_response)

		del route["controller"]
		args = list(route.values())
		if hasattr(controller, "_auth"):
			autherization = controller._auth
			cookie = controller._auth_cookie
			error = controller._error
			if cookie:
				token = request.cookies.get(cookie)
				if not token:
					if error:
						return error()(environ, start_response)
					rsp = Response(f"Error: No JWT found in the '{cookie}' cookie")
					return rsp(environ, start_response)
			else:
				token = request.headers.get("Authorization")
				if not token:
					if error:
						return error()(environ, start_response)
					rsp = Response("Error: No JWT token found in the Autherization header")
					rsp.status_code = 400
					return rsp(environ, start_response)
				if token.startswith("Bearer"):
					token = token[7:]

			if not autherization._verify(token):
				if error:
					return error()(environ, start_response)
				rsp = Response("Error: Invalid signature in token")
				rsp.status_code = 403
				return rsp(environ, start_response)

		if hasattr(controller, "_validator"):
			validator = controller._validator
			error = controller._error
			# Go through the request data, only json and html are supported
			try:
				data = request.json
			except:
				try:
					data = request.form
				except:
					if error:
						return error()
					rsp = Response("Error: No data provided")
					rsp.status_code = 400
					return rsp
			if not data:
				if error:
					return error()
				rsp = Response("Error: No data provided or data was malformed")
				rsp.status_code = 400
				return rsp(environ, start_response)

			validation_result = validate(validator, error, data)
			if validation_result:
				return validation_result(environ, start_response)

		return controller(request, *args)(environ, start_response)

	def __call__(self, environ, start_response):
		return self.wsgi_handler(environ, start_response)

