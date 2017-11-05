from ..utils import dbGetSession
from ..models import Business, Deal
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_
import bcrypt

business_controller = Blueprint('business_controller', __name__, template_folder='templates')

@business_controller.route("/business", methods=['POST'])
def registerBusiness():
    business_name = request.form['business_name']
    email = request.form['email']
    password = request.form['password']

    if business_name is None or email is None or password is None:
        return make_response(jsonify({
                'failure' : 'Missing parameters'
            }))

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Check if this email already has an account
    dbSession = dbGetSession()
    businessEmail = dbSession.query(Business).filter(Business.email == email).one_or_none()
    if businessEmail is not None:
        dbSession.close()
        return make_response(jsonify({
                'failure' : 'Email Already In Use'
            }))

    new_business = Business(email = email, password = hashed, business_name = business_name)
    dbSession.add(new_business)
    dbSession.commit()

    return make_response(jsonify({
            'success' : 'Registered'
        }))

@business_controller.route("/business/<id>", methods=['GET'])
def businessHomepage(id):
    if session.get('business_id') is None:
        return make_response(jsonify({
                'Failure' : 'You are not logged in'
            }))

    # Check if current user can look at business
    id = int(id)
    if session['business_id'] is not int(id):
        return make_response(jsonify({
                'Failure' : 'You do not have permission to view that page'
            }))

    # Check business exists
    dbSession = dbGetSession()
    business = dbSession.query(Business).filter(Business.id == id).one_or_none()
    if business is None:
        return make_response(jsonify({
                'Failure' : 'Business ID does not exist'
            }))

    # Retrieve all deals for a business
    deals = dbSession.query(Deal).filter(Deal.business_id == id).all()

    business_deals = []
    for deal in deals:
        business_deals.append(deal.serialize())

    return_obj = {
        'business' : business.serialize(),
        'deals': business_deals
    }
    return make_response(jsonify(return_obj))

@business_controller.route("/business_login", methods=['GET', 'POST'])
def loginBusiness():
    if request.method == 'GET':
        return render_template('business_login.html')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email is None or password is None:
            return make_response(jsonify({
                    'failure' : 'Missing parameters'
                }))

        dbSession = dbGetSession()
        business = dbSession.query(Business).filter(Business.email == email).one_or_none()
        dbSession.close()
        if business is None:
            return make_response(jsonify({
                    'failure' : 'Email does not exist'
                }))

        stored_hash = business.password.encode('utf-8')

        if bcrypt.hashpw(password.encode('utf-8'), stored_hash) == stored_hash:
            session['business_id'] = business.id
            return make_response(jsonify({
                    'Success' : 'Logged in'
                }))
        else:
            return make_response(jsonify({
                    'Failure' : 'Wrong password'
                }))

    return make_response(jsonify({
            'success' : 'Logged In!'
        }))
