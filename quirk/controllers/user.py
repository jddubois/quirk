import requests
from ..utils import dbGetSession
from ..models import User, Report
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_

user_controller = Blueprint('user_controller', __name__)

# Add user quirks to returned data
@user_controller.route("/user/<userId>", methods=['GET'])
def getUserRoute(userId):
    dbSession = dbGetSession()
    if not userHasPermission(userId, dbSession, False):
        dbSession.close()
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    user = dbSession.query(User).filter(User.id == userId).one_or_none()
    dbSession.close()
    if user is None:
        return make_response(jsonify({
            'error': 'User not found'
        }), 404)
    return make_response(jsonify({
        'user': user.serialize()
    }), 200)

@user_controller.route("/user/<userId>", methods=['PUT'])
def updateUserRoute(userId):
    dbSession = dbGetSession()
    if not userHasPermission(userId, dbSession, False):
        dbSession.close()
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    user = dbSession.query(User).filter(User.id == userId).one_or_none()
    if user is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'User not found'
        }), 404)
    # Iterate over request data and update user accordingly
    if request.get_json() is not None:
        user.set(request.get_json())
        dbSession.commit()
    dbSession.close()

    dbSession = dbGetSession()
    user = dbSession.query(User).filter(User.id == userId).one_or_none()
    dbSession.close()

    return make_response(jsonify({
        'user': user.serialize()
    }), 200)

@user_controller.route("/report/<userId>", methods=['POST'])
def reportUserRoute(userId):
    dbSession = dbGetSession()
    if not userHasPermission(userId, dbSession, False):
        dbSession.close()
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    reportData = request.get_json()
    if  reportData is not None and reportData['body'] is not None:
        report = Report(reporter_id=session['user_id'], reportee_id=userId, body=reportData['body'])
        dbSession.add(report)
        dbSession.commit()
        dbSession.close()
        return make_response(jsonify({
            'report': report.serialize()
        }), 200)
    dbSession.close()
    return make_response(jsonify({
        'error': 'No report body found'
    }), 400)

# Fix this to ensure correct permissions
def userHasPermission(userId, dbSession, isUpdate):
    if not 'user_id' in session:
        return False
    if session['user_id'] == userId:
        return True
    if not isUpdate:
        dbQueryOne = and_(Match.user_one_id == userId, Match.user_two_id == session['user_id'])
        dbQueryTwo = and_(Match.user_one_id == session['user_id'], Match.user_two_id == userId)
        match = dbSession.query(Match).filter(or_(dbQueryOne, dbQueryTwo)).one_or_none()
        if match is not None:
            return True
    return False
