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

app.config['TWILIO_ACCOUNT_SID'] = "ACcbc2a061491f1c1a3d1d236ac3b2cb16"
app.config['TWILIO_API_KEY'] = "SK5d6931aa13c2b510f12f6f0841280f6a"
app.config['TWILIO_API_SECRET'] = "AWcvPuzdKK1VqA0ZKaLdj7gHyPs42jAE"
app.config['TWILIO_CHAT_SERVICE_SID'] = "IS1d233ce4cf1445e198e43715718f9815"
app.config['TWILIO_AUTH_TOKEN'] = "420ca808acc07ef8156994d48537110a"

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['PHOTO_BASE_URL'] = "http://67.205.134.136:5000/" + app.config['UPLOAD_FOLDER']
app.config['PHOTO_EXT'] = ['jpg', 'png']
app.config['NUM_QUIRKS'] = 5

app.register_blueprint(controllers.login_controller)
app.register_blueprint(controllers.user_controller)
app.register_blueprint(controllers.quirk_controller)
app.register_blueprint(controllers.deal_controller)
app.register_blueprint(controllers.matches_controller)
app.register_blueprint(controllers.business_controller)
app.register_blueprint(controllers.test_controller)

@app.before_first_request
def initialize():
    utils.dbInitialize()
    controllers.fbInitialize()
    controllers.setupNotifications()

if __name__ == "__main__":
    app.run(host='0.0.0.0')
