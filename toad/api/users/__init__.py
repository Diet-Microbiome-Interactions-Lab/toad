'''
API for Fasta/FAA sequences
'''
from flask import Blueprint


from toad.api.lib.api_classes import DefaultAPI
from toad.api.lib.utilities import register_api
from toad.lib.models import User
from .. import _API_PATH_PREFIX


api_user = Blueprint('api_user', __name__,
                     url_prefix=_API_PATH_PREFIX + '/users')


register_api(api_user, DefaultAPI, User,
             'user_api', '/', pk='id')
