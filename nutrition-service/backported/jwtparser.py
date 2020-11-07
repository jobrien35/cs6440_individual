import jwt
import os




"""
For graphql queries see tests/gql_queries.txt/or postman collections
for workflow for authing admin, user, creating location
approving user, and giving write permissions for that location

for generating keys that adhere to the python jwt decode method
use runme.sh for RSA256 keys that work across all the services

low user
    permission: ACTIVE
    locations[index]['permissions'] = WRITE

super admin
    permission: ADMIN
    locations are empty, can do everything

location admin
    permission: ACTIVE
    locations[index]['permissions'] = WRITE


JWT for low user with write location permissions:


{
    'id': 2,
    'permission': 'ACTIVE',
    'company':
        {
            'id': 1,
            'name':
            'best company'
        },
    'locations':
    [
        {
            'id': 3,
            'name': 'location2',
            'permission': 'WRITE'
        }
    ],
    'iat': 1518899396, 'exp': 1518902996
}

"""




CAN_WRITE = ['WRITE', 'ADMIN']  # location permissions
QUERY_PARAM = 'access_token'
AUTH_HEADER = 'Authorization'

# (type, code) code corresponds to keys for use with api_responses.py to avoid the import
# set in self.ERR
AUTH_ERROR = ('jwtError', 'NOAUTH')
PERMISSION_ERROR = ('jwtPermissionError', 'NOPERMS')




