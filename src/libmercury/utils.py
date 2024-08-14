from werkzeug import Response

def get_connection():
	from src.cargo.connection import Connection
	return Connection

def find_or_404(model, **kwargs):
	result = get_connection().Session.query(model).filter_by(**kwargs).first()
	if result == None:
		return Response("<h1>404 Not Found</h1>", status=404)
	return result

def expires_in(seconds: int):
	import time
	return int(time.time())+seconds
