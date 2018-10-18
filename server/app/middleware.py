import falcon
import json
import logging
import urllib
import json
import logging

_logger = logging.getLogger(__name__)

class Middleware(object):
    def __init__(self):
        super(Middleware, self).__init__()

    def process_request(self, req, resp):
        pass

    def process_resource(self, req, resp, resource, params):
        pass

    def process_response(self, req, resp, resource):
        pass


class DBMiddleware(Middleware):
    def __init__(self, db_engine):
        self.db_engine = db_engine

    def process_resource(self, req, resp, resource, params):
        resource.cursor = self.db_engine.conn.cursor()

    def process_response(self, req, resp, resource, req_succeeded):
        if hasattr(resource, 'cursor'):
            if req_succeeded: self.db_engine.conn.commit()
            resource.cursor.close()


class RequireJSON(Middleware):
    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        if req.method in ('POST', 'GET'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')


class JSONTranslator(Middleware):
    def process_request(self, req, resp):
        if req.content_length in (None, 0):
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        if 'result' not in resp.context:
            return

        resp.body = json.dumps(resp.context['result'])


class AuthMiddleware(Middleware):
    def __init__(self, apikeys):
        super(AuthMiddleware, self).__init__()
        self.keys = apikeys

    def _token_is_valid(self, token):
        return token in self.keys

    def process_request(self, req, resp):
        if req.method not in ('OPTIONS'):
            params = dict(urllib.parse.parse_qsl(req.query_string))
            token = params.get('apikey', None)

            if token is None:
                _logger.error('Unauthorized request. No token given.')
                raise falcon.HTTPUnauthorized('Authentication required',
                    'Please provide an API key as part of the request.', [])

            if not self._token_is_valid(token):
                _logger.error('Unauthorized request. Invalid token.')
                raise falcon.HTTPUnauthorized('Authentication required',
                    'The provided API key is not valid.', [])