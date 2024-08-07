import re
class string:
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

    def validate(self, string):
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

class integer:
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

    def validate(self, integer):
        if type(integer) != int:
            return False

        if self.min:
            if integer < self.min:
                return False
        
        if self.max:
            if integer > self.max:
                return False

        return True #Return true if all conditions are met
