from functools import wraps
from .validate import validate
import re
class String:
	def __init__(self, **kwargs) -> None:
		self.kwargs = kwargs
		self.min = self.kwargs.get("min")
		self.max = self.kwargs.get("max")
		
		self.minimum = self.kwargs.get("minimum")
		self.maximum = self.kwargs.get("maximum")

		self.regex = self.kwargs.get("regex")

		if self.min == None:
			self.min = self.minimum
		if self.max == None:
			self.max = self.maximum

	def validate(self, string) -> bool:
		if type(string) != str:
			return False
		if self.regex:
			# Using fullmatch to ensure the whole string matches the pattern
			if re.compile(self.regex).fullmatch(string):
				return True
			else:
				return False

		if self.min:
			if len(string) < self.min:
				return False
		
		if self.max:
			if len(string) > self.max:
				return False

		return True #Return true if all conditions are met

class Integer:
	def __init__(self, **kwargs) -> None:
		self.kwargs = kwargs
		self.min = self.kwargs.get("min")
		self.max = self.kwargs.get("max")
		
		self.minimum = self.kwargs.get("minimum")
		self.maximum = self.kwargs.get("maximum")

		if self.min == None:
			self.min = self.minimum
		if self.max == None:
			self.max = self.maximum

	def validate(self, integer) -> bool:
		if type(integer) != int:
			return False

		if self.min:
			if integer < self.min:
				return False
		
		if self.max:
			if integer > self.max:
				return False

		return True #Return true if all conditions are met

class Float:
	def __init__(self, **kwargs) -> None:
		self.kwargs = kwargs
		self.min = self.kwargs.get("min")
		self.max = self.kwargs.get("max")
		
		self.minimum = self.kwargs.get("minimum")
		self.maximum = self.kwargs.get("maximum")

		if self.min is None:
			self.min = self.minimum
		if self.max is None:
			self.max = self.maximum

	def validate(self, value) -> bool:
		if type(value) not in [float, int]:  # Allow int as it can be considered a valid float
			return False

		if self.min is not None:
			if value < self.min:
				return False
		
		if self.max is not None:
			if value > self.max:
				return False

		return True  # Return true if all conditions are met

class Array:
	def __init__(self, element_type=None, **kwargs) -> None:
		self.element_type = element_type
		self.kwargs = kwargs
		self.min = self.kwargs.get("min")
		self.max = self.kwargs.get("max")

		self.minimum = self.kwargs.get("minimum")
		self.maximum = self.kwargs.get("maximum")

		if self.min is None:
			self.min = self.minimum
		if self.max is None:
			self.max = self.maximum

	def validate(self, array) -> bool:
		if not isinstance(array, list):  # Ensure the input is a list
			return False

		if self.min is not None:
			if len(array) < self.min:
				return False

		if self.max is not None:
			if len(array) > self.max:
				return False

		if self.element_type:  # If element_type is provided, validate each element
			for item in array:
				if hasattr(self.element_type, "__nested_validator"):
					# If the element_type is an Object, validate the nested structure
					if not isinstance(item, dict) or validate(self.element_type, None, item):
						return False
				elif not self.element_type.validate(item):
					return False

		return True  # Return true if all conditions are met

class Boolean:
	def __init__(self) -> None:
		pass #Its a boolean, what do you want it to do
			
	def validate(self, boolean) -> bool:
		if type(boolean) != boolean:
			return False
		return True

class Union:
	def __init__(self, *args) -> None:
		self.types = args

	def validate(self, any) -> bool:
		for typechecks in self.types:
			if typechecks.validate(any):
				#If a type check passes, it is valid
				return True
		return False

class Any:
	def validate(self, value) -> bool:
		return True

def Object(**kwargs):
	exclude_from_validation = kwargs.get('exclude_from_validation', False)
	
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)
		wrapper.__nested_validator = True
		wrapper.__exclude_from_validation = exclude_from_validation
		return wrapper
	return decorator

