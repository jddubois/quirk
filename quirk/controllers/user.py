import requests
from ..utils import dbGetSession
from ..models import User
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session

user_controller = Blueprint('user_controller', __name__, template_folder='templates')

# Add user quirks to returned data
@user_controller.route("/user/<userId>", methods=['GET'])
def getUserRoute(userId):
    dbSession = dbGetSession()
    if not userHasPermission():
        return jsonify({
            'success': False,
            'error': 'Access denied'
        })
    user = dbSession.query(User).filter(User.id == userId).one_or_none()
    dbSession.close()
    if user is None:
        return jsonify({
            'success': False,
            'error': 'User not found'
        })
    return jsonify({
        'success': True,
        'user': user.serialize()
    })

# Fix this to ensure correct permissions
def userHasPermission(userId, dbSession):
    if not 'user_id' in session:
        return False
