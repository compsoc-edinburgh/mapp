# Running:

THe environment variable MAPP_SECRET should be set to a long random 
set of characters to make the hashes leaving the bot more secure.
If it isn't set, 'None' will be used.

Open a tunnel to the callback host (Doing this because the callback
wasn't using HTTPS)
```
$ ssh -L 5000:localhost:5000 username@callback
```

Run the program:
```
$ python snoop.py <USERNAME FOR MACHINES TO SCAN> <MACHINE LIST>.json
```

Expects JSON file to be a list of machines whose names can be resolved 
from the host running the program.

All threads will authenticate with the remote hosts using the username 
provided, whose password will be asked for interactively when the 
program is run.

callback host must be running the counterpart software, that takes the
JSON object in the header and stores it in Redis. That's in a private
repo because it contains LDAP authentication and Redis interfaces.
