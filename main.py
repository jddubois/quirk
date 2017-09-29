import quirk
import controllers
from flask import Flask
from flask import session, request, render_template


app = Flask(__name__)

app.config['SECRET_KEY'] = 'super-secret'
app.config['FB_APP_SECRET'] = '4045330ee279f34938dcb1dc7895b4a8'
app.config['FB_APP_ID'] = '1978475429031886'

app.register_blueprint(controllers.login)
app.register_blueprint(controllers.test)

@app.before_first_request
def initialize():
    quirk.dbInitialize()
    controllers.fbInitialize()

if __name__ == "__main__":
    app.run(host='0.0.0.0')
