import ldap

from flask.ext.login import UserMixin

class ServerDownException(Exception): pass

class LDAPTools():
    def __init__(self, app):
        self.config = {
            "server": app.config['LDAP_SERVER'],
            "admin": app.config['LDAP_BIND_ADMIN'],
            "pass": app.config['LDAP_BIND_PASS'],
            "basedn": app.config['LDAP_BASE_DN'],
            "memberdn": app.config['LDAP_MEMBERDN'],
            "groupdn": app.config['LDAP_GROUPDN']
        }

    def getuser(self, id):
        l = ldap.initialize(self.config["server"])
        ldap_filter = "uid=" + id
        result_id = l.search(self.config['memberdn'], ldap.SCOPE_SUBTREE, ldap_filter, None)

        if result_id:
            type, data = l.result(result_id, 0)
        if data:
            dn, attrs = data[0]
            return User(attrs)

    def check_credentials(self, username, password):
        try:
            l = ldap.initialize(self.config["server"])
            l.set_option(ldap.OPT_REFERRALS,0)
            l.simple_bind_s("uid=%s,%s" % (username, self.config["memberdn"]), password)
        except ldap.INVALID_DN_SYNTAX:
            l.unbind()
            return False
        except ldap.INVALID_CREDENTIALS:
            l.unbind()
            return False
        except ldap.UNWILLING_TO_PERFORM:
            l.unbind()
            return False
        except ldap.SERVER_DOWN:
            l.unbind()
            raise ServerDownException()
            return False
        l.unbind()
        return True


class User(UserMixin):
    def __init__(self, attrs):
        self.__dict__.update(attrs)

    def get_id(self):
        return self.uid[0]

    def get_email(self):
        return self.mail[0]

    def get_friend(self, friend_hash):
        import hashlib
        from config import CRYPTO_SECRET as secret
        from map import flask_redis
        
        all_friends = flask_redis.smembers(self.get_id()+'-friends')
        
        for friend in all_friends:
            hasher = hashlib.sha512()
            hasher.update(friend + str(secret))
            if hasher.hexdigest() == friend_hash:
                return friend
        return ""

    def has_friend(self, friend_hash):
        if self.get_friend(friend_hash) != "":
            return True
        return False
