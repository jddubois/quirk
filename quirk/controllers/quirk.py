import requests
from ..utils import dbGetSession
from ..models import Quirk, User, UserLike, Match, QuirkLike, Priority
from flask import Flask, Blueprint
from flask import current_app as app
from flask import render_template, jsonify, request, session, make_response
from sqlalchemy import and_, or_, func
from math import radians
from math import sin, acos, cos


quirk_controller = Blueprint('quirk_controller', __name__)

# Will remove from list if returns true
def shouldRemoveUser(user, loggedInUser, dbSession):
    # Remove if logged in user has liked user in question

    if dbSession.query(UserLike).filter(
        UserLike.liker_id == session['user_id'],
        UserLike.likee_id == user.id
    ).one_or_none() is not None:
        return True

    # Remove if not compatible wit gender / seeking
    if not user.isGenderCompatible(loggedInUser):
        print("Not gender compatible")
        print(user.name)
        return True

    # Remove if users are too far apart
    if user.getDistance(loggedInUser) > loggedInUser.radius:
        print("Distance too far")
        return True

    # Remove if user is themselves
    if user.id == loggedInUser.id:
        return True

    # Remove if logged in user has matched wih user in question
    if user.id < session['user_id']:
        if dbSession.query(Match).filter(
            Match.user_one_id == user.id,
            Match.user_two_id == session['user_id']
        ).one_or_none() is not None:
            return True
    elif dbSession.query(Match).filter(
        Match.user_one_id == session['user_id'],
        Match.user_two_id == user.id
    ).one_or_none() is not None:
        return True

    # Do not remove
    return False


def shouldRemoveQuirk(quirk, dbSession):
    if dbSession.query(QuirkLike).filter(
        QuirkLike.quirk_id == quirk.id,
        QuirkLike.liker_id == session['user_id']
    ).one_or_none() is not None:
        return True
    return False

def getUserQuirks(user, dbSession):
    quirks = dbSession.query(Quirk).filter(
        Quirk.user_id == user.id
    ).all()
    return [ q for q in quirks if not shouldRemoveQuirk(q, dbSession) ]


@quirk_controller.route("/quirk", methods=['GET'])
def getQuirks():

    # Check if logged in
    if not 'user_id' in session:
        return make_response(jsonify({
            'error' : 'user not logged in'
        }), 403)

    # Get location from parameters
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    # Check if location is valid
    if latitude is None or longitude is None:
        return make_response(jsonify({
            'error': 'Missing parameters'
        }), 400)

    # Define constants for calculations
    maxUsers = 20
    radius = 3959

    # Get user
    dbSession = dbGetSession()
    user = dbSession.query(User).filter(User.id == session['user_id']).one_or_none()
    print "original user"
    print user

    print(session['user_id'])
    # check if user is none
    if user is None:
        return make_response(jsonify({
            'error' : 'user does not exist'
        }), 404)

    # Set user location
    user.latitude = float(latitude)
    user.longitude = float(longitude)
    dbSession.commit()

    # Get Quirks by querying Quirk, QuirkLike, User, and Priority for best options
    priorityUsers = [priorityUser[0] for priorityUser in dbSession.query(User, Priority).filter(
    # Filter by user priority
        or_(
            Priority.user_one_id == session['user_id'],
            Priority.user_two_id == session['user_id']
        )
    # Filter out users not in range
    ).filter(
        User.age >= user.min_age,
        User.age <= user.max_age
    # Filter by gender and seeking settings
    ).order_by(Priority.priority).all()]

    print "got priority quirks"
    # Filter by not liked quirks
    # TODO Clear priority after match
    #priorityUsers = [ u for u in priorityUsers if not shouldRemoveUser(u, dbSession) ]

    totalUsers = 0
    filteredUsers = []
    for u in priorityUsers:
        if not shouldRemoveUser(u, user, dbSession):
            totalUsers += 1
            filteredUsers.append(u)
            if totalUsers == maxUsers:
                break

    print "filtered priority quirks and displaying..."
    print filteredUsers
    if totalUsers < maxUsers:
        # Need to query more
        # TODO ensure NONE of these quirks are priority so that there is no overlap between previous set
        # Get Quirks by querying Quirk, QuirkLike, User, and Priority for best options
        otherUsers = dbSession.query(User).filter(
            User.age >= user.min_age,
            User.age <= user.max_age
        ).all()

        #otherUsers = [ u for u in otherUsers if not shouldRemoveUser(u, dbSession) and u is not in priorityUsers ]
        if otherUsers is not None:
            for u in otherUsers:
                    if not shouldRemoveUser(u, user, dbSession):
                        totalUsers += 1
                        filteredUsers.append(u)
                        if totalUsers == maxUsers:
                            break

        # print regularQuirks
        # shuffle them up
        #otherUsers = [ (item[0].serialize(), item[1].serialize()) for item in filter ]
        print "PRINTING TOTAL USERS + PRIORITY USERS"
        print(filteredUsers)

    # Filter out the quirks
    quirks = []
    for u in filteredUsers:
        quirks.extend(getUserQuirks(u, dbSession))

    dbSession.commit()

    # If out here we can just return 100 priority quirks
    response = make_response(jsonify({
        'quirks' : [ q.serialize() for q in quirks ]
    }), 200)

    dbSession.close()

    return response;

