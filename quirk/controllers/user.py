import requests
import os
from ..utils import dbGetSession
from ..models import User, Report, Photo, uuidGet
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_
from werkzeug.utils import secure_filename
from twilio.rest import Client

user_controller = Blueprint('user_controller', __name__)

@user_controller.route("/photo", methods=['POST'])
def uploadPhotoRoute():
    # Check user permissions
    if not 'user_id' in session:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    # Check if file exists
    print('test')
    print(request.files)
    if 'file' not in request.files:
        print('not found')
        return make_response(jsonify({
            'error': 'File not found'
        }), 400)
    file = request.files['file']
    # TODO: Check for file extension / get extension
    extension = request.args.get('extension')
    print(extension)
    if extension is None or extension.lower() not in app.config['PHOTO_EXT']:
        return make_response(jsonify({
            'error': 'File extension not included'
        }), 400)
    # Get thumbnail status
    isThumbnail = request.args.get('thumbnail')
    if isThumbnail is None:
        isThumbnail = False
    # Create photo entry
    photo = Photo(id=uuidGet(), ext=extension, user_id=session['user_id'], thumbnail=isThumbnail)
    # Generate filename
    filename = photo.id + '.' + photo.ext
    # Write to disk
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Add photo to database
        dbSession = dbGetSession()
        dbSession.add(photo)
        dbSession.commit()
        dbSession.close()
        # Return URL
        return make_response(jsonify({
            'url': photo.getUrl()
        }), 200)
    # Return error
    return make_response(jsonify({
        'error': 'File not found'
    }), 400)

#TODO: Complete this
@user_controller.route("/photo", methods=['DELETE'])
def deletePhotoRoute():
    url = request.args.get('url')
    if url is None:
        return make_response(jsonify({
            'error': 'File not found'
        }), 400)
    # Get filename from query parameters
    filename = os.path.basename(url)
    filename = secure_filename(filename)
    # Get photo id
    photoId = filename.split('.')[0]
    dbSession = dbGetSession()
    print(filename)
    print(photoId)
    photo = dbSession.query(Photo).filter(Photo.id == photoId).one_or_none()
    if photo is None:
        return make_response(jsonify({
            'error': 'Photo not found'
        }), 404)
    # Check user permissions
    if not userHasPermission(photo.user_id, dbSession, True):
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)
    # Make database changes
    dbSession.delete(photo)
    dbSession.commit()
    dbSession.close()
    # Remove from disk
    deleteUrl = app.config['UPLOAD_FOLDER'] + '/' + filename
    os.remove(deleteUrl)
    return make_response('', 200)

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

@user_controller.route("/user/<userId>", methods=['DELETE'])
def deleteUserRoute(userId):
    dbSession = dbGetSession()
    if not userHasPermission(userId, dbSession, True):
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

    account = app.config['TWILIO_ACCOUNT_SID']
    token = app.config['TWILIO_AUTH_TOKEN']
    client = Client(account, token)

    #Delete all channels by accessing chats
    chats = dbSession.query(Chat).filter(or_(Chat.user_one_id == userId, Chat.user_two_id == userId)).all()
    for chat in chats:
        response = client.chat \
                     .services(app.config['TWILIO_CHAT_SERVICE_SID']) \
                     .channels(chat.id) \
                     .delete()
    #Delete all photos from disk (see deletePhotoRoute)
    photos = dbSession.query(Photo).filter(Photo.id == userId).all()
    for photo in photos:
        url = photo.getUrl()
        if url is None:
            return make_response(jsonify({
                'error': 'File not found'
            }), 400)
        # Get filename
        filename = os.path.basename(url)
        filename = secure_filename(filename)
        # Remove from disk
        deleteUrl = app.config['UPLOAD_FOLDER'] + '/' + filename
        os.remove(deleteUrl)
    #Delete Twilio User
    client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
    response = client.chat.services('TWILIO_CHAT_SERVICE_SID').users.create(
        identity=userId
    ).delete()
    #Delete user
    dbSession.delete(user)
    dbSession.commit()
    dbSession.close()
    session.pop('user_id')

    return make_response("", 200)

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
