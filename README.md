# The Marauders App - worker
This is the worker that picks up information about every DICE machine.

## Setup

1. Use `virtualenv env` to create a virtual environment. (Don't have `virtualenv`? Use `pip install virtualenv` to install it.)
2. `. env/bin/activate` to activate it
3. `pip install -f requirements.txt` to install deps
4. create and setup `config.py` as below


The environment variable `MAPP_SECRET` should be set to a long random 
set of characters to make the hashes leaving the bot more secure.
If it isn't set, 'None' will be used.

./config.py must contain the following, It isn't included in the git repo.

```python
MAPP_SECRET  = "some really long complex random string"
CALLBACK_KEY = "another different really long string"
```

## Syntax and how it works

Run the program:
```
$ python worker.py machines.json
```

If you omit the machine list, it will just do your current machine.

Expects JSON file to be a list of machines whose names can be resolved 
from the host running the program.

It will attempt to check your authentication against `student.login`.
If authentication does not work to `student.login`, it will abort.

All threads will authenticate with the remote hosts using the
Kerberos credentials on your machine.

You can get a `machines.json` file (can be called anything,
must be a `json` file though) by visiting
[this URL](https://mapp.betterinformatics.com/rooms/6.06,5.05).
Note that you can provide multiple rooms to receive machines
from multiple rooms at once.

## Production 

To run this bot on any Informatics DICE machine, run the following line:

```
longjob -nobackground -28day -c "nice python worker.py machines.json"
```

The `longjob` command will ask for your DICE password and then
produce renewable Kerberos credentials valid for up to 28 days.
This will allow your bot to run for 28 days.

callback host must be running the counterpart software, that takes the
JSON object in the header and stores it in Redis. That's in a private
repo because it contains LDAP authentication and Redis interfaces.

