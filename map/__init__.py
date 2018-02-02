from flask import Flask
from flask.ext.redis import FlaskRedis
from flask.ext.login import LoginManager
from flask.sessions import SecureCookieSessionInterface


from cosign import CoSign

app = Flask(__name__)
app.config.from_object('config')

flask_redis = FlaskRedis(app, 'REDIS')

cosign = CoSign(app)
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
