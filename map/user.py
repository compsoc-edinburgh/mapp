from flask.ext.login import UserMixin

class User(UserMixin):
    def __init__(self, login_token, attrs):
        self.login_token = login_token
        self.__dict__.update(attrs)

    def get_id(self):
        return self.login_token

    def get_username(self):
        return self.Principal

    def get_name(self):
        from map import get_ldap
        return get_ldap().get_name(self.get_username())

    def get_dnd(self):
        from map import flask_redis
        return flask_redis.sismember("dnd-users", self.get_username())

    def set_dnd(self, state):
        from map import flask_redis

        uun = self.get_username()
        if state:
            flask_redis.sadd("dnd-users", uun)
        else:
            flask_redis.srem("dnd-users", uun)

    def get_friend(self, friend_hash, ignore_dnd=False):
        import hashlib
        from config import CRYPTO_SECRET as secret
        from map import flask_redis
        
        all_friends = flask_redis.smembers(self.get_username()+'-friends')
        
        for friend in all_friends:
            hasher = hashlib.sha512()
            hasher.update(friend + str(secret))
            if hasher.hexdigest() == friend_hash:
                from map import flask_redis
                is_dnd = flask_redis.sismember("dnd-users", friend)
                if is_dnd and not ignore_dnd:
                    return ""
                else:
                    return friend
        return ""

    def has_friend(self, friend_hash, ignore_dnd=False):
        if self.get_friend(friend_hash, ignore_dnd) != "":
            return True
        return False

class BannedUser(User):
    def get_friend(self, hash):
        return ""

    def has_friend(self, hash):
        return False
