"""
run the service with "heroku local" for dev from repo root dir
"""

import os
from flask_cors import CORS
from flask import Flask
from flask.views import MethodView
from backported.api_responses import api_success_response, api_error_response, codes
from endpoints.version_1 import Static, Upload_FHIR_V1, Download_FHIR_V1, Get_Mfp_V1, Post_New_FHIR_R4_Observation


UPLOAD_DIRECTORY = 'nutrition/uploads'
VERSION_1 = '/api/v1/nutrition'


app = Flask(__name__)
app.debug = True  # restart server on edits
app.config['UPLOAD_DIRECTORY'] = UPLOAD_DIRECTORY


@app.errorhandler(codes['NOMETHOD'])
def unsupported_method(error):
    """
    globally catch invalid http methods used on any endpoint
    """
    return api_error_response('Endpoint does not support this method',
                              errName='UnsupportedMethodError', code=codes['NOMETHOD'])


app.add_url_rule(  # serve static js from here or static dir, or something with smart launcher
    '/',
    view_func=Static.as_view('root')
)  # GET


app.add_url_rule(  # base r4 patient bundle posted here
    f'{VERSION_1}/upload',
    view_func=Upload_FHIR_V1.as_view('upload')
)  # POST


app.add_url_rule(  # get nutrition from fs
    f'{VERSION_1}/download'.format(),
    view_func=Download_FHIR_V1.as_view('download')
)  # GET

app.add_url_rule(  # get nutrition from myfitnesspal
    f'{VERSION_1}/mfp',
    view_func=Get_Mfp_V1.as_view('mfp')
)  # POST

app.add_url_rule(  # post new observations to be uploaded to r4 server
    f'{VERSION_1}/observation',
    view_func=Post_New_FHIR_R4_Observation.as_view('observation')
)  # POST



if __name__ == "__main__":
    CORS(app.run(host='0.0.0.0', port=int(os.environ.get('PORT'))))
