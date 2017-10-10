from flask import Flask
from flask.ext.redis import FlaskRedis
from flask.ext.login import LoginManager
from flask.sessions import SecureCookieSessionInterface


from ldaptools import LDAPTools

import braintree

app = Flask(__name__)
app.config.from_object('config')

flask_redis = FlaskRedis(app, 'REDIS')

ldap = LDAPTools(app)
lm = LoginManager(app)
lm.login_view = "login"


class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""
    def save_session(self, *args, **kwargs):
        return

app.session_interface = CustomSessionInterface()

@lm.user_loader
def shit_me(uid):
    print("user_loader: trying to get user from " + uid)
    return ldap.getuser(request.cookies['cosign-betterinformatics.com'], request.remote_addr)


@lm.request_loader
def get_user(request):
    print("request_loader: checking for session cookie...")
    if 'cosign-betterinformatics.com' in request.cookies:
        print("request_loader: getting user via request_loader")
        return ldap.getuser(request.cookies['cosign-betterinformatics.com'], request.remote_addr)

from . import views
