from flask import Flask
from flask.ext.redis import FlaskRedis
from flask.ext.login import LoginManager

from ldaptools import LDAPTools

import braintree

app = Flask(__name__)
app.config.from_object('config')

flask_redis = FlaskRedis(app)
ldap = LDAPTools(app)
lm = LoginManager(app)
lm.login_view = "login"

braintree.Configuration.configure(braintree.Environment.Sandbox,
                                  merchant_id=app.config['BT_MERCHANT_ID'],
                                  public_key=app.config['BT_PUBKEY'],
                                  private_key=app.config['BT_PRIVKEY'])

@lm.user_loader
def get_user(uid):
    return ldap.getuser(uid)

from . import views
