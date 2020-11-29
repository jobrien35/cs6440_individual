from backported.api_responses import api_error_response, api_success_response, codes

from datetime import timedelta, date
from flask import request, send_file, safe_join
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from flask.views import MethodView
import requests
import json
import uuid
import copy
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
            print(f'[I] upload made {UPLOAD_DIRECTORY}')

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

        if 'pid' not in request.args:
            return api_error_response('No data requested')
        if request.args.get('pid') == '':
            return api_error_response('Invalid file name')
        pid = request.args.get('pid')
        if pid == '...':
            return api_error_response('Invalid pid value')
        fhir_data = requests.get(f'https://r4.smarthealthit.org/Observation?patient={pid}').json()

        print('=' * 25)
        print('[I] Download_FHIR -> get()')
        print(f'[I] patient requested: {pid}')
        full = pid + '.json'
        fname = secure_filename(full)

        if not os.path.isdir(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)
            print(f'[I] download made {UPLOAD_DIRECTORY}')
        
        fileLocation = safe_join(UPLOAD_DIRECTORY, fname)
        with open(fileLocation, 'w') as f:
            json.dump(fhir_data, f)
            print('[I] created ' + os.path.abspath(fileLocation))
        print(f'[I]     filename: {fname}')
        print(f'[I] fileLocation: {fileLocation}')
        if os.path.isfile(fileLocation):
            print('[I] found ' + os.path.abspath(fileLocation))
            return send_file(f'../{fileLocation}', as_attachment=True, mimetype='application/fhir+json')
        else:
            return api_error_response('No file found', 'InternalServerError', codes['CRITERROR'])




bundle = {
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": []
}

bp_entry = {
      "fullUrl": "urn:uuid:some_uuid_here",
      "resource": {
        "resourceType": "Observation",
        "id": "some_uuid_here",
        "status": "final",
        "category": [
          {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "vital-signs"
              }
            ]
          }
        ],
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "85354-9",
              "display": "Blood Pressure"
            }
          ],
          "text": "Blood Pressure"
        },
        "subject": {
          "reference": "urn:uuid:pid_here"
        },
        "effectiveDateTime": "2020-03-07T20:22:14-04:00",
        "issued": "2020-03-107T20:22:14.197-04:00",
        "component": [
          {
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "8462-4",
                  "display": "Diastolic Blood Pressure"
                }
              ],
              "text": "Diastolic Blood Pressure"
            },
            "valueQuantity": {
              "value": 0,
              "unit": "mm[Hg]",
              "system": "http://unitsofmeasure.org",
              "code": "mm[Hg]"
            }
          },
          {
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "8480-6",
                  "display": "Systolic Blood Pressure"
                }
              ],
              "text": "Systolic Blood Pressure"
            },
            "valueQuantity": {
              "value": 0,
              "unit": "mm[Hg]",
              "system": "http://unitsofmeasure.org",
              "code": "mm[Hg]"
            }
          }
        ]
      },
      "request": {
        "method": "POST",
        "url": "Observation"
      }
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


def populate_entry(entry, entry_date, entry_value, pid):
    """
    take in a minimally populated fhir r4 observation dict and populate with any necessary values

    to be appended to bundle entry list afterwards

    assume date properly formatted before calling

    """
    entry_uuid = uuid.uuid1()
    entry['fullUrl'] = entry_uuid.urn
    entry['resource']['id'] = str(entry_uuid)
    # need to specify 'Patient/x' as resource needs to exist, or use uuid contained in transaction
    entry['resource']['subject']['reference'] = f'Patient/{pid}'

    # match units for loinc code for potassium and sodium
    # TODO: can move loic code math out to make code more general
    entry['resource']['valueQuantity']['value'] = entry_value/1000

    entry['resource']['effectiveDateTime'] = entry_date
    entry['resource']['issued'] = entry_date
    print(f'uuid {entry["resource"]["id"]}')
    return entry

def populate_bp(entry, entry_date, pid, systolic_value, diastolic_value):
    """
    take in a minimally populated fhir r4 observation dict and populate bp hardcoded components
    """
    entry_uuid = uuid.uuid1()
    entry['fullUrl'] = entry_uuid.urn
    entry['resource']['id'] = str(entry_uuid)
    # need to specify 'Patient/x' as resource needs to exist, or use uuid contained in transaction
    entry['resource']['subject']['reference'] = f'Patient/{pid}'

    # hard code this ordering to match hardcoded in-line sample
    entry['resource']['component'][0]['valueQuantity']['value'] = diastolic_value
    entry['resource']['component'][1]['valueQuantity']['value'] = systolic_value

    entry['resource']['effectiveDateTime'] = entry_date
    entry['resource']['issued'] = entry_date
    print(f'uuid {entry["resource"]["id"]}')
    return entry

