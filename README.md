# Running:

THe environment variable MAPP_SECRET should be set to a long random 
set of characters to make the hashes leaving the bot more secure.
If it isn't set, 'None' will be used.

./config.py must contain the following, It isn't included in the git repo.

```python
MAPP_SECRET  = "some really long complex random string"
CALLBACK_KEY = "another different really long string"
```

Open a tunnel to the callback host if it isn't publicly accessible 
(Probably a good idea)
```
$ ssh -L 5000:localhost:443 username@callback
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
