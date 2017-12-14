# Setup

1. Use `virtualenv env` to create a virtual environment. (Don't have `virtualenv`? Use `pip install virtualenv` to install it.)
2. `. env/bin/activate` to activate it
3. `pip install -f requirements.txt` to install deps
4. create and setup `config.py` as below


The environment variable MAPP_SECRET should be set to a long random 
set of characters to make the hashes leaving the bot more secure.
If it isn't set, 'None' will be used.

./config.py must contain the following, It isn't included in the git repo.

```python
MAPP_SECRET  = "some really long complex random string"
CALLBACK_KEY = "another different really long string"
```

# Running

Run the program:
```
$ python snoop.py <MACHINE LIST>.json <USERNAME FOR MACHINES TO SCAN>
```

- If you omit the username, it will take your current username.
- If you omit the machine list, it will just do your current machine.

Expects JSON file to be a list of machines whose names can be resolved 
from the host running the program.

It'll attemt to check your authentication against the first host, of course
this won't work if it's not listening for SSH connections

All threads will authenticate with the remote hosts using the username 
provided, whose password will be asked for interactively when the 
program is run.

callback host must be running the counterpart software, that takes the
JSON object in the header and stores it in Redis. That's in a private
repo because it contains LDAP authentication and Redis interfaces.

# Example

Given a 5and6.json file, this will create a long running process.

```python
longjob -nobackground -28day -c "nice python worker.py 5and6.json"
```
