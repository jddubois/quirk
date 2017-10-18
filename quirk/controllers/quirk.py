import requests
from ..utils import dbGetSession
from ..models import Quirk, User, UserLike, Match, QuirkLike, Priority
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_
from math import sin, cos, sqrt, radians

quirk_controller = Blueprint('quirk_controller', __name__)

# Updates a users quirk
# 1. Check if all parameters are passed
# 2. Check if used has permission to update that quirk
# 3. Update the quirk
@quirk_controller.route("/quirk", methods=['GET'])
def getQuirks():

    if not 'user_id' in session:
        return make_response(jsonify({
            'error' : 'user not logged in'
        }), 403)

    # TODO Return error if no location found
    # TODO store new location in database
    latitude = radians(request.args.get("latitude"))
    longitude = radians(request.args.get("longitude"))
    radius = 3959 # miles
    maxQuirks = 100


    dbSession = dbGetSession()
    user = dbSession.query(User).filter(User.user_id == session['user_id']).one_or_none()

    # check if user is none
    if user is None:
        return make_response(jsonify({
            'error' : 'user does not exist'
        }), 404)

    # Get Quirks by querying Quirk, QuirkLike, User, and Priority for best options
    priorityQuirks = dbSession.query(Priority, User, QuirkLike, Quirk).filter(
    # Filter by user priority
        or_(
            Priority.user_one_id == session['user_id'],
            Priority.user_two_id == session['user_id']
        )
    # Filter out users not in range
    ).filter(
            acos(sin(latitude) * sin(User.latitude) + cos(latitude) * cos(User.latitude) * cos(User.longitude - (longitude))) * radius <= user.radius
    # Filter out unliked quirks
    ).filter(
        QuirkLike.liker_id != session['user_id']
    ).order_by(Priority.priority).limit(maxQuirks)
    # TODO: Filter by gender and seeking settings
    #filter().\
    # TODO: Filter by age and age range
    #filter().\

    print priorityQuirks

    if len(priorityQuirks) < maxQuirks:
        # Need to query more
        # TODO ensure NONE of these quirks are priority so that there is no overlap between previous set
        regularQuirks = dbSession.query(User, QuirkLike, Quirk).filter(and_(acos(sin(latitude) * sin(User.latitude) + cos(latitude) * cos(User.latitude) * cos(User.longitude - (longitude))) * radius <= user.radius, QuirkLike.liker_id != session['user_id'])).limit(100 - priorityQuirks.count())
        # print regularQuirks
        # shuffle them up
        return make_response(({
        'priorities' : jsonify(priorityQuirks),
        'regular' : jsonify(regularQuirks)
        }), 200)

    # If out here we can just return 100 priority quirks
    return make_response(jsonify({
    'priorities' : jsonify(priorityQuirks),
    'other': ''
    }), 200)

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


def fetchPriority(liker, likee, dbSession):
    if liker.id < likee.id:
        priority = dbSession.query(Priority).filter(Priority.user_one_id == liker.id, Priority.user_two_id == likee.id).one_or_none()
    else:
        priority = dbSession.query(Priority).filter(Priority.user_one_id == likee.id, Priority.user_two_id == liker.id).one_or_none()

    return priority

def userExists(userId, dbSession):
    curr_user = dbSession.query(User).filter(User.id == userId).one_or_none()
    if curr_user is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'User not found'
        }), 404)

    return curr_user

def createMatch(liker, likee, dbSession):
    # Create a match bc liker and likee like each other
    if(liker.id < likee.id):
        print "liker < likee"
        newMatch = Match(user_one_id = liker.id, user_two_id = likee.id)

    elif(likee.id < liker.id):
        print "likee < liker"
        newMatch = Match(user_one_id = likee.id, user_two_id = liker.id)

    dbSession.add(newMatch)
    dbSession.commit()

