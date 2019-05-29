from flask import Flask, g
from flask_redis import FlaskRedis
from flask_login import LoginManager
from flask.sessions import SecureCookieSessionInterface
from ldappool import ConnectionManager

from .cosign import CoSign
from .ldaptools import LDAPTools
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = ProxyFix(app.wsgi_app)

flask_redis = FlaskRedis(app, 'REDIS', decode_responses=True)
ldap = LDAPTools(
    ConnectionManager(app.config["LDAP_SERVER"])
)

cosign = CoSign(app, flask_redis)

lm = LoginManager(app)
lm.login_view = "login"


class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""
    def save_session(self, *args, **kwargs):
        return

app.session_interface = CustomSessionInterface()

@lm.request_loader
def get_user(request):
    print("request_loader: checking for session cookie...")
    if 'cosign-betterinformatics.com' in request.cookies:
        print("request_loader: getting user via request_loader")
        return cosign.getuser(request.cookies['cosign-betterinformatics.com'], request.remote_addr)

from . import views

app.jinja_env.globals.update(rooms_list=views.rooms_list)
