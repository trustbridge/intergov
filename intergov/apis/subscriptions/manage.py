from flask_script import Manager
from libtrustbridge.utils.specs import GenerateApiSpecCommand

from intergov.apis.subscriptions.app import create_app
from intergov.apis.subscriptions.conf import Config

app = create_app(config_object=Config())
manager = Manager(app)
manager.add_command('generate_swagger', GenerateApiSpecCommand)

if __name__ == "__main__":
    manager.run()