def post_fhir_r4_bundle(bundle_dict):
    """
    more generic than the upload fhir file method because we're using it twice and code should
    work fine for both routes

    returns bundle id or None
    """
    send = json.dumps(bundle_dict)
    resp = requests.post('https://r4.smarthealthit.org', json=bundle_dict)

    print(resp.status_code)
    js = resp.json()
    if resp.status_code in [200, 201]:
        print(js['id'])
        return js['id']
    return None


def format_bundle_response(msg, bundle, bundle_id, pid, code=codes['SUCCESS']):
    args = {
        'pid': pid,
        'bundle_id': bundle_id,
        'bundle': bundle
    }
    return api_success_response(msg, args, code)


def daterange(start_date, end_date):
    """ https://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python """
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


class Get_Mfp_V1(MethodView):
    @cross_origin()
    def post(self):
        """
        u - username for vendor
        p - password for vendor
        start - start date or beginning date to request from vendor
        end - end date to stop requesting nutrition data from vendor
        pid - fhir patient id to add observations to

        returns bundle already post'ed to r4 server
        returns bundle id
        returns patient id
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
        # instantiate a new bundle, don't append to the singleton
        new_bundle = {}
        new_bundle.update(bundle)
        bundle_length = len(new_bundle["entry"])
        print(f'[I] initial mfp bundle size {bundle_length}')
        if bundle_length > 0:
            print('[I] resetting mfp bundle entry')
            new_bundle['entry'] = []

        print(f'[I] second mfp bundle size {len(new_bundle["entry"])}')

        for curr_date in daterange(start_date, end_date):
            print(curr_date)

            resp = client.get_date(curr_date).totals
            sod = {}
            sod = copy.deepcopy(sodium_entry)
            pot = {}
            pot = copy.deepcopy(potassium_entry)
            converted_date = curr_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            updated_sod_entry = populate_entry(sod, converted_date, resp['sodium'], pid)
            updated_pot_entry = populate_entry(pot, converted_date, resp['potass.'], pid)
            new_sod = updated_sod_entry['resource']['valueQuantity']['value']
            new_pot = updated_pot_entry['resource']['valueQuantity']['value']
            print(f'date: {converted_date} values: resp sod: {resp["sodium"]} -> {new_sod} | resp pot: {resp["potass."]} -> {new_pot}')
            new_bundle['entry'].append(updated_sod_entry)
            new_bundle['entry'].append(updated_pot_entry)
        print(f'posting mfp bundle len {len(new_bundle["entry"])} to r4 server')
        bundle_id = post_fhir_r4_bundle(new_bundle)

        return format_bundle_response('mfp done', new_bundle, bundle_id, pid)


class Post_New_FHIR_R4_Observation(MethodView):
    """
    post desired observation type with related values to be persisted in fhir r4 server so download
    can get latest observation set.

    assume frontend updates gui separately and fhir requests only needed for upload/download workflows
    since these observations are newer in time than the ones already stored, as previous requests
    would have already received the latest of everything else
    """
    SUPPORTED_OBSERVATIONS = ['sod', 'pot', 'bp']
    @cross_origin()
    def post(self):

        data = request.form.to_dict(flat=False)
        if 'pid' not in data:
            return api_error_response('No pid provided')
        if 'date' not in data:
            return api_error_response('No date provided')
        if 'val' not in data:
            return api_error_response('No value provided')
        if 'type' not in data:
            return api_error_response('No observation type provided')
        typ = data['type'][0]
        if typ not in self.SUPPORTED_OBSERVATIONS:
            return api_error_response(f'Unsupported observation type {typ}')
        if typ == 'bp' and 'val2' not in data:
            return api_error_response('BP 1/2 provided')

        pid = data['pid'][0]
        date = data['date'][0]
        # systolic
        val = data['val'][0]

        val2 = None

        desired_entry = None
        # instantiate a new object, don't append to the singleton
        new_bundle = {}
        new_bundle.update(bundle)
        bundle_length = len(new_bundle["entry"])
        print(f'[I] initial bundle size {bundle_length}')
        if bundle_length > 0:
            print('[I] resetting bundle entry')
            new_bundle['entry'] = []

        print(f'[I] second bundle size {len(new_bundle["entry"])}')
        new_entry = {}

        if typ == 'bp':
            # diastolic
            val2 = data['val2'][0]
            desired_entry = bp_entry
        elif typ == 'sod':
            desired_entry = sodium_entry
        elif typ == 'pot':
            desired_entry = potassium_entry

        print(f'[I] pid: {pid} val: {val} type: {typ} val2: {val2}')

        new_entry.update(desired_entry)

        if typ == 'bp':
            new_entry = populate_bp(new_entry, date, pid, int(val), int(val2))
        elif typ in ['sod', 'pot']:
            new_entry = populate_entry(new_entry, date, float(val), pid)

        new_bundle['entry'].append(new_entry)
        
        print(f'[I] Post new bundle length {len(new_bundle["entry"])} to r4 server')
        bundle_id = post_fhir_r4_bundle(new_bundle)

        return format_bundle_response('observation post done', new_bundle, bundle_id, pid)
