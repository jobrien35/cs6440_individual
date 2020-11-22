from backported.api_responses import api_error_response, api_success_response, codes

from flask import request, send_file, safe_join
from werkzeug.utils import secure_filename
from flask.views import MethodView

import myfitnesspal

import uuid
import os

# remove leading slash for non-docker deployments
UPLOAD_DIRECTORY = "nutrition/uploads"
EXTENSIONS = set(['json'])


class Upload_FHIR_V1(MethodView):

    def format_response(self, msg, token, code=codes['SUCCESS']):
        args = {'token': token}
        return api_success_response(msg, args, code)

    def post(self):
        """

        Upload FHIR data to be posted to FHIR r4 test server
        Assuming frontend already parsed the observations beforehand and updated the graphs there

        Posted fd via form-data to be uploaded

        RETURNS location_img_name.extension or error response
        """

        data = request.form.to_dict(flat=False)

        if 'fd' not in request.files:
            return api_error_response('No fhir_file provided')
        if request.files is None:
            return api_error_response('no file for parameter')

        print('=' * 25)
        print('[I] Upload_FHIR_V1 -> post()')
        fhir_file = request.files['fd']
        name = fhir_file.filename.lower()

        if name == '' or '.' not in name:
            return api_error_response('Invalid file name')

        name_parts, extension = name.split('.',  1)
        first, last, uuid = name_parts.split('_', 2)
        print(f'first: {first} last: {last} uuid: {uuid}')
        if not extension in EXTENSIONS:
            return api_error_response('Invalid file extension')


        filename = secure_filename(name)
        fileLocation = safe_join(UPLOAD_DIRECTORY, filename)

        if not os.path.isdir(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)

        if os.path.isfile(fileLocation):
            return self.format_response(f'File already saved {fileLocation}', filename)

        # flask file method
        fhir_file.save(fileLocation)
        fhir_file.close()
        print('[I] fhir_file saved')
        print(f'[I]     fhir_file: {fhir_file}')
        print(f'[I]     filename: {filename}')
        print(f'[I] fileLocation: {fileLocation}')
        return self.format_response('Upload complete', filename, codes['CREATED'])


class Download_FHIR_V1(MethodView):
    def get(self):
        """

        Users can access with any ADMIN/ACTIVE permissions

        Authorization via query_parameter 'access_token' only

        Retrieves the requested fhir file by first_last_uuid.extension, same returned from
        the post request originally

        RETURNS the file requested or error response
        """

        if 'fd' not in request.args:
            return api_error_response('No data requested')
        if request.args.get('fd') == '':
            return api_error_response('Invalid file name')

        print('=' * 25)
        print('[I] Download_FHIR -> get()')
        name = request.args.get('fd')
        print(f'[I] file requested: {name}')
        imageName = secure_filename(name)
        location = name.split('_')[0]

        fileLocation = safe_join(UPLOAD_DIRECTORY, imageName)
        print(f'[I]     filename: {imageName}')
        print(f'[I] fileLocation: {fileLocation}')
        if os.path.isfile(fileLocation):
            mimetype = 'image/' + imageName.split('.', 1)[1].lower()
            return send_file(safe_join(UPLOAD_DIRECTORY, imageName), mimetype=mimetype)
        else:
            return api_error_response('No file found', 'InternalServerError', codes['CRITERROR'])


class Get_Mfp_V1(MethodView):
    def get(self):

        client = myfitnesspal.Client('jobrien35', password='Pinto43212020gt')

        day = client.get_date(2013, 3, 2)
        print(day)
        return api_success_response(day.meals)
