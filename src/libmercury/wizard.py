from json import dumps
from json import loads
from .version import version
import os
class CLI:
    def __init__(self, arguments) -> None:
        self.arguments = arguments

    def execute(self):
        try:
            with open(".mercury", "r") as f:
                os.chdir(f.read())
            print("Directory changed! (:")
        except:
            pass
        del self.arguments[0]
        commands = {
            "init": self.init,
            "create": self.create,
            "migrate": self.migrate,
            "run": self.run,
        }
        if len(self.arguments) < 1:
            self.version_display()
        try:
            commands[self.arguments[0]]()
        except KeyError:
            self.unknown_command()

    def init(self):
        print(f"Mercury {version} project initializer")
        directory = input("Name of directory to use: ")
        interpreter = input("Please provide your python interpreter(python, python3, etc): ")

        #Create project file structure
        os.mkdir(directory) 
        os.mkdir(f"{directory}/src")
        os.mkdir(f"{directory}/src/controlers")
        os.mkdir(f"{directory}/src/validators")
        os.mkdir(f"{directory}/src/cargo")
        os.mkdir(f"{directory}/src/cargo/migrations")
        os.mkdir(f"{directory}/src/security")
        
        #Create files
        with open(f"{directory}/map.json", "w") as f:
            f.write(dumps({
                "interpreter": interpreter,
                "version": version,
                "controlers": [],
                "models": [],
                "validators": [],
                "security": []
            }))

        with open(f"{directory}/src/cargo/dev.db", "w") as f:
            f.write("")

        with open(f"{directory}/src/cargo/db_connect.json", "w") as f:
            f.write(dumps({
                "url": "sqlite:///src/models/dev.db",
            }))

        with open(f"{directory}/app.py", "w") as f:
            f.write("""from libmercury.wsgi import WSGIApp
from werkzeug.serving import run_simple
app = WSGIApp()
app.load_project()
run_simple("localhost", 8000, app)
                    """)

        #Create .mercury files that allow us to run commands from anywhere in the file structure
        with open(f"{directory}/src/.mercury", "w") as f:
            f.write(f"{os.getcwd()}/{directory}")
        with open(f"{directory}/src/controlers/.mercury", "w") as f:
            f.write(f"{os.getcwd()}/{directory}")
        with open(f"{directory}/src/validators/.mercury", "w") as f:
            f.write(f"{os.getcwd()}/{directory}")
        with open(f"{directory}/src/security/.mercury", "w") as f:
            f.write(f"{os.getcwd()}/{directory}")
        with open(f"{directory}/src/cargo/.mercury", "w") as f:
            f.write(f"{os.getcwd()}/{directory}")
        with open(f"{directory}/src/cargo/migrations/.mercury", "w") as f:
            f.write(f"{os.getcwd()}/{directory}")

    def create(self):
        if len(self.arguments) < 2:
            print("Error: Command 'create' requires at least 2 parameters")
            print("Usage:")
            print("create <thing> <named>")
        
        thing = self.arguments[1]
        named = self.arguments[2]

        things = {
            "controler": self._create_controler,
            "preprocesser": self._create_preprocesser,
            "model": self._create_model,
            "jwt": self._create_jwt,
        }
        try:
            things[thing](named)
        except KeyError:
            print(f"Error: Unknown createable {thing}")
            print("Usage:")
            print("create <thing> <named>")
    
    def _create_controler(self, name):
        #Create placeholder
        with open(f"src/controlers/{name}Controler.py", "w") as f:
            f.write(f"""from libmercury import GETRoute, Response
class {name}Controler:
    @GETRoute("/example")
    def example(request):
        response = Response("<h1>Example Page</h1>")
        response.headers['Content-Type'] = 'text/html'
        return response""")
        
        #Update Map.json
        with open("map.json", "r") as f:
            map_json = loads(f.read())
            map_json["controlers"].append(f"src/controlers/{name}Controler.py")
        with open("map.json", "w") as f:
            f.write(dumps(map_json))

    def _create_preprocesser(self, name):
        pass

    def _create_model(self, name):
        pass

    def _create_jwt(self, name):
        pass

    def migrate(self):
        pass

    def run(self):
        pass

    def unknown_command(self):
        pass

    def version_display(self):
        print(r""" __  __                               
|  \/  | ___ _ __ ___ _   _ _ __ _   _ 
| |\/| |/ _ \ '__/ __| | | | '__| | | |
| |  | |  __/ | | (__| |_| | |  | |_| |
|_|  |_|\___|_|  \___|\__,_|_|   \__, |
                                 |___/ """)
        print(version)
