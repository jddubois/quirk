import os
import requests
import hashlib
import json
from ..utils import dbGetSession
from ..models import Deal, UserDeal
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_
from werkzeug.utils import secure_filename
from geopy.distance import vincenty

deal_controller = Blueprint('deal_controller', __name__)

# Constant for file types allowed
ALLOWED_EXTENSIONS = set(['jpg', 'png'])

@deal_controller.route("/deals", methods=['GET'])
def getDeals():
    if not 'user_id' in session:
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    # Get all the args from request
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    user_id = request.args.get('user_id')

    if (latitude is None or longitude is None):
        return make_response(jsonify({
            'error' : 'Missing request parameters'
            }), 422)


    # This creates box around coordinates
    latitude = float(latitude)
    longitude = float(longitude)
    dist_range = (300 / 69.172)
    lat_lower_bound = latitude - dist_range
    lat_upper_bound = latitude + dist_range
    long_lower_bound = longitude - dist_range
    long_upper_bound = longitude + dist_range

    dbSession = dbGetSession()

    if user_id is None:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'User does not exist'
            }), 404)

    # Filters deals by location box we created
    deals = dbSession.query(Deal).filter(and_(Deal.latitude >= lat_lower_bound, Deal.latitude <= lat_upper_bound, Deal.longitude >= long_lower_bound, Deal.longitude <= long_upper_bound)).all()

    deals_serialized = []
    for deal in deals:
        current_deal = deal.serialize()

        # Check if user has been already used
        used_deal = dbSession.query(UserDeal).filter(and_(UserDeal.user_id == user_id, UserDeal.deal_id == deal.id)).one_or_none()
        if used_deal is None:
            current_deal["deal_used"] = False
        else:
            current_deal["deal_used"] = True

        deals_serialized.append(current_deal)

    dbSession.close()
    return make_response(jsonify({
        'deals' : deals_serialized
        }))

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
    if not 'user_id' in session:
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    user_id = request.args.get('user_id')
    deal_id = request.args.get('deal_id')
    user_latitude = request.args.get('user_latitude')
    user_longitude = request.args.get('user_longitude')

    dbSession = dbGetSession()

    # Make sure user exists
    if user_id is None:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'User does not exist'
            }), 404)

    # Make sure deal exists
    deal = dbSession.query(Deal).filter(Deal.id == deal_id).one_or_none()
    if deal is None:
        dbSession.close()
        return make_response(jsonify({
            'error' : "Deal does not exist"
            }))

    # Make sure they aren't trying to use the deal again
    deal_redeemed = dbSession.query(UserDeal, Deal).filter(and_(Deal.id == deal_id, UserDeal.deal_id == deal_id, UserDeal.user_id == user_id)).one_or_none()

    if deal_redeemed is not None:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'Deal has already been used'
            }), 403)

    deal_latitude = deal.latitude
    deal_longitude = deal.longitude
    user_coords = (user_latitude, user_longitude)
    deal_coords = (deal_latitude, deal_longitude)

    # Make sure user is within 500 feet of the deal
    distance = vincenty(user_coords, deal_coords).miles
    if distance >= 0.5:
        dbSession.close()
        return make_response(jsonify({
            'error' : 'User is too far from deal'
            }), 403)

    # Use deal
    newUse = UserDeal(user_id = user_id, deal_id = deal_id)
    dbSession.add(newUse)
    dbSession.commit()
    dbSession.close()

    return make_response(jsonify({
        'success' : 'Deal Used'
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
