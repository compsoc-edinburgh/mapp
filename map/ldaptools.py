import ldap

class LDAPTools():
    def __init__(self, app):
        self.config = {
            "server": app.config['LDAP_SERVER'],
            "memberdn": "ou=People,dc=inf,dc=ed,dc=ac,dc=uk"
        }

    def get_name(self, uun):
        l = ldap.initialize(self.config["server"])
        ldap_filter = "uid=" + uun
        result_id = l.search(self.config['memberdn'], ldap.SCOPE_SUBTREE, ldap_filter, None)

        if result_id:
            type, data = l.result(result_id, 0)
            if data:
                dn, attrs = data[0]
                return attrs['gecos'][0]
