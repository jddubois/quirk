import os
import requests
import hashlib
from ..utils import dbGetSession
from ..models import Deal, UserDeal, User
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_
from math import sin, cos, sqrt, radians, acos
from werkzeug.utils import secure_filename

deal_controller = Blueprint('deal_controller', __name__)

# Constant for file types allowed
ALLOWED_EXTENSIONS = set(['jpg', 'png'])

@deal_controller.route("/deals", methods=['GET'])
def getDeals():
    latitude = radians(float(request.args.get("latitude")))
    longitude = radians(float(request.args.get("longitude")))
    user = request.args.get("user_id")
    radius = 3959.0 # miles

    dbSession = dbGetSession()

    if user is None:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'User does not exist'
            }), 404)

    # TODO: order by closeness
    deals = dbSession.query(Deal, UserDeal).\
    filter(and_(UserDeal.deal_id != Deal.id, acos(sin(latitude) * sin(Deal.latitude)) * radius <= 15.0)).all()
    #  * sin(float(Deal.latitude)) + cos(latitude) * cos(float(Deal.latitude)) * cos(float(Deal.longitude - (longitude)))

    for deal in deals:
        # Make request and see if this deal has been used
        deal.serialize()

    dbSession.close()
    return make_response(jsonify({
        'deals' : deals
        }))

# TODO:, user authentication for requests
@deal_controller.route("/deal", methods=['POST'])
def createDeal():
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")
    business_name = request.args.get("business_name")
    deal_name = request.args.get("deal_name")
    deal_text = request.args.get("deal_text")

    # Make sure all values are passed in
    if latitude is None or longitude is None or business_name is None or deal_name is None or deal_text is None:
        return make_response(jsonify({
            'error' : 'Missing parameters'
        }), 422)

    dbSession = dbGetSession()
    new_deal = Deal(latitude = latitude, longitude = longitude, business_name = business_name, deal_name = deal_name, deal_text = deal_text)
    dbSession.add(new_deal)
    dbSession.commit()

    return make_response(jsonify({
        'id' : new_deal.id
    }), 200)

@deal_controller.route("/deal/<deal_id>/update_photo", methods=['PUT'])
def updatePhoto(deal_id):
    if 'file' not in request.files:
        return make_response(jsonify({
            'error' : 'No file in request'
        }), 422)

    file = request.files['file']

    # empty file
    if file.filename == '':
        return make_response(jsonify({
            'error' : 'No file chosen'
        }), 422)

    dbSession = dbGetSession()
    deal = dbSession.query(Deal).filter(Deal.id == deal_id).one_or_none()

    if deal is None:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'Invalid deal_id'
        }), 422)

    filename = ''
    if file and allowed_file(file.filename):
        filename = hashlib.md5(deal_id + secure_filename(file.filename)).hexdigest() + returnFileExtension(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    deal.photo_id = filename
    dbSession.commit()
    dbSession.close()

    return make_response(jsonify({
            'success' : 'File uploaded'
        }))


@deal_controller.route("/deal/<id>", methods=['PUT'])
def updateDeal(deal_id):
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")
    business_name = request.args.get("business_name")
    deal_name = request.args.get("deal_name")
    deal_text = request.args.get("deal_text")

    # Make sure all values are passed in
    if latitude is None or longitude is None or business_name is None or deal_name is None or deal_text is None:
        return make_response(jsonify({
            'error' : 'Missing parameters'
        }), 422)

    dbSession = dbGetSession()
    deal = deal = dbSession.query(Deal).filter(Deal.id == deal_id).one_or_none()
    deal.latitude = latitude
    deal.longitude = longitude
    deal.business_name = business_name
    deal.deal_name = deal_name
    deal.deal_text = deal_text
    dbSession.commit()
    dbSession.close()

    return make_response(jsonify({
            'success' : 'Deal updated'
        }))

@deal_controller.route("/deals", methods=['PUT'])
def useDeal():
    user = request.args.get('user_id')
    dealId = request.args.get('deal_id')

    dbSession = dbGetSession()

    # Make sure user exists
    if user is None:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'User does not exist'
            }), 404)

    # Make sure deal exists
    deal = dbSession.query(Deal).filter(Deal.id == dealId).one_or_none()
    if deal is None:
        dbSession.close()
        return make_response(jsonify({
            'error' : "Deal does not exist"
            }))

    # Make sure they aren't trying to use the deal again
    deal = dbSession.query(UserDeal, Deal).filter(and_(Deal.id == dealId, UserDeal.deal_id == dealId, UserDeal.user_id == user)).one_or_none()
    # Deal.id == dealId, UserDeal.deal_id == dealId, UserDeal.user_id == user.id
    if deal is not None:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'Deal has already been used'
            }), 403)

    # Use deal
    newUse = UserDeal(user_id = user, deal_id = dealId)
    dbSession.add(newUse)
    dbSession.commit()
    dbSession.close()

    return make_response(jsonify({
        'success' : 'deal used'
        }), 200)

@deal_controller.route("/deal/<deal_id>", methods=['DELETE'])
def deleteDeal(deal_id):
    dbSession = dbGetSession()

    dbSession.query(Deal).filter(Deal.id == deal_id).delete()
    dbSession.commit()
    dbSession.close()

    return make_response(jsonify({
        'success' : 'Deleted deal'
        }), 200)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def returnFileExtension(filename):
    return '.' + filename.rsplit('.', 1)[1].lower()
