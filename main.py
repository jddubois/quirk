import os
from quirk import controllers
from quirk import models
from quirk import utils
from flask import Flask
from flask import session, request, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['jpg', 'png'])

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super-secret'
app.config['FB_APP_SECRET'] = '4045330ee279f34938dcb1dc7895b4a8'
app.config['FB_APP_ID'] = '1978475429031886'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/root/quirk/quirk/images'

app.register_blueprint(controllers.login_controller)
app.register_blueprint(controllers.user_controller)
app.register_blueprint(controllers.quirk_controller)
app.register_blueprint(controllers.deal_controller)
app.register_blueprint(controllers.test_controller)

@app.before_first_request
def initialize():
    utils.dbInitialize()
    controllers.fbInitialize()

if __name__ == "__main__":
    app.run(host='0.0.0.0')
