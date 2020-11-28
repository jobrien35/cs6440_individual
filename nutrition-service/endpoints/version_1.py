from backported.api_responses import api_error_response, api_success_response, codes

from datetime import timedelta, date
from flask import request, send_file, safe_join
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from flask.views import MethodView
import requests
import uuid
import os

import myfitnesspal




# removed leading slash for non-docker deployments "/n"
UPLOAD_DIRECTORY = "nutrition/uploads"
EXTENSIONS = set(['json'])


class Static(MethodView):
    @cross_origin()
    def get(self):
        return api_success_response("hello world")


class Upload_FHIR_V1(MethodView):

    def format_response(self, msg, token, code=codes['SUCCESS']):
        args = {'token': token}
        return api_success_response(msg, args, code)

    @cross_origin()
    def post(self):
        """

        Upload FHIR data to be posted to FHIR r4 test server

        Return patient id from r4 server so frontend can then get and parse observations from server

        Posted fd via form-data to be uploaded

        RETURNS location_img_name.extension or error response
        """

        data = request.form.to_dict(flat=False)        

        #print(request.get_json())

        #print('name: ' + request.form.name)
        if 'fd' not in request.files:
            return api_error_response('No fd provided')
        if request.files is None:
            return api_error_response('no file for parameter')

        print('=' * 25)
        print('[I] Upload_FHIR_V1 -> post()')
        fhir_file = request.files['fd']
        name = fhir_file.filename.lower()

        if name == '' or '.' not in name:
            return api_error_response('Invalid file name')

        name_parts, extension = name.split('.',  1)
        # synthea does first_last_uuid.json
        # first, last, uuid = name_parts.split('_', 2)
        # print(f'first: {first} last: {last} uuid: {uuid}')
        if not extension in EXTENSIONS:
            return api_error_response('Invalid file extension')

        filename = secure_filename(name)
        fileLocation = safe_join(UPLOAD_DIRECTORY, filename)

        if not os.path.isdir(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)

        if os.path.isfile(fileLocation):
            resp = f'File already saved {fileLocation}'
            print(resp)
            return self.format_response(resp, filename)

        # flask file method
        fhir_file.save(fileLocation)
        fhir_file.close()
        print('[I] fhir_file saved')
        print(f'[I]     fhir_file: {fhir_file}')
        print(f'[I]     filename: {filename}')
        print(f'[I] fileLocation: {fileLocation}')
        return self.format_response('Upload complete', filename, codes['CREATED'])


class Download_FHIR_V1(MethodView):
    @cross_origin()
    def get(self):
        """

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


def daterange(start_date, end_date):
    """ https://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python """
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

bundle = {
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": []
}

sodium_entry = {
  "fullUrl": "urn:uuid:uuid_here",
  "resource": {
    "resourceType": "Observation",
    "id": "uuid_here",
    "status": "final",
    "category": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": "laboratory",
            "display": "laboratory"
          }
        ]
      }
    ],
    "code": {
      "coding": [
        {
          "system": "http://loinc.org",
          "code": "81011-9",
          "display": "Sodium intake 24 hour Estimated"
        }
      ],
      "text": "Sodium intake 24 hour Estimated"
    },
    "subject": {
      "reference": "pid_here"
    },
    "valueQuantity": {
      "value": 0,
      "unit": "g",
      "system": "http://unitsofmeasure.org",
      "code": "g"
    }
  },
  "request": {
    "method": "POST",
    "url": "Observation"
  }
}

potassium_entry = {
      "fullUrl": "urn:uuid:a_uuid_here",
      "resource": {
        "resourceType": "Observation",
        "id": "a_uuid_here",
        "status": "final",
        "category": [
          {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
                "display": "laboratory"
              }
            ]
          }
        ],
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "81010-1",
              "display": "Potassium intake 24 hour Estimated"
            }
          ],
          "text": "Potassium intake 24 hour Estimated"
        },
        "subject": {
          "reference": "pid_here"
        },
        "valueQuantity": {
          "value": 0,
          "unit": "g",
          "system": "http://unitsofmeasure.org",
          "code": "g"
        }
      },
      "request": {
        "method": "POST",
        "url": "Observation"
      }
    }





class Get_Mfp_V1(MethodView):
    @cross_origin()
    def post(self):
        """
        u - username for vendor
        p - password for vendor
        start - start date or beginning date to request from vendor
        end - end date to stop requesting nutrition data from vendor
        pid - fhir patient id to add observations to

        returns list of entries to be graphed
        """

        data = request.form.to_dict(flat=False)

        if 'u' not in data:
            return api_error_response('No user provided')
        if 'p' not in data:
            return api_error_response('No pass provided')
        if 'start' not in data:
            return api_error_response('No start date provided')
        if 'end' not in data:
            return api_error_response('No end date provided')

        username = data['u']
        password = data['p']
        start = data['start'][0]
        end = data['end'][0]
        pid = None
        if 'pid' in data:
            # if pid provided, add to fhir server
            pid = data['pid']

        start_y, start_m, start_d = start.split('-')
        end_y, end_m, end_d = end.split('-')

        start_y = int(start_y)
        start_m = int(start_m)
        start_d = int(start_d)
        end_y = int(end_y)
        end_m = int(end_m)
        end_d = int(end_d)

        #print(start_y)
        #print(start_m)
        #print(start_d)

        client = myfitnesspal.Client(username, password=password)

        start_date = date(start_y, start_m, start_d)
        end_date = date(end_y, end_m, end_d)
        new_bundle = bundle
        for single_date in daterange(start_date, end_date):
            sodium_uuid = uuid.uuid4().urn
            potassium_uuid = uuid.uuid4().urn
            print(f"sodium: {sodium_uuid} potassium: {potassium_uuid}")

            print(single_date)
            print(type(single_date))

            day = client.get_date(single_date)
            print(day)
        #print(client.get_measurements())
        #print(dir(client))
        return api_success_response('mfp done')
