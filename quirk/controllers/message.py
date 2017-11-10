import requests
from ..utils import dbGetSession
from flask import Flask, Blueprint
from flask import current_app as app
from flask import jsonify, request, session, make_response
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from sqlalchemy import and_, or_
from ..models import Chat


message_controller = Blueprint('matches_controller', __name__)

def setupNotifications():
    # Find your Account Sid at https://www.twilio.com/console/account/settings
    account_sid = app.config['TWILIO_ACCOUNT_SID']
    # Create an API Key and Secret at
    # https://www.twilio.com/console/chat/dev-tools/api-keys
    api_key = app.config['TWILIO_API_KEY']
    api_secret = app.config['TWILIO_API_SECRET']
    # Your Chat Service SID from https://www.twilio.com/console/chat/services
    service_sid = app.config['TWILIO_CHAT_SERVICE_SID']

    # Authenticate with Twilio
    client = Client(api_key, api_secret, account_sid)
    template = 'You have a new message from ${USER}! ${MESSAGE}'
    service = client.chat \
                    .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
                    .update(
                        notifications_added_to_channel_enabled=True,
                        notifications_added_to_channel_template=template,
                        notifications_added_to_channel_sound='default')

# TODO: Fix this to ensure correct permissions
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

    # Check user permissions
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    dbSession = dbGetSession()

    userId = session['user_id']

    chats = dbSession.query(Chat).filter(or_(Chat.user_one_id == userId, Chat.user_two_id == userId)).all()

    response = make_response(jsonify({
        'chats' : [ c.serialize(userId, dbSession) for c in chats ]
    }), 200)

    dbSession.close()

    return response

# TODO
# Creates a new chat channel betwen logged-in user and user_id
# Need to make sure that a match exists between these userHasPermission
# If either user does not have Twilio data, make them a USER
@message_controller.route('/message/<userId>',  methods=['POST'])
def sendMessageRoute(userId):

    # Check user permissions
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    dbSession = getDbSession()

    dbQueryOne = and_(Match.user_one_id == userId, Match.user_two_id == session['user_id'])
    dbQueryTwo = and_(Match.user_one_id == session['user_id'], Match.user_two_id == userId)
    match = dbSession.query(Match).filter(or_(dbQueryOne, dbQueryTwo)).one_or_none()

    if match is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Match does not exist'
        }), 403)

    requestData = request.get_json()

    client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

    if not match.has_chat:

        # Create the channel
        channel = client.chat \
                .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
                .channels \
                .create(type=private)

        newChat = Chat(id= channel.sid, user_one_id= match.user_one_id, user_two_id= match.user_two_id, last_message= requestData['message'])

        dbSession.add(newChat)
        dbSession.commit()

        channel.members.create(match.user_one_id)
        channel.members.create(match.user_two_id)

        # send message
        user = dbSession.query(User).filter(User.id == session['user_id']).one_or_none()

        channel.messages.create(body=requestData['message']) #, from=user.name

    else:

        # Chat already exists, just send message
        currChat = dbSession.query(Chat).filter(user_one_id = match.user_one_id, user_two_id= match.user_two_id).one_or_none()

        if currChat is None:
            dbSession.close()
            return make_response(jsonify({
                'error': 'chat does not exist'
            }), 404)

        channel = client.chat \
            .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
            .channels(currChat.id) \
            .fetch()

        channel.messages.create(body=requestData['message']) #, from=user.name

    dbSession.close()
    return make_response(jsonify({
            'success': 'message was sent'
        }), 200)


@message_controller.route('/message/<userId>',  methods=['GET'])
def getMessagesRoute(userId):

    # Check user permissions
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    dbSession = getDbSession()

    dbQueryOne = and_(Match.user_one_id == userId, Match.user_two_id == session['user_id'])
    dbQueryTwo = and_(Match.user_one_id == session['user_id'], Match.user_two_id == userId)
    match = dbSession.query(Match).filter(or_(dbQueryOne, dbQueryTwo)).one_or_none()

    if match is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Match does not exist'
        }), 403)

    if not match.has_chat:
        dbSession.close()
        return make_response(jsonify({
            'messages': []
        }), 200)

    currChat = dbSession.query(Chat).filter(user_one_id = match.user_one_id, user_two_id= match.user_two_id).one_or_none()

    if currChat is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'chat does not exist'
        }), 404)

    client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

    channel = client.chat \
        .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
        .channels(currChat.id) \
        .fetch()

    messages = channel.messages.list()

    dbSession.close()
    return make_response(jsonify({
            'messages': messages
        }), 200)


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

