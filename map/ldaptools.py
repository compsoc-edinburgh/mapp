import ldap
from ldap.filter import filter_format

class LDAPTools():
    def __init__(self, cm):
        self.config = {
            "memberdn": "ou=People,dc=inf,dc=ed,dc=ac,dc=uk"
        }

        self.cm = cm

    def conn(self):
        return self.cm.connection()

    def get_name(self, uun):
        with self.conn() as l:
            return self.get_name_bare(uun, l)

    def get_names(self, uuns):
        with self.conn() as l:
            return self.get_names_bare(uuns, l)

    def get_name_bare(self, uun, l):
        ldap_filter = filter_format("uid=%s", [uun])
        data = l.search_s(self.config['memberdn'], ldap.SCOPE_SUBTREE, ldap_filter, None)

        if data:
            dn, attrs = data[0]
            return attrs['gecos'][0]

    def get_names_bare(self, uuns, l):
        """Takes a list of uuns and returns a dict of uun->name"""
        query = filter_format("(|" + ("(uid=%s)" * len(uuns)) + ")", uuns)
        data = l.search_s(self.config["memberdn"], ldap.SCOPE_SUBTREE, query, ["gecos", "uid"])

        names = {}
        for _, row in data:
            names[row['uid'][0]] = row['gecos'][0]

        return names
    
    def search_name(self, name):
        with self.conn() as l:
            return self.search_name_bare(name, l)

    def search_name_bare(self, name, l):
        ldap_filter = filter_format("(|(name=*%s*)(uid=%s))", [name, name])
        data = l.search_s(self.config['memberdn'], ldap.SCOPE_SUBTREE, ldap_filter, ["gecos", "uid"])

        return map(lambda p: {
            'uun': p[1]['uid'][0],
            'name': p[1]['gecos'][0],
        }, data)



