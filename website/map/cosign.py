import requests
from .user import User, DisabledUser


class ServerDownException(Exception):
    pass


class CoSign():
    def __init__(self, app, flask_redis):
        self.config = {
            "name": app.config["DICE_API_NAME"],
            "key": app.config["DICE_API_KEY"]
        }

        self.flask_redis = flask_redis

    def getuser(self, login_token, ip):
        #try:
            payload = {'cookie': login_token, 'ip': ip}
            r = requests.get("http://bi:6663/check/" + self.config['name'] + "/" + self.config['key'], params=payload)
            obj = r.json()

            # print(obj)
            if obj['status'] == 'success' and obj['data']['Realm'] == 'INF.ED.AC.UK':
                banned = self.flask_redis.sismember("bannedusers", obj['data']['Principal'])
                if not banned:
                    return User(login_token, obj['data'])

            # if obj['status'] == 'success':
            #     return DisabledUser(login_token, obj['data'])

        #except Exception:
        #    print("Ran into exception in getuser")
