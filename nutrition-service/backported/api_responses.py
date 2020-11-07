from flask import make_response
import json




"""

Standardized responses for all endpoints to communicate with the frontend
and return json with accompanying http code and data

"""




codes = {
    'SUCCESS'   : 200,
    'CREATED'   : 201,
    'ERROR'     : 400,
    'NOAUTH'    : 401,
    'NOPERMS'   : 403,
    'GONE'      : 410,
    'CRITERROR' : 500,
}




def api_error_response(message, errName, code):
    """
    take in message and http error code
    for frontend to have standardized responses
    https://github.com/thebigredgeek/apollo-errors

    RETURN appolo-error stylized json for frontend
    """
    err = {}
    err['data'] = {}
    err['errors'] = [{
        'message': message,
        'name': errName
    }]
    resp = make_response(json.dumps(err), code)
    resp.headers['Content-Type'] = 'application/json'
    return resp


def api_success_response(message, args={}, code=codes['SUCCESS']):
    """
    take in a success message to send to frontend to maintain appolo-error
    stylized responses and a variable amount of args for passing data between
    various endpoints as needed
    """
    win = {}
    win['message'] = message
    win.update(args)
    resp = make_response(json.dumps(win), code)
    resp.headers['Content-Type'] = 'application/json'
    return resp
