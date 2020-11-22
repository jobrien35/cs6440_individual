from flask import make_response
import json


"""
Standardized responses for all endpoints to communicate with the frontend
and return json with accompanying http code and data
"""


codes = {
    'SUCCESS'   : 200,
    'CREATED'   : 201,
    'ERROR'     : 422,
    'NOAUTH'    : 401,
    'NOPERMS'   : 403,
    'NOMETHOD'  : 405,
    'GONE'      : 410,
    'CRITERROR' : 500,
}


def format_response(res, code):
    resp = make_response(json.dumps(res), code)
    resp.headers['Content-Type'] = 'application/json'
    return resp


def api_error_response(message, errName='ValidationError', code=codes['ERROR']):
    """
    take in message and http error code
    for frontend to have standardized responses
    https://github.com/thebigredgeek/apollo-errors

    Only errors have empty data field, success is just message and code

    RETURN appolo-error stylized json for frontend
    """
    err = {}
    err['data'] = {}
    err['errors'] = [{
        'message': message,
        'name': errName
    }]
    return format_response(err, code)


def api_success_response(message, args={}, code=codes['SUCCESS']):
    """
    take in a success message to send to frontend to maintain appolo-error
    stylized responses and a variable amount of args for passing data between
    various endpoints as needed
    """
    win = {}
    win['message'] = message
    win.update(args)
    return format_response(win, code)
