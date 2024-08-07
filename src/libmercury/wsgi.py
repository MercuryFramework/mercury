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
            if route.url[-1] == "/":
                route.url = route.url[:-1]
            self.mapper.connect(None, route.url, controller=route.handler)

    def load_project(self):
        # Load the map.json file
        with open('map.json') as f:
            config = json.load(f)
        
        # Load and register routes from controllers
        for controller_path in config.get('controlers', []):
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
            print(f"[WARNING]Controller class {controller_class_name} not found in module {module_name}")
            return
    
        # Iterate over all attributes in the class
        for method_name in dir(controller_class):
            method = getattr(controller_class, method_name)
            
            # Check if the attribute is callable and has route attributes
            if callable(method) and hasattr(method, '_route_method') and hasattr(method, '_route_url'):
                route = Route(method._route_method, method._route_url, method)
                self.routes.append(route)

    def wsgi_handler(self, environ, start_response):
        # Create a Request object from WSGI environment
        request = Request(environ)
        
        method = request.method
        path = request.path
        try:
            route = dict(self.mapper.match(path))
        except:
            response = Response('Not Found', status=404, content_type='text/html')
            return response(environ, start_response)
        controller = route.get("controller")
        if controller == None:
            response = Response('Not Found', status=404, content_type='text/html')
            return response(environ, start_response)
        if not method == controller._route_method:
            response = Response('Wrong method', status=405, content_type='text/html')
            return response(environ, start_response)
        del route["controller"]
        args = list(route.values())
        if hasattr(controller, "_auth"):
            autherization = controller._auth
            cookie = controller._auth_cookie
            if cookie:
                token = request.cookies.get(cookie)
                if not token:
                    rsp = Response(f"Error: No JWT found in the '{cookie}' cookie")
                    return rsp(environ, start_response)
            else:
                token = request.headers.get("Authorization")
                if not token:
                    rsp = Response("Error: No JWT token found in the Autherization header")
                    rsp.status_code = 400
                    return rsp(environ, start_response)
                if token.startswith("Bearer"):
                    token = token[7:]

            try:
                if not autherization._verify(token):
                    rsp = Response("Error: Invalid signature provided")
                    rsp.status_code = 400
                    return rsp(environ, start_response)
            except ValueError:
                rsp = Response("Error: Invalid or malformed JWT token")
                rsp.status_code = 400
                return rsp(environ, start_response)

        if hasattr(controller, "_validator"):
            validator = controller._validator

            #Find all fields 
            class_vars = {}
            for name, value in validator.__dict__.items():
                if not name.startswith('__') and not callable(value):
                    class_vars[name] = value
            
            #Go through the request data, only json and html are supported
            try:
                data = request.json
            except:
                try:
                    data = request.form
                except:
                    rsp = Response("Error: No data provided")
                    return rsp(environ, start_response)
            if not data:
                rsp = Response("Error: No data provided")
                return rsp(environ, start_response)

            class_fields = list(class_vars.keys())
            request_fields = list(data.keys())

            for field in class_fields:
                if field not in request_fields:
                    rsp = Response(f"Error: Missing field '{field}'")
                    return rsp(environ, start_response)
                else:
                    value = data[field]
                    validator = class_vars[field]
                    if not validator.validate(value):
                        rsp = Response(f"Error: type mismatch in field '{field}'")
                        return rsp(environ, start_response)

        return controller(request, *args)(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_handler(environ, start_response)