class JWTParser:
    """
    parse jwt, verify authorization permissions
    """
    def __init__(self, request, requestedLocation, query_param=False):
        """
        Configure authentication and token information for current request
        Parse jwt and validate against public key
        Confirm user has permissions to perform write operation
            Users with READ do not need to access file import features
            Users with READ do need to access images ONLY via download, not upload

        request
            Request from frontend containing authorization information

        requestedLocation
            The parsed location being accessed with the current jwt/request

        query_param
            Should only be True in a GET request for images (see has_auth)

        RETURNS usable token information, or error message
        """
        self.token = None
        self.ERR = None  # TUPLE only used when error occurs (type, code)
        self.company = None
        # set allowed=True for users with permissions to read/write at valid location
        #   False for requested location with user not approved by admin
        self.allowed = False
        # set readOnly=True for users with read permissions
        #   used for blocking write perms
        #   but still allow image download when location is valid
        self.readOnly = False
        self.message = ''
        print()  # spacing
        print('[I] jwt -> init()\n -- validating jwt')
        self.authed, self.encToken, self.message = self.has_auth(request, query_param)
        if self.authed:
            print('[I] jwt -> init()\n -- valid auth information received')
            self.public = self.get_public_key()
            if not self.public:
                print('[I] jwt -> init()\n -- public key malformed, invalid')
                self.authed = False
                self.message = 'invalid key'  # docker problem usually
                self.ERR = AUTH_ERROR
            if self.public:
                self.decode_token()  # sets self.token or does error handling
            if self.token and self.authed:  # valid jwt jic something went wrong
                print('[I] jwt token: {0}'.format(self.token))
                self.allowed, self.message = self.parse_location_permissions(requestedLocation)
                print('[I] jwt allowed: {0}'.format(self.allowed))
                print('[I] jwt message: {0}'.format(self.message))
                self.company = self.token['company']['name'].replace(' ', '_')
                if self.message == 'READ':
                    print('[I] read only user')
                    self.readOnly = True  # image download ignores the message response
                    self.message = 'User cannot perform this action'
                    if not query_param:
                        print('[I] jwt read only, prevent GET query')
                        self.ERR = PERMISSION_ERROR
                    if query_param and self.allowed:
                        self.ERR = None
                        print('[I] jwt read only, allowed GET query')
            if not self.allowed:
                print('[I] jwt not allowed, erroring')
                self.ERR = PERMISSION_ERROR
        elif not self.encToken:
            print('[I] jwt invalid auth param/header, fix your request')
            print(self.message)
            self.ERR = AUTH_ERROR
        print()  # spacing


    def has_auth(self, request, query_param=False):
        """
        query_param=True
            GET requests for images with access_token parameter only
              Only implemented for use with image download on frontend
                for read_only users to view ecomarkers at valid location
                due to image GET not allowing auth header being set

        query_param=False
            check for 'Authorization': Bearer token
                POST requests with header
                GET request file

        RETURNS Boolean for authorization
        RETURNS Token if found
        RETURNS Message about type of auth
        """
        print('[I] jwt -> has_auth()')
        authed = False
        token = None
        message = 'Request Not Authorized'
        if query_param:
            if QUERY_PARAM in request.args:
                authed = True
                message = 'Authed via request parameter'
                token = request.args.get('access_token')
            else:
                message = 'Missing parameter'

        elif not query_param:
            if AUTH_HEADER in request.headers:
                authed = True
                token = request.headers['Authorization'].split()[1]
                message = 'Authed via header'
            else:
                message = 'Missing header'
        print('[I] authed: {0}\n[I] message: {1}'.format(authed, message))
        return authed, token, message


    def get_public_key(self):
        """
        get public key from environment variable
        either production or development method:

        PRODUCTION:
        assuming key starts with -----BEGIN PUBLIC KEY-----\n
        and each line parsed from the original file is in the string with a \n

        -----BEGIN PUBLIC KEY-----\n
        line1\n
        line2\n
        ...\n
        -----END PUBLIC KEY-----

        saved in env as

        key=-----BEGIN PUBLIC KEY-----\nline1\nline2\n...\n-----END PUBLIC KEY-----

        DEVELOPMENT:
        set PUBLIC_KEY as the path to the file

        RETURNS string or None if error
        """
        key = os.environ.get('PUBLIC_KEY', None)
        if os.path.isfile(key):
            print('[I] jwt -> get_public_key()\n -- development, key path given')
            try:  # read from file and format like prod internally
                with open(key, 'r') as fd:
                    publicArr = fd.readlines()
                pubKey = ''.join(publicArr)
                print('[I] pubkey: ...{0}...'.format(pubKey[-40:]))  # only print key in dev
            except FileNotFoundError:  # issue with docker env, path, key
                pubKey = None
        else:
            pubKey = bytes(key, 'utf-8').decode('unicode_escape')
        return pubKey


    def decode_token(self):
        """
        the token has been acquired successfully from the request
        now decode that token for verifying location and permissions
        """
        print('[I] jwt -> decode_token()')
        try:
            self.token = jwt.decode(self.encToken, self.public, algorithm='RS256')
        except jwt.exceptions.ExpiredSignatureError:
            print('[I] token is old, refresh needed')
            self.authed = False
            self.token = None
            self.message = 'Token is expired'
        except jwt.exceptions.DecodeError:
            self.authed = False
            self.token = None
            self.message = 'Malformed token received'
        except ValueError:  # keygen.js used for keys, use runme.sh
            self.authed = False
            self.token = None
            self.message = 'Parsed key invalid'
        except jwt.exceptions.InvalidAlgorithmError:
            self.authed = False
            self.token = None  # need cryptography package for RSA256
            self.message = 'Missing dependencies for decode'


    def parse_location_permissions(self, requestedLocation):
        """
        parse jwt for corresponding user locations and permissions

        RETURNS True if user can access location and perform action
        RETURNS Message about type of permission/user
        """
        print('[I] jwt -> parse_location_permissions()')
        print('-- requested location: <{0}>'.format(requestedLocation))
        if self.token['permission'] == 'ADMIN':
            return True, 'Company admin authorized'
        if self.token['permission'] == 'INACTIVE':
            return False, 'Inactive user'
        for entry in self.token['locations']:
            print('[I] jwt location: {0}'.format(entry['name']))
            if requestedLocation == entry['name']:
                if entry['permission'] in CAN_WRITE:  # admin | write
                    return True, 'User can perform action on given location'
                else:  # user only has read permissions
                    return True, 'READ'
            else:
                continue  # check other locations
        return False, 'User not approved for location'  # user not in location
