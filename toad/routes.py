from flask import Blueprint, request

from toad.api import _API_PATH_PREFIX
from toad.lib import Toad

main = Blueprint('main', __name__, url_prefix=_API_PATH_PREFIX + '/')


@main.route("/functions/test")
def test():
    comargs = ['show', 'fasta']
    qparams = request.args
    print(f'\nIn the test() function--> {qparams}')
    data = Toad(run_mode="gui", comargs=comargs,
                qparams=qparams, mode='quiet').report.formatted('json')
    return data
    # return {'Hi': 'How are you?', 'Good': 'How are you my friend?'}


@main.route("/functions/")
def test2():
    pass
