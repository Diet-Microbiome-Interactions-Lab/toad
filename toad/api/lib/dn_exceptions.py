'''
Special exception handling.
'''
import http

import werkzeug


class DBInsertException(werkzeug.exceptions.HTTPException):
    code = http.HTTPStatus.CONFLICT
    description = 'Issue inserting into database'


class RequestValidationException(werkzeug.exceptions.HTTPException):
    code = http.HTTPStatus.UNPROCESSABLE_ENTITY
    description = 'Request body not valid for model'
