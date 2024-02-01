'''
API for Fasta/FAA sequences
'''
from flask import Blueprint


from toad.api.lib.api_classes import DefaultAPI
from toad.api.lib.utilities import register_api
from toad.lib.models import Fasta
from .. import _API_PATH_PREFIX


api_amplicon = Blueprint('api_amplicons', __name__,
                         url_prefix=_API_PATH_PREFIX + '/amplicon')


register_api(api_amplicon, DefaultAPI, Fasta,
             'fasta_api', '/fastas/', pk='id')
# register_api(api_amplicon, DefaultAPI, Group,
#              'group_api', '/groups/', pk='id')