### Endpoint for telling whether there is a like or not
### Returns whether or not you matched with person
### Creates entry in the match table
@quirk_controller.route("/quirk_like", methods=['POST'])
def addLikeRoute():
    likerId = request.args.get("liker_id")
    likeeId = request.args.get("likee_id")
    quirkId = request.args.get("quirk_id")
    liked = request.args.get("liked") == "true"

    # Checks if liker, likee, quirk exists
    dbSession = dbGetSession()

    # TODO: check if liker is logged in via facebook
    liker = userExists(likerId, dbSession)
    likee = userExists(likeeId, dbSession)

    # Check if quirk exists
    quirk = dbSession.query(Quirk).filter(Quirk.id == quirkId).one_or_none()
    if quirk is None:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Quirk not found'
            }), 404)

    # Quirk checks: make sure likee doesn't like their own quirk
    if liker == likee:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Liker and likee cannot be the same user'
        }), 403)

    # Quirk checks: make sure likee owns that quirk
    if quirk.user_id != likee.id:
        dbSession.close()
        return make_response(jsonify({
            'error': 'Likee does not own quirk'
            }), 403)

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

    # Determine if there is already a priority between them and fetch it
    priority = fetchPriority(liker, likee, dbSession)

    # The liker liked the likee
    if liked:

        # Add liked quirk to the QuirkLikes table
        likedQuirk = QuirkLike(likee_id= likee.id, quirk_id= quirk.id, liker_id= liker.id, liked= True)
        dbSession.add(likedQuirk)

        # Create a priority
        if priority is None:

            if liker.id < likee.id:
                priority = Priority(user_one_id = liker.id, user_two_id= likee.id, priority= 1)
            else:
                priority = Priority(user_one_id = likee.id, user_two_id= liker.id, priority= 1)

            dbSession.add(priority)

        # Update (++) the existing priority
        else:

            priority.priority = priority.priority + 1

        dbSession.commit()

    # The liker disliked the likee
    else:

        # Add disliked quirk to the QuirkLikes table
        likedQuirk = QuirkLike(likee_id= likee.id, quirk_id= quirk.id, liker_id= liker.id, liked= False)
        dbSession.add(likedQuirk)

        if priority is not None:

            # Delete a priority if under 1
            if priority.priority == 1:

                if liker.id < likee.id:
                    dbSession.query(Priority).filter(Priority.user_one_id == liker.id, Priority.user_two_id == likee.id).delete()
                else:
                    dbSession.query(Priority).filter(Priority.user_one_id == likee.id, Priority.user_two_id == liker.id).delete()

            # Update (--) the exisiting priority
            elif priority.priority > 1:

                priority.priority = priority.priority - 1;

        dbSession.commit()
        dbSession.close()
        return make_response(jsonify({
            'match': 'false'
            }), 200)

    # See if liker likes likee
    alllikerQuirks = dbSession.query(QuirkLike).filter(and_(QuirkLike.liker_id == liker.id, QuirkLike.likee_id == likee.id)).all()

    # Liker does not like likee yet
    if len(alllikerQuirks) < 3:

        dbSession.close()
        return make_response(jsonify({
            'match': 'false'
            }), 200)

    # See if likee likes liker
    newUserLike = dbSession.query(UserLike).filter(and_(UserLike.liker_id == likee.id and UserLike.likee_id == liker.id)).one_or_none()

    # Likee does not like liker, liking is one way
    if newUserLike is None:

        # Add that liker like likee only
        dbSession.add(UserLike(liker_id= liker.id, likee_id= likee.id, liked= True))
        dbSession.commit()
        dbSession.close()

        return make_response(jsonify({
            'match': 'false'
            }), 200)

    # Both like each other, delete this entry UserLike
    dbSession.query(UserLike).filter(and_(UserLike.likee_id == likee.id and UserLike.liker_id == liker.id)).delete()

    # Create a match bc liker and likee like each other
    createMatch(liker, likee, dbSession)

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
