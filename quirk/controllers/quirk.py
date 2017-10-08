import requests
from ..utils import dbGetSession
from ..models import Quirk, User, UserLike, Match, QuirkLike
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_

quirk_controller = Blueprint('quirk_controller', __name__)

# Updates a users quirk
# 1. Check if all parameters are passed
# 2. Check if used has permission to update that quirk
# 3. Update the quirk
@quirk_controller.route("/quirk_update", methods=['PUT'])
def updateQuirkRoute():
    id = request.args.get("id")
    user_id = request.args.get("user_id")
    quirk = request.args.get("quirk")

    # Check if parameters are passed in
    if (id is None or user_id is None or quirk is None):
        return make_response(jsonify({
            'error': 'Missing parameters'
        }), 400)

    print "Checked parameters"

    # Check user permission
    dbSession = dbGetSession()
    if not userHasPermission(user_id, id, dbSession):
        dbSession.close()
        return make_response(jsonify({
            'error': 'Access denied'
        }), 403)

    print "Checked user permission"

    quirk_entry = dbSession.query(Quirk).filter(Quirk.id == quirk_id).one_or_none()
    quirk_entry.quirk = quirk
    dbSession.commit()
    dbSession.close()

    return make_response(jsonify({
            'id': id,
            'user_id': user_id,
            'quirk': quirk 
        }), 200)

### Endpoint for telling whether there is a like or not
### Returns whether or not you matched with person
### Creates entry in the match table
@quirk_controller.route("/quirk_like", methods=['POST'])
def addLikeRoute():
    likerId = request.args.get("liker_id")
    likeeId = request.args.get("likee_id")
    quirkId = request.args.get("quirk_id")

    # Checks if liker, likee, quirk exists
    dbSession = dbGetSession()

    # TODO: check if liker  is logged in via facebook
    liker = dbSession.query(User).filter(User.id == likerId).one_or_none()
    if liker is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'User not found'
        }), 404)
    likee = dbSession.query(User).filter(User.id == likeeId).one_or_none()
    if likee is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'User not found'
            }), 404)
    quirk = dbSession.query(Quirk).filter(Quirk.id == quirkId).one_or_none()
    if quirk is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Quirk not found'
            }), 404)

    print "Checked permissions done"

    # Quirk checks: make sure likee doesn't like their own quirk
    if liker == likee:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Liker and likee cannot be the same user'
        }), 403)

    print "Quirk check #1 done"

    # Quirk checks: make sure likee owns that quirk
    print quirk.user_id
    print likee.id
    if quirk.user_id != likee.id:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Likee does not own quirk'
            }), 403)

    print "Quirk check #2 done"


    # This is how the rest of this code pans out:
    # 1. First we add any liked quirks to the QuirkLike table
    # 2. Then, since we added a liked quirk to the QuirkLike table, this might be the 3rd liked quirk.
    #    Because of this, we need to check if it's the 3rd liked quirk bc then the liker "likes" the likee.
    #    If there is < 3 liked quirks, we close the session. No matches or likes need to be added.
    # 3. If we have >= 3 liked quirks, we check to see if the likee already likes the liker.
    #    We do this first so we don't have to add a UserLike(liker, likee) and then delete it later to create a match.
    # 4. If the likee does not like the liker, the liker still has >= liked quirks at this point,
    #    So, we add the UserLike(liker, likee) to the UserLike table.
    # 5. If the likee likes the liker, both the liker and the likee like each other.
    #    Delete the UserLike entry, we don't need this anymore.
    # 6. Create a match. 

    # Add liked quirk to the QuirkLikes table
    likedQuirk = QuirkLike(likee_id= likee.id, quirk_id= quirk.id, liker_id= liker.id, liked= True)
    dbSession.add(likedQuirk)
    dbSession.commit()

    print "Added liked quirk to QuirkLike table"

    # See if liker likes likee
    alllikerQuirks = dbSession.query(QuirkLike).filter(and_(QuirkLike.liker_id == liker.id, QuirkLike.likee_id == likee.id)).all()

    if len(alllikerQuirks) < 3:
        dbSession.close()
        print "liker doesn't have 3 likes for likee"
        return make_response(jsonify({
            'match': 'false'
            }), 200)

    print "Liker likes likee"

    # See if likee likes liker before we add to UserLike table (don't want to have to add and delete later)
    newUserLike = dbSession.query(UserLike).filter(and_(UserLike.liker_id == likee.id and UserLike.likee_id == liker.id)).one_or_none()
    print newUserLike
    if newUserLike is None:
        dbSession.add(UserLike(liker_id= liker.id, likee_id= likee.id, liked= True))
        dbSession.commit()
        dbSession.close()
        print "likee doesn't like liker"
        # Liker likes likee, so add this entry to the UserLike table
        return make_response(jsonify({
            'match': 'false'
            }), 200)

    print "Likee likes liker"

    # Users like each other, delete this entry from table and add to match
    dbSession.query(UserLike).filter(and_(UserLike.likee_id == likee.id and UserLike.liker_id == liker.id)).delete()

    print "Deleted entry from UserLike table"

    # Create a match bc liker and likee like each other
    if(liker.id < likee.id):
        print "liker < likee"
        newMatch = Match(user_one_id = liker.id, user_two_id = likee.id)
        dbSession.add(newMatch)
        dbSession.commit()

    elif(likee.id < liker.id):
        print "likee < liker"
        newMatch = Match(user_one_id = likee.id, user_two_id = liker.id)
        dbSession.add(newMatch)
        dbSession.commit()

    print "Created match"

    return make_response(jsonify({
        'match': 'true'
    }), 200)

def userHasPermission(user_id, quirk_id, dbSession):
    if not 'user_id' in session:
        return False

    if session['user_id'] != user_id:
        return False

    quirk = dbSession.query(Quirk).filter(Quirk.id == quirk_id).one_or_none()

    if quirk is None:
        return False

    if quirk.user_id == user_id:
        return True