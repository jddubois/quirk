import requests
from ..utils import dbGetSession
from flask import Flask, Blueprint
from flask import current_app as app
from flask import jsonify, request, session, make_response
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant

message_controller = Blueprint('matches_controller', __name__)

# Fix this to ensure correct permissions
def userHasPermission():
    if not 'user_id' in session:
        return False
    return True

@message_controller.route('/twilio',  methods=['GET'])
def twilioRoute():

    # Check user permissions
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    # get credentials for environment variables
    account_sid = app.config['TWILIO_ACCOUNT_SID']
    api_key = app.config['TWILIO_API_KEY']
    api_secret = app.config['TWILIO_API_SECRET']
    service_sid = app.config['TWILIO_CHAT_SERVICE_SID']

    # get user identity
    identity = session['user_id']

    # Create a unique endpoint ID for the logged in user
    device_id = request.args.get('device')
    endpoint = "Quirk:{0}:{1}".format(identity, device_id)

    # Create access token with credentials
    token = AccessToken(account_sid, api_key, api_secret, identity=identity)

    # Create a Chat grant and add to token
    chat_grant = ChatGrant(endpoint_id=endpoint, service_sid=service_sid)
    token.add_grant(chat_grant)

    # Return token info as JSON
    return make_response(jsonify({
            'identity': identity,
            'token': token.to_jwt()
        }), 200)
