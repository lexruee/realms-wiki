from __future__ import absolute_import

import importlib
from hashlib import sha256

from flask import current_app
from flask_login import UserMixin, logout_user, AnonymousUserMixin
from itsdangerous import URLSafeSerializer
import bcrypt

from realms import login_manager
from realms.lib.util import gravatar_url
from . import modules


@login_manager.user_loader
def load_user(auth_id):
    return Auth.load_user(auth_id)


auth_users = {}


class Auth(object):

    @staticmethod
    def register(module):
        modules.add(module)

    @staticmethod
    def get_auth_user(auth_type):
        mod = importlib.import_module('realms.modules.auth.{0}.models'.format(auth_type))
        return mod.User

    @staticmethod
    def load_user(auth_id):
        auth_type, user_id = auth_id.split("/")
        return Auth.get_auth_user(auth_type).load_user(user_id)

    @staticmethod
    def login_forms():
        forms = []
        for t in modules:
            form = Auth.get_auth_user(t).login_form()
            if form:
                forms.append(form)
        return "<hr />".join(forms)


class AnonUser(AnonymousUserMixin):
    username = 'Anon'
    email = ''
    admin = False


class BaseUser(UserMixin):
    id = None
    email = None
    username = None
    type = 'base'

    def get_id(self):
        return unicode("{0}/{1}".format(self.type, self.id))

    def get_auth_token(self):
        key = sha256(self.auth_token_id).hexdigest()
        return BaseUser.signer(key).dumps(dict(id=self.id))

    @property
    def auth_token_id(self):
        raise NotImplementedError

    @property
    def avatar(self):
        return gravatar_url(self.email)

    @staticmethod
    def load_user(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def signer(salt):
        return URLSafeSerializer(current_app.config['SECRET_KEY'] + salt)

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))

    @staticmethod
    def check_password(password, hashed):
        return bcrypt.hashpw(password.encode('utf-8'), hashed.encode('utf-8')) == hashed

    @classmethod
    def logout(cls):
        logout_user()

    @staticmethod
    def login_form():
        pass

login_manager.anonymous_user = AnonUser
