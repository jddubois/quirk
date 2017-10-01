from flask import Flask, Blueprint
from flask import render_template, session

test_controller = Blueprint('test_controller', __name__, template_folder='templates')

@test_controller.route("/")
def indexTestRoute():
    return "test"

@test_controller.route("/test")
def loginTestRoute():
    if 'user_id' in session:
        return "Logged in"
    return render_template("index.html")
