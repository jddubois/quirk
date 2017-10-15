import requests
from ..utils import dbGetSession
from ..models import User
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import or_, and_

matches_controller = Blueprint('matches_controller', __name__)

# Add user quirks to returned data
@matches_controller.route("/matches", methods=['GET'])
def getMatches():
    dbSession = dbGetSession()
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    matches = dbSession.query(Match).filter(or_(Match.userOneId == session["user_id"], Match.userTwoId == session["user_id"])).all()
    if matches is None:
        return jsonify({
            [].serialize()
        })
    matchIdAndPhoto = []
    for each in matches:
        if each.userOneId == session["user_id"]: #match is userTwo
            photo = dbSession.query(Photo).filter(Photo.userId == each.userTwoId).all()
            if photo is None:
                matchIdAndPhoto.append({'matchedUserId': each.userTwoId, 'photo': None})
            else:
                matchIdAndPhoto.append({'matchedUserId': each.userTwoId, 'photo': photo[0]})
        else: #match is userOne
            photo = dbSession.query(Photo).filter(Photo.userId == each.userOneId).all()
            if photo is None:
                matchIdAndPhoto.append({'matchedUserId': each.userOneId, 'photo': None})
            else:
                matchIdAndPhoto.append({'matchedUserId': each.userOneId, 'photo': photo[0]})
    dbSession.close()
    return make_response(jsonify({
        "matchIdAndPhoto": [item.serialize() for item in matchIdAndPhoto]
    }), 200)


@matches_controller.route("/unmatch/<userId>", methods=['DELETE'])
def unmatch(userId):
    dbSession = dbGetSession()
    if not userHasPermission():
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    dbSession.query(Match).filter(userOneId == session["user_id"] and_ userTwoId == UNuserId).delete()
    dbSession.commit()
    dbSession.close()

# Fix this to ensure correct permissions
def userHasPermission(userId, dbSession):
    if not 'user_id' in session:
        return False
