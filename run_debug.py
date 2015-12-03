#!/usr/bin/env python
from map import app

app.run(host="0.0.0.0", port=4430, processes=30, debug=True, ssl_context='adhoc')
