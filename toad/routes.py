import json

from flask import Blueprint, request

from toad.api import _API_PATH_PREFIX
from toad.lib import Toad

main = Blueprint('main', __name__, url_prefix=_API_PATH_PREFIX + '/')


@main.route("/functions/test")
def test():
    print(f'Calling this route...')
    print(f'Request headers:\n{request.headers}\n\n')
    comargs = ['show', 'fasta']
    qparams = request.args
    print(f'This is the test function. What we need to do here is feed it the language expected')
    print(f'\nIn the test() function--> {qparams}')
    data = Toad(run_mode="gui", comargs=comargs,
                qparams=qparams, mode='debug').report.formatted('json')
    print(f'Returning data: {data}')
    return data
    # return {'Hi': 'How are you?', 'Good': 'How are you my friend?'}


@main.route("/functions/test2", methods=['GET', 'POST', 'PUT'])
def test2():
    project = request.form['project']
    lab = request.form['lab']
    user_id = request.form['userID']
    uploaded_files = request.files.getlist('files[]')
    print(f'User = {user_id}, Project = {project}, Lab = {lab}, UploadedFiles = {uploaded_files}')
    for file in uploaded_files:
        print(f'Found file: {file.filename}')
    comargs = ['ingest', 'contigs', 'scan:', 'mylocation', 'files', uploaded_files]
    return_data = Toad(run_mode="gui", comargs=comargs,
                       qparams=request.args, mode='debug', user_id=user_id).report.formatted('json')
    print(f'Returning data: {return_data}')
        # if file and file.filename:
        #     lines = file.readlines()
        #     print(f'Lines of {file.filename}:\n{lines}\n\n')
    return (json.dumps({"Status": "Successfully Updated User"}), 200, {'ContentType': 'application/json'})