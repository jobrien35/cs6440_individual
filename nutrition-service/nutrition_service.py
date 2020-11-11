import os
from flask import Flask
from flask.views import MethodView
from backported.api_responses import api_success_response, api_error_response
from endpoints.version_1 import Upload_Image_V1, Download_Image_V1



UPLOAD_DIRECTORY = '/nutrition/uploads'
VERSION_1 = '/api/v1/nutrition'
NO_METHOD = 405




app = Flask(__name__)
app.debug = True  # restart server on edits
app.config['UPLOAD_DIRECTORY'] = UPLOAD_DIRECTORY


@app.errorhandler(NO_METHOD)
def unsupported_method(error):
    """
    globally catch invalid http methods used on any endpoint
    """
    return api_error_response('Endpoint does not support this method',
                              'UnsupportedMethodError', NO_METHOD)


class Static(MethodView):
    def get(self):
        return api_success_response("hello world")



app.add_url_rule(  # serve static js from here or static dir, or something with smart launcher
    '/',
    view_func=Static.as_view('root')
)  # GET

app.add_url_rule(  # nutrition posted here
    '{0}/upload'.format(VERSION_1),
    view_func=Upload_Image_V1.as_view('upload')
)  # POST


app.add_url_rule(  # get nutrition from fs
    '{0}/download'.format(VERSION_1),
    view_func=Download_Image_V1.as_view('download')
)  # GET




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT')))
