import requests
from ..utils import dbGetSession
from ..models import User, Match
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import or_, and_
from twilio.rest import Client

matches_controller = Blueprint('matches_controller', __name__)

# Add user quirks to returned data
@matches_controller.route("/matches", methods=['GET'])
def getMatchesRoute():
    dbSession = dbGetSession()
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    matches = dbSession.query(Match).filter(and_(Match.has_chat==False, or_(Match.user_one_id == session["user_id"], Match.user_two_id == session["user_id"]))).all()
    matchesDict = [ match.serialize(session["user_id"], dbSession) for match in matches ]
    dbSession.close()
    return make_response(jsonify({
        "matches": matchesDict
    }), 200)

@matches_controller.route("/match/<userId>", methods=['DELETE'])
def unmatchRoute(userId):
    dbSession = dbGetSession()
    if not userHasPermission():
        dbSession.close()
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    dbQueryOne = and_(Match.user_one_id == userId, Match.user_two_id == session['user_id'])
    dbQueryTwo = and_(Match.user_one_id == session['user_id'], Match.user_two_id == userId)
    match = dbSession.query(Match).filter(or_(dbQueryOne, dbQueryTwo)).one_or_none()
    if match is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Match not found'
        }), 404)
    dbSession.delete(match)
    #Check has chat
    dbQueryThree = and_(Chat.user_one_id == userId, Chat.user_two_id == session['user_id'])
    dbQueryFour = and_(Chat.user_one_id == session['user_id'], Chat.user_two_id == userId)
    chat = dbSession.query(Chat).filter(or_(dbQueryThree, dbQueryFour)).one_or_none()
    if chat is None:
        dbSession.close()
        return

    account = app.config['TWILIO_ACCOUNT_SID']
    token = app.config['TWILIO_AUTH_TOKEN']
    client = Client(account, token)

    # Delete the channel
    response = client.chat \
                 .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
                 .channels(chat.id) \
                 .delete()

    #Delete chat from Database
    dbSession.delete(chat)
    dbSession.commit()
    dbSession.close()
    return make_response("", 200)
#
# # Delete channel upon unmatching
# @matches_controller.route('/<userId>',  methods=['DELETE'])
# def deleteChannel(userId):
#
#     #Check user is in session
#     if 'user_id' not in session:
#         return make_response(jsonify({
#             'error': 'Access denied'
#         }), 403)
#
#     dbSession = dbGetSession()
#
#     #Check has match
#     dbQueryOne = and_(Match.user_one_id == userId, Match.user_two_id == session['user_id'])
#     dbQueryTwo = and_(Match.user_one_id == session['user_id'], Match.user_two_id == userId)
#     match = dbSession.query(Match).filter(or_(dbQueryOne, dbQueryTwo)).one_or_none()
#     if match is None:
#         dbSession.close()
#         return
#
#     #Check has chat
#     dbQueryThree = and_(Chat.user_one_id == userId, Chat.user_two_id == session['user_id'])
#     dbQueryFour = and_(Chat.user_one_id == session['user_id'], Chat.user_two_id == userId)
#     chat = dbSession.query(Chat).filter(or_(dbQueryThree, dbQueryFour)).one_or_none()
#     if chat is None:
#         dbSession.close()
#         return
#
#     account = app.config['TWILIO_ACCOUNT_SID']
#     token = app.config['TWILIO_AUTH_TOKEN']
#     client = Client(account, token)
#
#     # Delete the channel
#     response = client.chat \
#                  .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
#                  .channels(chat.id) \
#                  .delete()
#
#     #Delete 1 Chat from Database
#     dbSession.delete(chat)
#     dbSession.commit()
#     dbSession.close()
#
# # Delete chat upon unmatching
# @matches_controller.route('/<userId>',  methods=['DELETE'])
# def deleteChat(userId):
#     #Check user is in session
#     if 'user_id' not in session:
#         return make_response(jsonify({
#             'error': 'Access denied'
#         }), 403)
#
#     dbSession = dbGetSession()
#
#     # Check has match
#     dbQueryOne = and_(Match.user_one_id == userId, Match.user_two_id == session['user_id'])
#     dbQueryTwo = and_(Match.user_one_id == session['user_id'], Match.user_two_id == userId)
#     match = dbSession.query(Match).filter(or_(dbQueryOne, dbQueryTwo)).one_or_none()
#
#     if match is None:
#         dbSession.close()
#         return
#
#     #Check has chat
#     dbQueryThree = and_(Chat.user_one_id == userId, Chat.user_two_id == session['user_id'])
#     dbQueryFour = and_(Chat.user_one_id == session['user_id'], Chat.user_two_id == userId)
#     chat = dbSession.query(Chat).filter(or_(dbQueryThree, dbQueryFour)).one_or_none()
#     if chat is None:
#         dbSession.close()
#         return
#
#     dbSession.delete(chat)
#     dbSession.commit()
#     dbSession.close()

# Fix this to ensure correct permissions
def userHasPermission():
    if not 'user_id' in session:
        return False
    return True
