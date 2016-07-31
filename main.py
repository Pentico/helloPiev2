#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import jinja2

from google.appengine.api import users
from models import Note
from models import CheckListItem
from google.appengine.ext import ndb

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)


# Method for rendering the view, and doing queries.
def _render_template(template_name, context=None):

    if context is None:
        context = {}

    user = users.get_current_user()
    ancestor_key = ndb.Key("User", user.nickname())
    qry = Note.owner_query(ancestor_key)
    context['notes'] = qry.fetch()

    template = jinja_env.get_template(template_name)
    return template.render(context)


# Main Class called MainHandler
class MainHandler(webapp2.RequestHandler):

    # Transactions
    @ndb.transactional
    def _create_note(self, user):
        note = Note(parent=ndb.Key("User", user.nickname()),
                    title=self.request.get('title'),
                    content=self.request.get('content'))
        note.put()

        item_titles = self.request.get('checklist_items').split(',')
        for item_title in item_titles:
            item = CheckListItem(parent=note.key, title=item_title)
            item.put()
            note.checklist_items.append(item.key)

        note.put()

    # Method for get method html(handler)
    def get(self):
        user = users.get_current_user()

        if user is not None:
            # self.response.write('Hello Note, am a User')
            logout_url = users.create_logout_url(self.request.uri)
            template_context = {
                'user': user.nickname(),
                'logout_url': logout_url,
            }

            self.response.out.write(
                _render_template('main.html', template_context)
            )

        else:
            login_url = users.create_login_url(self.request.uri)
            self.redirect(login_url)

    def post(self):
        user = users.get_current_user()
        if user is None:
            self.error(401)

        self._create_note(user)

        logout_url = users.create_logout_url(self.request.uri)
        template_context = {
            'user': user.nickname(),
            'logout_url': logout_url,
        }

        self.response.out.write(
            _render_template('main.html', template_context)
        )



app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
