from flask_login import UserMixin

def check_uun_hash(uun, hash):
    import hashlib
    from config import CRYPTO_SECRET as secret

    hasher = hashlib.sha512()
    hasher.update((uun + str(secret)).encode("utf-8"))

    return hasher.hexdigest() == hash

class User(UserMixin):
    def __init__(self, login_token, attrs):
        self.login_token = login_token
        self.__dict__.update(attrs)

    def get_id(self):
        return self.login_token

    def get_username(self):
        return self.Principal

    def get_name(self):
        from map import ldap
        return ldap.get_name(self.get_username())

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
        from map import flask_redis

        if check_uun_hash(self.get_username(), friend_hash):
            if self.get_dnd() and not ignore_dnd:
                return ""
            return self.get_username()
        
        all_friends = flask_redis.smembers(self.get_username()+'-friends')
        
        for friend in all_friends:
            if check_uun_hash(friend, friend_hash):
                from map import flask_redis
                is_dnd = flask_redis.sismember("dnd-users", friend)
                if is_dnd and not ignore_dnd:
                    return ""
                else:
                    return friend
        return ""

    def has_friend(self, friend_hash, ignore_dnd=False):
        return self.get_friend(friend_hash, ignore_dnd) != ""

class DisabledUser(User):
    def get_friend(self, hash):
        return ""

    def has_friend(self, hash):
        return False
