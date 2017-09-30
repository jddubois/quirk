import requests
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request

login = Blueprint('login', __name__, template_folder='templates')

def fbInitialize():
    fbUrl = 'https://graph.facebook.com/oauth/access_token'
    fbParams = {
        'client_id': app.config['FB_APP_ID'],
        'client_secret': app.config['FB_APP_SECRET'],
        'grant_type': 'client_credentials'
    }
    fbResponse = requests.get(fbUrl, fbParams)
    if fbResponse.status_code == 200:
        fbResponseData = fbResponse.json()
        app.config['FB_APP_ACCESS_TOKEN'] = fbResponseData['access_token']
    else:
        app.config['FB_APP_ACCESS_TOKEN'] = None

@login.route("/login", methods=['POST'])
def loginRoute():
    requestData = request.get_json()
    if requestData['accessToken'] is not None:
        fbUrl = 'https://graph.facebook.com/debug_token'
        fbParams = {
            'input_token': requestData['accessToken'],
            'access_token': app.config['FB_APP_ACCESS_TOKEN']
        }
        fbResponse = requests.get(fbUrl, fbParams)
        if fbResponse.status_code == 200:
            print("Got response")
            return jsonify(fbResponse.json())
    return jsonify({})
