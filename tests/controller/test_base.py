# -*- coding: utf-8 -*-

# Licensed under the Open Software License ("OSL") v. 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.opensource.org/licenses/osl-3.0.php

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import urllib
try:
    # Python >= 2.6
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

import simplexml
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, url

from torneira.controller import BaseController


class SimpleController(BaseController):
    def index(self, *args, **kwargs):
        if 'request_handler' in kwargs:
            response = 'request_handler received'
        else:
            response = 'request_handler not received'
        return response

    def post_data(self, request_handler, *args, **kwargs):
        response = []
        for key, value in kwargs.iteritems():
            if type(value) == list:
                for v in value:
                    response.append((key, v))
            else:
                response.append((key, value))
        return urllib.urlencode(response)

    def render_json(self, request_handler, *args, **kwargs):
        response = [
            {'a': 1},
            {'b': 2},
        ]
        return self.render_to_json(response, request_handler)

    def render_xml(self, request_handler, *args, **kwargs):
        response = {
            'root': {
                'a': 1,
                'b': 2,
            }
        }
        return self.render_to_xml(response, request_handler)

    def render_response_error(self, request_handler, *args, **kwargs):
        message = 'error!'
        return self.render_error(message)

    def render_response_success(self, request_handler, *args, **kwargs):
        message = 'success!'
        return self.render_success(message)


urls = (
    url(r'/controller/simple/', SimpleController, {'action': 'index'}),
    url(r'/controller/post-data/', SimpleController, {'action': 'post_data'}),
    url(r'/controller/render-json/', SimpleController, {'action': 'render_json'}),
    url(r'/controller/render-xml/', SimpleController, {'action': 'render_xml'}),
    url(r'/controller/render-error/', SimpleController, {'action': 'render_response_error'}),
    url(r'/controller/render-success/', SimpleController, {'action': 'render_response_success'}),
)
app = Application(urls, cookie_secret='secret')


class BaseControllerTestCase(AsyncHTTPTestCase):
    def get_app(self):
        return app

    def test_controller_method_must_receive_request_handler_as_kwarg(self):
        response = self.fetch('/controller/simple/')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, 'request_handler received')

    def test_post_data_should_be_received_in_kwargs(self):
        post_data = (
            ('a_list', 1),
            ('a_list', 2),
            ('a_list', 3),
            ('single_value', 'value'),
            ('another_single_value', 'value 2'),
        )
        post_body = urllib.urlencode(post_data)
        response = self.fetch('/controller/post-data/', method='POST', body=post_body)
        self.assertEqual(response.code, 200)
        self.assertEqual(parse_qs(response.body), parse_qs(post_body))

    def test_render_to_json_should_return_json_response(self):
        response = self.fetch('/controller/render-json/')
        self.assertTrue('Content-Type' in response.headers)
        self.assertEqual(response.headers['Content-Type'], 'application/json; charset=UTF-8')
        self.assertEqual(response.code, 200)

        expected = [
            {'a': 1},
            {'b': 2},
        ]
        parsed_response = json.loads(response.body)
        self.assertEqual(parsed_response, expected)

    def test_render_to_xml_should_return_xml_response(self):
        response = self.fetch('/controller/render-xml/')
        self.assertTrue('Content-Type' in response.headers)
        self.assertEqual(response.headers['Content-Type'], 'text/xml; charset=UTF-8')
        self.assertEqual(response.code, 200)

        expected = {
            'root': {
                'a': '1',
                'b': '2',
            }
        }
        parsed_response = simplexml.loads(response.body)
        self.assertEqual(parsed_response, expected)

    def test_render_response_error_should_return_preformatted_json(self):
        response = self.fetch('/controller/render-error/')
        self.assertTrue('Content-Type' in response.headers)
        self.assertEqual(response.headers['Content-Type'], 'application/json; charset=UTF-8')
        self.assertEqual(response.code, 200)

        expected = {
            'errors': {
                'error': {
                    'message': 'error!'
                }
            }
        }
        parsed_response = json.loads(response.body)
        self.assertEqual(parsed_response, expected)

    def test_render_response_success_should_return_preformatted_json(self):
        response = self.fetch('/controller/render-success/')
        self.assertTrue('Content-Type' in response.headers)
        self.assertEqual(response.headers['Content-Type'], 'application/json; charset=UTF-8')
        self.assertEqual(response.code, 200)

        expected = {
            'errors': '',
            'message': 'success!'
        }
        parsed_response = json.loads(response.body)
        self.assertEqual(parsed_response, expected)
