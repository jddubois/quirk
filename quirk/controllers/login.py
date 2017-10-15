import requests
from ..utils import dbGetSession
from ..models import User
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response

login_controller = Blueprint('login_controller', __name__, template_folder='templates')

# Creates a new user from facebook access token
def createUser(accessToken, dbSession):
    userData = fbGetUser(accessToken)
    id = userData['id']
    name = userData['first_name']
    age = userData['age_range']['min']
    user = User(id=id, name=name, age=age)
    dbSession.add(user)
    dbSession.commit()
    return user

# Returns user if response is a valid login, None otherwise
def fbVerifyUser(fbResponse):
    if fbResponse.status_code is not 200:
        return None
    fbResponseData = fbResponse.json()
    fbResponseData = fbResponseData['data']
    if fbResponseData['is_valid'] is not True:
        return None
    if fbResponseData['app_id'] != app.config['FB_APP_ID']:
        return None
    return fbResponseData['user_id']

# Gets user data from facebook from access token
def fbGetUser(accessToken):
    fbUrl = 'https://graph.facebook.com/me'
    fbParams = {
        'fields': 'first_name,age_range',
        'access_token': accessToken
    }
    fbResponse = requests.get(fbUrl, fbParams)
    if fbResponse.status_code is not 200:
        return None
    return fbResponse.json()

# Handles user creation and session update upon login
def fbHandleResponse(fbResponse, accessToken):
    fbUser = fbVerifyUser(fbResponse)
    if not fbUser:
        return make_response(jsonify({
            'error': 'User verification failed'
        }), 400)
    dbSession = dbGetSession()
    user = dbSession.query(User).filter(User.id == fbUser).one_or_none()
    newUser = user is None
    if newUser:
        user = createUser(accessToken, dbSession)
    session['user_id'] = user.id
    dbSession.close()
    return make_response(jsonify({
        'is_new_user': newUser,
        'user': user.serialize()
    }), 200)

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

@login_controller.route("/login", methods=['POST'])
def loginRoute():
    requestData = request.get_json()
    if requestData['access_token'] is not None:
        fbUrl = 'https://graph.facebook.com/debug_token'
        fbParams = {
            'input_token': requestData['access_token'],
            'access_token': app.config['FB_APP_ACCESS_TOKEN']
        }
        fbResponse = requests.get(fbUrl, fbParams)
        return fbHandleResponse(fbResponse, requestData['access_token'])
    return make_response(jsonify({
        'error': 'Access token not found'
    }), 400)

@login_controller.route("/logout", methods=['POST'])
def logoutRoute():
    if not 'user_id' in session:
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    id = session.pop('user_id')
    return make_response("", 200)
