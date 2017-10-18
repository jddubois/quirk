import requests
from ..utils import dbGetSession
from ..models import User, Match
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import or_, and_

matches_controller = Blueprint('matches_controller', __name__)

# Add user quirks to returned data
@matches_controller.route("/matches", methods=['GET'])
def getMatchesRoute():
    dbSession = dbGetSession()
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    #session['user_id'] = '1'
    matches = dbSession.query(Match).filter(or_(Match.user_one_id == session["user_id"], Match.user_two_id == session["user_id"])).all()
    matchesDict = [ match.serialize(session["user_id"], dbSession) for match in matches ]
    dbSession.close()
    return make_response(jsonify({
        "matches": matchesDict
    }), 200)

    # matchIdAndPhoto = []
    # for each in matches:
    #     if each.userOneId == session["user_id"]: #match is userTwo
    #         photo = dbSession.query(Photo).filter(Photo.userId == each.userTwoId).all()
    #         if photo is None:
    #             matchIdAndPhoto.append({'matchedUserId': each.userTwoId, 'photo': None})
    #         else:
    #             matchIdAndPhoto.append({'matchedUserId': each.userTwoId, 'photo': photo[0]})
    #     else: #match is userOne
    #         photo = dbSession.query(Photo).filter(Photo.userId == each.userOneId).all()
    #         if photo is None:
    #             matchIdAndPhoto.append({'matchedUserId': each.userOneId, 'photo': None})
    #         else:
    #             matchIdAndPhoto.append({'matchedUserId': each.userOneId, 'photo': photo[0]})
    # dbSession.close()



@matches_controller.route("/match/<userId>", methods=['DELETE'])
def unmatchRoute(userId):
    dbSession = dbGetSession()
    if not userHasPermission(userId):
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    dbQueryOne = and_(Match.user_one_id == userId, Match.user_two_id == session['user_id'])
    dbQueryTwo = and_(Match.user_one_id == session['user_id'], Match.user_two_id == userId)
    match = dbSession.query(Match).filter(or_(dbQueryOne, dbQueryTwo)).one_or_none()
    if match is  None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Match not found'
        }), 404)
    dbSession.delete(match)
    dbSession.commit()
    dbSession.close()
    return make_response("", 200)

# Fix this to ensure correct permissions
def userHasPermission(userId):
    if not 'user_id' in session:
        return False
    return True
