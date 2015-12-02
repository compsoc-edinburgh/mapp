#!/usr/bin/env python
from map import app

app.run(host="0.0.0.0", port=443, processes=30, debug=False, ssl_context='adhoc')
