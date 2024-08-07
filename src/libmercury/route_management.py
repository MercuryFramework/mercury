from functools import wraps

def useValidator(validator):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper._validator = validator
        return wrapper
    return decorator

def route(method, url):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper._route_method = method
        wrapper._route_url = url
        return wrapper
    return decorator
# HTTP method specific decorators
def GETRoute(url):
    return route('GET', url)

def POSTRoute(url):
    return route('POST', url)

class Route:
    def __init__(self, method, url, handler):
        self.method = method
        self.url = url
        self.handler = handler

    def __repr__(self):
        return f"Route(method={self.method}, url='{self.url}', handler={self.handler})"

