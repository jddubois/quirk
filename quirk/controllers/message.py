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

@message_controller.route('/message/token',  methods=['GET'])
def getTokenRoute():

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

# TODO
# Gets open chat channels for logged-in user
@message_controller.route('/message/chats',  methods=['GET'])
def getChatsRoute():
    return

# TODO
# Creates a new chat channel betwen logged-in user and user_id
# Need to make sure that a match exists between these userHasPermission
# If either user does not have Twilio data, make them a USER
@message_controller.route('/message/<userId>',  methods=['POST'])
def sendMessageRoute(userId):
    return

@message_controller.route('/message/<userId>',  methods=['GET'])
def getMessagesRoute(userId):
    return


# NOTE
# A channel is a Twilio object that represents a chat between users
# A chat is our object in the database that represents a chat

# TODO NOTIFICATIONS
# Set up notifications

# TODO MATCHES
# Alter match endpoints to only return users with no chats
# Delete channels upon unmatching
# Delete chats upon unmatching

# TODO USER
# Delete Twilio user data and all channels upon deleting user
# Create a Twilio user upon creating user

# TODO
# Get messages
    # Checks if channel exists between users
    # if so, returns n messages from Twilio
    # if not, returns empty messages

# TODO
# Send message
    # Checks if channel exists between users
        # if so, send message on the channel
        # if not,
            # Checks if both users are Twilio user
                # if not for either, create user
            # Creates channel between user
            # Adds chats to database and sets match attribute for has_chat
            # Sends message on channel

# TODO
# Get channels
    # returns all currently open user chat channels
