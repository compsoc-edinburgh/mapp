# The Marauders App - worker

This is the worker that picks up information about every DICE machine. It takes inspiration from the original [Python implementation](https://github.com/compsoc-edinburgh/mapp-worker-py).

## How to run
- [Have Go installed](https://golang.org/doc/install)
- Ensure `$GOPATH/bin` is in your `PATH`
- Get the worker by running `go get -u github.com/compsoc-edinburgh/mapp/cmd/mapp-worker`
- Set the `MAPP_SECRET`, `CALLBACK_KEY` environment variables
- Run `mapp-worker` and let it do its magic.

## Speed
This goes through every DICE machine and scans it within 30 seconds.

## How it works

It downloads a `machines.json` file from the mapp website.

It will then attempt to authenticate against `student.login`.
If authentication does not work to `student.login`, it will abort.

All threads will authenticate with the remote hosts using the
Kerberos credentials on your machine.

### You can provide a `machines.json` file

Expects the `MACHINES_LIST` environment variable
to point to a JSON file containing a list of DICE machines.

You can get a `machines.json` file (can be called anything,
must be a `json` file though) by visiting
[this URL](https://mapp.betterinformatics.com/rooms/6.06,5.05).
Note that you can provide multiple rooms to receive machines
from multiple rooms at once.

## Production

To run this bot on any Informatics DICE machine, create a script that sets those environment variables and runs the program:

```
export CALLBACK_KEY='....'
export MAPP_SECRET='......'
mapp-worker
```

Then run the following line:

```
longjob -nobackground -28day -c "nice ./mapp-worker.sh"
```

The `longjob` command will ask for your DICE password and then
produce renewable Kerberos credentials valid for up to 28 days.
This will allow your bot to run for 28 days.

### Recovering from crashes

[@qaisjp](https://github.com/qaisjp) is a monster and uses this:

```
alias mapp_start="longjob -nobackground -28day -c ~/Documents/mapp-worker/mapp-worker.sh"
function mapp {
    read -sp "Password? " PW
    while true; do
        printf "%s" "$PW" | mapp_start
    done;
}
```
