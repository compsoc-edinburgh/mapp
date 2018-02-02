import ldap

class LDAPTools():
    def __init__(self, app):
        self.config = {
            "server": app.config['LDAP_SERVER'],
            "memberdn": "ou=People,dc=inf,dc=ed,dc=ac,dc=uk"
        }

        self.l = ldap.initialize(self.config["server"])
        print("LDAP connection created")

    def close(self):
        self.l.unbind()
        print("LDAP connection closed")

    def get_name(self, uun):
        ldap_filter = "uid=" + uun
        result_id = self.l.search(self.config['memberdn'], ldap.SCOPE_SUBTREE, ldap_filter, None)

        if result_id:
            type, data = self.l.result(result_id, 0)
            if data:
                dn, attrs = data[0]
                return attrs['gecos'][0]
