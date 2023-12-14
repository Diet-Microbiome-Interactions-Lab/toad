from flask import Blueprint

from toad.lib import Toad

main = Blueprint('main', __name__)


@main.route("/functions/test")
def test():
    comargs = ['show', 'fasta']
    data = Toad(run_mode="gui", comargs=comargs).report.formatted('json')
    return data
    # return {'Hi': 'How are you?', 'Good': 'How are you my friend?'}
