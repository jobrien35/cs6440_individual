from backported.api_responses import api_error_response, api_success_response, codes

from datetime import timedelta, date
from flask import request, send_file, safe_join
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from flask.views import MethodView
import requests
import json
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

    def post_new_data(self, fhir_file):
        #print(fhir_file.read())
        send = json.loads(fhir_file.read())
        resp = requests.post('https://r4.smarthealthit.org', json=send)
        #print(resp.json())
        #return resp.json()
        for entry in resp.json()['entry']:
            print(entry['response']['location'])
            if 'Patient' in entry['response']['location']:
                return entry['response']['location'].split('/')[1]

    def format_response(self, msg, pid, code=codes['SUCCESS']):
        args = {'pid': pid}
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
        if 'pid' not in data:
            return api_error_response('No pid provided')

        print('=' * 25)
        print('[I] Upload_FHIR_V1 -> post()')
        fhir_file = request.files['fd']
        name = fhir_file.filename.lower()
        pid = data['pid'][0]

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

        # uploaded and gui knows pid already
        if os.path.isfile(fileLocation) and pid != '...':
            resp = f'File already saved: {fileLocation} valid pid: {pid}'
            print(resp)
            return self.format_response(resp, pid)

        # no real pid from gui
        if pid == '...':
            print('Posting new r4 data to server to get pid')
            pid = self.post_new_data(fhir_file)

        # flask file method
        fhir_file.save(fileLocation)
        fhir_file.close()
        print('[I] fhir_file saved')
        print(f'[I]    fhir_file: {fhir_file}')
        print(f'[I]     filename: {filename}')
        print(f'[I] pid received: {pid}')
        print(f'[I] fileLocation: {fileLocation}')
        return self.format_response('Upload complete', pid, codes['CREATED'])


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
    "effectiveDateTime": "2020-03-07T20:53:14-05:00",
    "issued": "2020-03-07T20:53:14.197-05:00",
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
    "effectiveDateTime": "2020-03-07T20:53:14-05:00",
    "issued": "2020-03-07T20:53:14.197-05:00",
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


def populate_entry(entry, entry_uuid, entry_date, entry_value, pid):
    """
    take in a minimally populated fhir r4 observation dict and populate with any necessary values

    to be appended to bundle entry list afterwards

    """

    entry['fullUrl'] = entry_uuid.urn
    entry['resource']['id'] = str(entry_uuid)
    entry['resource']['subject']['reference'] = pid

    # match units for loinc code for potassium and sodium
    entry['resource']['valueQuantity']['value'] = entry_value/1000

    converted_date = entry_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    entry['resource']['effectiveDateTime'] = converted_date
    entry['resource']['issued'] = converted_date

    print('='*10 + ' entry ' + '='*10)
    print(entry)
    print('='*30)

    return entry



class Get_Mfp_V1(MethodView):

    def format_response(self, msg, bundle, pid, code=codes['SUCCESS']):
        args = {
            'pid': pid,
            'bundle': bundle
        }
        return api_success_response(msg, args, code)

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
        if 'pid' not in data:
            return api_error_response('No pid provided')

        username = data['u']
        password = data['p']
        start = data['start'][0]
        end = data['end'][0]
        pid = data['pid'][0]

        start_y, start_m, start_d = start.split('-')
        end_y, end_m, end_d = end.split('-')

        start_y = int(start_y)
        start_m = int(start_m)
        start_d = int(start_d)
        end_y = int(end_y)
        end_m = int(end_m)
        end_d = int(end_d)

        print(f"{start_y}-{start_m}-{start_d} {end_y}-{end_m}-{end_d}")
        print(f"pid: {pid}")

        client = myfitnesspal.Client(username, password=password)

        start_date = date(start_y, start_m, start_d)
        end_date = date(end_y, end_m, end_d)
        new_bundle = bundle
        for curr_date in daterange(start_date, end_date):
            print(curr_date)
            sodium_uuid = uuid.uuid4()
            potassium_uuid = uuid.uuid4()
            print(f"[I] sodium: {sodium_uuid} potassium: {potassium_uuid}")

            resp = client.get_date(curr_date).totals
            print(resp)

            bundle['entry'].append(populate_entry(sodium_entry, sodium_uuid, curr_date, resp['sodium'], pid))
            bundle['entry'].append(populate_entry(potassium_entry, potassium_uuid, curr_date, resp['potass.'], pid))
            #print(type(curr_date))

        #print(client.get_measurements())
        #print(dir(client))
        return self.format_response('mfp done', bundle, pid)
