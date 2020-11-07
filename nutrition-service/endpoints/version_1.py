from backported.api_responses import api_error_response, api_success_response, codes
from backported import jwtparser

from flask import request, send_file, safe_join
from werkzeug.utils import secure_filename
from flask.views import MethodView
#from PIL import Image

import uuid
import os




UPLOAD_DIRECTORY = "/images/uploads"
EXTENSIONS = set(['jpg', 'jpeg', 'png'])




def check_image(filename):
    return '.' in filename and filename.split('.', 1)[1].lower() in EXTENSIONS


class Upload_Image_V1(MethodView):
    def compress_image(self, image_path):
        """
        save smaller images to decrease load times on mobile

        resampling filter methods
        https://pillow.readthedocs.io/en/5.1.x/handbook/concepts.html?highlight=NEAREST#filters-comparison-table
        thumbnail()
        https://pillow.readthedocs.io/en/5.1.x/reference/Image.html#PIL.Image.Image.thumbnail
        save()
        https://pillow.readthedocs.io/en/5.1.x/reference/Image.html#PIL.Image.Image.save
        """
        #fd = Image.open(image_path)
        #dimensions = (640, 480)  # x,y
        #fd.thumbnail(size=dimensions, resample=Image.HAMMING)
        #fd.save(image_path)  # default quality is 75 out of 95 for jpg, png does not support quality
        print('upload')

    def post(self):
        """

        Users can only access if user has write/admin permissions for given location

        Authorization via request header 'Authorization' only

        Posted image via form-data to be compressed and saved to file system
        Posted location via form-data used to verify jwt and save file

        RETURNS location_img_name.extension or error response
        """

        data = request.form.to_dict(flat=False)

        if 'image' not in request.files:
            return api_error_response('No image provided', 'ValidationError', codes['ERROR'])
        if 'location' not in data:
            return api_error_response('No location provided', 'validationError', codes['ERROR'])

        print('=' * 25)
        print('[I] Upload_Image -> post()')
        image = request.files['image']
        location = data['location'][0]

        if image.filename == '':
            return api_error_response('Invalid image name', 'validationError', codes['ERROR'])
        if not check_image(image.filename):
            return api_error_response('Invalid extension', 'validationError', codes['ERROR'])

        jw = jwtparser.JWTParser(request, location)
        if jw.ERR:
            return api_error_response(jw.message, jw.ERR[0], codes[jw.ERR[1]])
        print('[I] auth complete')

        img_uuid = str(uuid.uuid4())
        token = '{0}_{1}'.format(location, img_uuid)
        img_name = token + "." + image.filename.split('.', 1)[1].lower()
        filename = secure_filename(img_name)
        fileLocation = safe_join(UPLOAD_DIRECTORY, filename)
        image.save(fileLocation)
        print('[I] image saved')
        self.compress_image(fileLocation)
        print('[I] image compressed')
        print('[I]     img_name: {0}'.format(img_name))
        print('[I]     filename: {0}'.format(filename))
        print('[I] fileLocation: {0}'.format(fileLocation))
        image.close()
        args = {'token': img_name}
        return api_success_response('Image uploaded', args, code=codes['CREATED'])


class Download_Image_V1(MethodView):
    def get(self):
        """

        Users can access with any ADMIN/ACTIVE permissions

        Authorization via query_parameter 'access_token' only

        Retrieves the requested image by location_img_name.extension, same returned from
        the post request originally

        RETURNS the image requested or error response
        """

        if 'image' not in request.args:
            return api_error_response('No image requested', 'ValidationError', codes['ERROR'])
        if request.args.get('file') == '':
            return api_error_response('Invalid file name', 'ValidationError', codes['ERROR'])

        print('=' * 25)
        print('[I] Download_Image -> get()')
        name = request.args.get('image')
        print('[I] image requested: {0}'.format(name))
        imageName = secure_filename(name)
        location = name.split('_')[0]

        jw = jwtparser.JWTParser(request, location, query_param=True)

        if jw.ERR:
            return api_error_response(jw.message, jw.ERR[0], codes[jw.ERR[1]])
        print('[I] auth complete')

        fileLocation = safe_join(UPLOAD_DIRECTORY, imageName)
        print('[I]     filename: {0}'.format(imageName))
        print('[I] fileLocation: {0}'.format(fileLocation))
        if os.path.isfile(fileLocation):
            mimetype = 'image/' + imageName.split('.', 1)[1].lower()
            return send_file(safe_join(UPLOAD_DIRECTORY, imageName), mimetype=mimetype)
        else:
            return api_error_response('No image found', 'InternalServerError', codes['CRITERROR'])
