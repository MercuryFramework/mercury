def route(method, url):
    def decorator(func):
        func._route_method = method
        func._route_url = url
        return func
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

