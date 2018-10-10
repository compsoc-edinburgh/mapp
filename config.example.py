import os

SECRET_KEY = os.urandom(512)

DICE_API_NAME = "mapp"
DICE_API_KEY = "PASSWORD" # this needs to be provided

LDAP_SERVER = "ldap://dir.inf.ed.ac.uk"

REDIS_URL = "redis://:PASSWORD@localhost:6379/0"

CRYPTO_SECRET="SECRET KEY"
#CRYPTO_SECRET="Done this to invalidate old data"
