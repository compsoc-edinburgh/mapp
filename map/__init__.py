from flask import Flask
from flask.sessions import SecureCookieSessionInterface

from flask_login import LoginManager

from flask_redis import FlaskRedis

from werkzeug.contrib.fixers import ProxyFix

from .cosign import CoSign

flask_redis = FlaskRedis()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    app.wsgi_app = ProxyFix(app.wsgi_app)

    flask_redis.init_app(app, decode_responses=True)

    from .blueprints import api, auth, views
    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(views.bp)

    app.jinja_env.globals.update(rooms_list=api.rooms_list)

    return app


class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""
    def save_session(self, *args, **kwargs):
        return


app = create_app()

app.session_interface = CustomSessionInterface()

cosign = CoSign(app)

lm = LoginManager(app)
lm.login_view = "login"


@lm.request_loader
def get_user(request):
    print("request_loader: checking for session cookie...")
    if 'cosign-betterinformatics.com' in request.cookies:
        print("request_loader: getting user via request_loader")
        return cosign.getuser(request.cookies['cosign-betterinformatics.com'], request.remote_addr)