# Updates a users quirk
# 1. Check if all parameters are passed
# 2. Check if used has permission to update that quirk
# 3. Update the quirk
@quirk_controller.route("/quirk/<id>", methods=['PUT'])
def updateQuirkRoute(id):
    mm_quirk = request.args.get("match_maker")
    quirk = None
    requestData = request.get_json()

    if requestData is None or requestData["quirk"] is None:
        return make_response(jsonify({
            'error': 'Missing parameters'
        }), 400)

    quirk = requestData["quirk"]
    dbSession = dbGetSession()

    quirk_entry = dbSession.query(Quirk).filter(Quirk.id == id).one_or_none()
    if not userHasPermission(quirk_entry.user_id):
        dbSession.close()
        return make_response(jsonify({
    'error': 'Access denied'
    }), 403)

    quirk_entry.quirk = quirk

    if mm_quirk is None:
        quirk_entry.match_maker = False

    quirk_entry.mm_quirk = mm_quirk

    dbSession.commit()

    response = make_response(jsonify(quirk_entry.serialize()), 200)

    dbSession.close()

    return response


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
    return newMatch

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

    # Check if logged in
    if not 'user_id' in session:
        return make_response(jsonify({
            'error' : 'user not logged in'
        }), 403)

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
    if not quirk.match_maker:
        print "not match maker quirk"
        alllikerQuirks = dbSession.query(QuirkLike).filter(and_(QuirkLike.liker_id == liker.id, QuirkLike.likee_id == likee.id)).all()

        # Liker does not like likee yet
        if len(alllikerQuirks) < 3:
            print "liker does not like likee yet"
            dbSession.close()
            return make_response(jsonify({
                'match': 'false'
                }), 200)

    # See if likee likes liker
    newUserLike = dbSession.query(UserLike).filter(and_(UserLike.liker_id == likee.id and UserLike.likee_id == liker.id)).one_or_none()

    # Likee does not like liker, liking is one way
    if newUserLike is None:
        print "likee does not like liker, liking is one way"

        # Add that liker like likee only
        userEntry = dbSession.query(UserLike).filter(UserLike.liker_id== liker.id, UserLike.likee_id== likee.id, UserLike.liked== True).one_or_none();

        if userEntry is None:
            dbSession.add(UserLike(liker_id= liker.id, likee_id= likee.id, liked= True))
            dbSession.commit()

        dbSession.close()

        return make_response(jsonify({
            'match': 'false'
            }), 200)

    # Both like each other, delete this entry UserLike
    dbSession.query(UserLike).filter(and_(UserLike.likee_id == likee.id and UserLike.liker_id == liker.id)).delete()

    # Delete priority
    if liker.id < likee.id:
        dbSession.query(Priority).filter(Priority.user_one_id == liker.id, Priority.user_two_id == likee.id).delete()
    else:
        dbSession.query(Priority).filter(Priority.user_one_id == likee.id, Priority.user_two_id == liker.id).delete()

    # Create a match bc liker and likee like each other
    match = createMatch(liker, likee, dbSession)

    dbSession.commit()

    print "match is made"

    response = make_response(jsonify({
        'match': 'true',
        'user': match.serialize(liker.id, dbSession)
    }), 200)

    dbSession.close()

    return response

def userHasPermission(user_id):
    if not 'user_id' in session:
        return False
    if session['user_id'] != user_id:
        return False
    return True
