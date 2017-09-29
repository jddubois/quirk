from flask import Flask, Blueprint
from flask import render_template

test = Blueprint('test', __name__, template_folder='templates')

@test.route("/")
def indexTestRoute():
    return "test"

@test.route("/test")
def loginTestRoute():
    return render_template("index.html")
