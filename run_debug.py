#!/usr/bin/env python
from map import app

app.run(host="0.0.0.0", port=9000, processes=1, debug=True)
