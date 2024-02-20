'''
API for Fasta/FAA sequences
'''
import json

from flask import Blueprint, request
from toad import bcrypt, mongo
from toad.api.lib.api_classes import DefaultAPI
from toad.api.lib.utilities import DaneJsonEncoder, register_api, user_for_id
from toad.lib.models import User, UserSession
from .. import _API_PATH_PREFIX


api_user = Blueprint('api_user', __name__,
                     url_prefix=_API_PATH_PREFIX + '/users')


register_api(api_user, DefaultAPI, User,
             'user_api', '/', pk='id')


def sessionid_for_user(user_dbeUUID: str, createSessionIfNone = False) -> str | None:
    session = mongo.db['UserSessions'].find_one({'user_dbeUUID': user_dbeUUID})
    if not session and createSessionIfNone:
        session = UserSession(user_dbeUUID=user_dbeUUID).to_bson()
        print(f'\nSession {session}\n')
        mongo.db['UserSessions'].insert_one(session)
    elif not session:
        return None
    
    return session['dbeUUID']


@api_user.route('/login-user/', methods=['POST'])
def login_user():
    email = request.form.get('email')
    password = request.form.get('password')
    
    print(f'[__init__.py]: {email=} {password=}')
    user = mongo.db.Users.find_one({'email': email})
    print(f'{user=}')
    if not user:
        return (json.dumps({"user": None, "validEmail": False, "validPassword": False}, cls=DaneJsonEncoder), 200, {'ContentType': 'application/json'})
    
    if not bcrypt.check_password_hash(user['password'], password):
        print(f'Passwords dont match up')
        return (json.dumps({"user": None, "validEmail": True, "validPassword": False}, cls=DaneJsonEncoder), 200, {'ContentType': 'application/json'})
    print(f'Passwords match up!!')


    # sessionID = sessionid_for_user(user['dbeUUID'], createSessionIfNone=True)
    sessionID = sessionid_for_user(user['dbeUUID'], createSessionIfNone=True)
    print(f'SessionID = {sessionID}')
    return (json.dumps({"user": user, "validEmail": True, "validPassword": True, 'sessionID': sessionID}, cls=DaneJsonEncoder), 200, {'ContentType': 'application/json'})

@api_user.route('/validate-user/<sessionid>', methods=['GET'])
def validated_user(sessionid):

    user = user_for_session(sessionid)
    if not user:
        return {'error': f'no user associated with session id: {sessionid}'}, 404, {'ContentType': 'application/json'}

    return user, 200, {'ContentType': 'application/json'}


def user_for_session(sessionID: str) -> dict | None:
    session = mongo.db['UserSessions'].find_one({'dbeUUID': sessionID})
    if not session:
        print(f'Warning: no session found with {sessionID}')
        return None
    user = user_for_id(session['user_dbeUUID'])
    # userdict = PublicUserInfo(**user.to_bson()).to_bson()
    userdict = user.to_bson()
    return userdict