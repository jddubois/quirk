import requests
import json
from ..utils import dbGetSession
from flask import Flask, Blueprint
from flask import current_app as app
from flask import jsonify, request, session, make_response
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from sqlalchemy import and_, or_
from ..models import Chat, Match, User

message_controller = Blueprint('message_controller', __name__)

def serializeMessage(msg):
    print(msg.body)
    print(msg.attributes)
    attrs = json.loads(msg.attributes)
    print(attrs)
    return {
        'from': attrs['from'],
        'body': msg.body
    }

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

# Sends a message between two users
@message_controller.route('/message/<userId>',  methods=['POST'])
def sendMessageRoute(userId):

    # Check user permissions
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    dbSession = dbGetSession()

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
                .create()

        newChat = Chat(id= channel.sid, user_one_id= match.user_one_id, user_two_id= match.user_two_id, last_message= requestData['message'])
        match.has_chat = True
        dbSession.add(newChat)
        dbSession.commit()

        channel.members.create(match.user_one_id)
        channel.members.create(match.user_two_id)

        # send message
        user = dbSession.query(User).filter(User.id == session['user_id']).one_or_none()

        fromData = json.dumps({'from': session['user_id']})
        print(fromData)
        channel.messages.create(body=requestData['message'], attributes=fromData) #, from=user.name

    else:

        # Chat already exists, just send message
        currChat = dbSession.query(Chat).filter(Chat.user_one_id == match.user_one_id, Chat.user_two_id == match.user_two_id).one_or_none()

        if currChat is None:
            dbSession.close()
            return make_response(jsonify({
                'error': 'chat does not exist'
            }), 404)

        channel = client.chat \
            .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
            .channels(currChat.id) \
            .fetch()

        fromData = json.dumps({'from': session['user_id']})
        print(fromData)
        currChat.last_message = requestData['message']
        channel.messages.create(body=requestData['message'], attributes=fromData) #, from=user.name
        dbSession.commit()

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

    dbSession = dbGetSession()

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

    currChat = dbSession.query(Chat).filter(Chat.user_one_id == match.user_one_id, Chat.user_two_id == match.user_two_id).one_or_none()

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
            'messages': [serializeMessage(msg) for msg in messages]
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
