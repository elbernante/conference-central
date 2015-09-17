import json
import os
import time
import uuid

from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models import Profile

def getUserId(user, id_type="email"):
    if id_type == "email":
        return user.email()

    if id_type == "oauth":
        """A workaround implementation for getting userid."""
        auth = os.getenv('HTTP_AUTHORIZATION')
        bearer, token = auth.split()
        token_type = 'id_token'
        if 'OAUTH_USER_ID' in os.environ:
            token_type = 'access_token'
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
               % (token_type, token))
        user = {}
        wait = 1
        for i in range(3):
            resp = urlfetch.fetch(url)
            if resp.status_code == 200:
                user = json.loads(resp.content)
                break
            elif resp.status_code == 400 and 'invalid_token' in resp.content:
                url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
                       % ('access_token', token))
            else:
                time.sleep(wait)
                wait = wait + i
        return user.get('user_id', '')

    if id_type == "custom":
        # implement your own user_id creation and getting algorythm
        # this is just a sample that queries datastore for an existing profile
        # and generates an id if profile does not exist for an email
        profile = Conference.query(Conference.mainEmail == user.email())
        if profile:
            return profile.id()
        else:
            return str(uuid.uuid1().get_hex())


class MultiInequalityQuery(object):
    def __init__(self, model_or_query):
        if isinstance(model_or_query, ndb.model.MetaModel):
            self.query = model_or_query.query()
        elif isinstance(model_or_query, ndb.query.Query):
            self.query = model_or_query
        else:
            raise TypeError('Must be instance of Model or Query.')

        self.first_inequality = self._get_first_inequality(self.query.filters)
        self.post_inq_filters = []


    def filter(self, *args):
        """Checks if each arg is an ineqality and appends it to the inequality
        post filters
        """
        if not args:
            return self

        for arg in args:
            if not isinstance(arg, ndb.query.Node):
                raise TypeError('Filter should be instance of Node.')
            if not self._push_filter(arg):
                self.query = self.query.filter(arg)

        return self


    def _get_first_inequality(self, f_node):
        inequalities = self._get_inequalities(f_node)
        if len(inequalities) == 0:
            return None
        else:
            return inequalities[0]


    def _get_inequalities(self, f_node):
        inequalities = []
        if isinstance(f_node,
                (ndb.query.DisjunctionNode, ndb.query.ConjunctionNode)):
            for f_n in f_node:
               inequalities.extend(self._get_inequalities(f_n))
        elif isinstance(f_node, ndb.query.FilterNode):
            filter_dict = self._node_to_dict(f_node)
            if filter_dict['symbol'] != '=':
                inequalities.append(filter_dict)
        return inequalities


    def _push_filter(self, filter_node):
        inequalities = self._get_inequalities(filter_node)
        put_to_post = False

        for inq in inequalities:
            if not self.first_inequality:
                self.first_inequality = inq
            else:
                self.first_inequality['name'] != inq['name']
                put_to_post = True
                break

        if put_to_post:
            self.post_inq_filters.append(filter_node)

        return put_to_post


    def _node_to_dict(self, f_node):
        filter_dict = {}
        node_dict = getattr(f_node, '__dict__')
        for key, value in node_dict.items():
            if key.endswith('name'):
                filter_dict['name'] = value
            elif key.endswith('symbol'):
                filter_dict['symbol'] = value
            elif key.endswith('value'):
                filter_dict['value'] = value
        return filter_dict


    def _make_evaluator(self, filter_node):

        def make_closure(inq):
            if (inq['symbol'] == '>'):
                return lambda x: getattr(x, inq['name']) > inq['value']
            elif (inq['symbol'] == '<'):
                return lambda x: getattr(x, inq['name']) < inq['value']
            elif (inq['symbol'] == '>='):
                return lambda x: getattr(x, inq['name']) >= inq['value']
            elif (inq['symbol'] == '<='):
                return lambda x: getattr(x, inq['name']) <= inq['value']
            elif (inq['symbol'] == '!='):
                return lambda x: getattr(x, inq['name']) != inq['value']
            elif (inq['symbol'] == '='):
                return lambda x: getattr(x, inq['name']) == inq['value']
            else:
                raise NotImplementedError(
                    'Unsuported operator: {}'.format(inq['symbol'])
                )

        f_dict = self._node_to_dict(filter_node)

        # FilterNode coverts TimeProperty and DateProperty to datetime.
        # Convert back to time or date
        prop_type = ndb.Model._kind_map[self.query.kind] \
                        ._properties[f_dict['name']].__class__.__name__
        if prop_type == 'TimeProperty' \
                and isinstance(f_dict['value'], datetime):
            f_dict['value'] = f_dict['value'].time()
        elif prop_type == 'DateProperty' \
                and isinstance(f_dict['value'], datetime):
            f_dict['value'] = f_dict['value'].date()

        return make_closure(f_dict)


    def _make_and_evaluator(self, con_node):
        post_evals = []

        for f_n in con_node:
            if isinstance(f_n, ndb.query.ConjunctionNode):
                post_evals.append(self._make_and_evaluator(f_n))
            elif isinstance(f_n, ndb.query.DisjunctionNode):
                post_evals.append(self._make_or_evaluator(f_n))
            elif isinstance(f_n, ndb.query.FilterNode):
                post_evals.append(self._make_evaluator(f_n))

        def and_evaluators(x):
            retval = True
            for p_eval in post_evals:
                if not p_eval(x):
                    retval = False
                    break
            return retval

        return and_evaluators


    def _make_or_evaluator(self, dis_node):
        post_evals = []

        for f_n in dis_node:
            if isinstance(f_n, ndb.query.ConjunctionNode):
                post_evals.append(self._make_and_evaluator(f_n))
            elif isinstance(f_n, ndb.query.DisjunctionNode):
                post_evals.append(self._make_or_evaluator(f_n))
            elif isinstance(f_n, ndb.query.FilterNode):
                post_evals.append(self._make_evaluator(f_n))

        def or_evaluators(x):
            retval = False
            for p_eval in post_evals:
                if p_eval(x):
                    retval = True
                    break
            return retval

        return or_evaluators


    def __iter__(self):
        """Iterate through the result set of the query, and hand back only
        those that satify all of the post inequality filters
        """
        post_evaluator = self._make_and_evaluator(self.post_inq_filters)
        for result in self.query:
            try:
                if post_evaluator(result):
                    yield result
            except TypeError:
                pass            # Value of a property from datastore is None
