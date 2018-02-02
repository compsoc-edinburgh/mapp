from map import app, flask_redis, ldap
from datetime import datetime
import hashlib
import json, re
from flask import render_template, request, jsonify, redirect, make_response
from flask.ext.login import login_user, logout_user, login_required, current_user


class APIError(Exception):
    status_code = 401
    
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
            
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(APIError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def map_routine(which_room):
    room = flask_redis.hgetall(str(which_room))
    room_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
    machines = {m: flask_redis.hgetall(m) for m in room_machines}
    num_rows = max([int(machines[m]['row']) for m in machines])
    num_cols = max([int(machines[m]['col']) for m in machines])

    num_machines = len(machines.keys())
    num_used = 0
    
    rows = []
    for r in xrange(0, num_rows+1):
        unsorted_cells = []
        for c in xrange(0, num_cols+1):
            default_cell = {'hostname': None, 'col': c, 'row': r}
            cell = [v for (k, v) in machines.iteritems() if int(v['row']) == r and int(v['col']) == c]
            if not cell:
                cell = default_cell
            else:
                cell = cell[0]

            try:
                if cell['user'] is not "" or cell['status'] == "offline":
                    num_used += 1
            except Exception:
                pass
            unsorted_cells.append(cell)

        cells = unsorted_cells
        rows.append(cells)

    num_free = num_machines - num_used

    low_availability = num_free <= 0.3 * num_machines

    date_format = "%Y-%m-%dT%H:%M:%S.%f"
    last_update = datetime.strptime(flask_redis.get("last-update"),date_format)
    last_update = last_update.strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "room"             : room,
        "rows"             : rows,
        "num_free"         : num_free,
        "num_machines"     : num_machines,
        "low_availability" : low_availability,
        "last_update"      : last_update
    }

def rooms_dict():
    out = dict({})
    rooms = list(flask_redis.smembers("forresthill-rooms"))
    rooms.sort()
    for room in rooms:
        out[room] = flask_redis.hget(room, "name")
    return out

def room_machines(which):
    machines = flask_redis.lrange(which + "-machines", 0, -1)
    print(machines)
    return machines

@app.route("/")
def about():
    rooms = map(lambda name: flask_redis.hgetall(name), flask_redis.smembers("forresthill-rooms"))
    rooms.sort(key=lambda x: x['key'])

    friends = set()
    if current_user.is_authenticated:
        for room in rooms:
            room_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
            for machineName in room_machines:
                machine = flask_redis.hgetall(machineName)
                if current_user.has_friend(machine['user']):
                    username = ldap.get_name(current_user.get_friend(machine['user']))
                    friends.add((username, room['key'], room['name']))
        friends = list(friends)
        friends.sort(key=lambda x: x[0])
    return render_template("about.html", rooms=rooms, friends=friends)

@app.route('/site/<which>', methods=['GET', 'POST'])
@login_required
def index(which):
    default = "drillhall"
    if which == "":
        which = default

    try:
        this = map_routine(which)
    except KeyError:
        this = map_routine(default)
        
    return render_template('index.html',
                           room=this['room'],
                           rows=this['rows'],
                           num_machines=this['num_machines'],
                           num_free=this['num_free'],
                           low_availability=this['low_availability'],
                           last_update=this['last_update'],
                           ldap=ldap)

@app.route('/api/refresh')
@login_required
def refresh():
    default = "drillhall"
    which = request.args.get('site', '')
    if which == "":
        which = default

    try:
        this = map_routine(which)
    except KeyError:
        this = map_routine(default)
        
    return render_template('refresh.xml',
                           room=this['room'],
                           rows=this['rows'],
                           num_machines=this['num_machines'],
                           num_free=this['num_free'],
                           low_availability=this['low_availability'],
                           last_update=this['last_update'])


@app.route("/login", methods=['GET'])
def login():
    url = "https://weblogin.inf.ed.ac.uk/cosign-bin/cosign.cgi?cosign-betterinformatics.com&https://map.betterinformatics.com"
    return redirect(url + request.args.get('next', '/'))

@app.route("/flip_dnd", methods=['POST'])
@login_required
def flip_dnd():
    current_user.set_dnd(not current_user.get_dnd())
    return redirect(request.form.get('next', '/'))

@app.route("/logout")
def logout():
    resp = make_response(redirect(request.args.get('next','/')))
    resp.set_cookie("cosign-betterinformatics.com", "", domain="betterinformatics.com", expires=0)
    return resp

@app.route("/api/rooms")
@app.route("/api/rooms/<which>")
@login_required
def rooms(which=""):
    if not which:
        return jsonify(rooms_dict())
    else:
        rooms = []
        for room in which.split(","):
            rooms.extend(room_machines(room))
        return jsonify({"rooms":rooms})
    

@app.route('/api/update', methods=['POST'])
def update():
    content = request.json

    try:
        key = content['callback-key']
    except Exception:
        key = ""

    if key not in flask_redis.lrange("authorised-key", 0, -1):
        # HTTP 401 Not Authorised
        print "******* CLIENT ATTEMPTED TO USE BAD KEY *******"
        raise APIError("Given key is not an authorised API key") 

    pipe = flask_redis.pipeline()
    
    try:
        for machine in content['machines']:
            host   = machine['hostname']
            user   = machine['user']
            ts     = machine['timestamp']
            active = machine['active']
            status = machine['status']

            pipe.hset(host, "user", user)
            pipe.hset(host, "timestamp", ts)
            pipe.hset(host, "active", active)
            pipe.hset(host, "status", status)

    except Exception:
        print("Malformed JSON content")
        raise APIError("Malformed JSON content", status_code=400)

    pipe.set("last-update", str(datetime.utcnow().isoformat()))
    pipe.execute()

    return jsonify(status="ok")

@app.route("/api/update_available", methods=['POST'])
@login_required
def update_available():
    content = request.json
    date_format = "%Y-%m-%dT%H:%M:%S.%f"
    
    try:
        client_time = datetime.strptime(content['timestamp'],date_format)
    except Exception as e:
        raise APIError("Malformed JSON POST data", status_code=400)

    last_update = datetime.strptime(flask_redis.get("last-update"),date_format)

    user_behind = client_time < last_update
    
    return jsonify(status=str(user_behind))



@app.route("/api/friends", methods=['GET', 'POST'])
@login_required
def friends():
    if request.method == "POST":
       formtype = request.form.get('type')
       if formtype == "del":
           remove_friends = request.form.getlist('delfriends[]')
           print remove_friends
           flask_redis.srem(current_user.get_username() + "-friends", *remove_friends)
       elif formtype == "add":
           add_friend = request.form.get('newfriend')
           #if(re.match("^[A-Za-z]+\ [A-Za-z]+$", add_friend) == None):
           #    raise APIError("Friend name expected in [A-z]+\ [A-z]+ form.", status_code=400)
           flask_redis.sadd(current_user.get_username() + "-friends", add_friend)

    friends = flask_redis.smembers(current_user.get_username() + "-friends")
    friends = list(friends)

    for i in range(len(friends)):
        uun = friends[i]
        friend = uun

        friend_name = ldap.get_name(uun)
        if friend_name:
            friend = friend_name + " (" + uun + ")"

        friends[i] = (friend, uun)

    friends = sorted(friends, key=lambda s: s[0].lower())

    return jsonify(friendList=friends) #Set up for ajax responses

    
@app.route("/demo")
def demo():
    # Manual render, for demo purpoises.
    # DOES NOT REQUIRE AUTH
    return render_template(
        "index.html",
        room={"name":"Mapp Demo"},
        rows=[
            [
                {},
                {"hostname":"dish"},
                {"hostname":"paulajennings"},
                {},{},{},{},{}
            ],[
                {"hostname":"dent"},
                {"hostname":"prefect"},
                {"hostname":"slartibartfast", "user":" ","friend":"moony"},
                {"hostname":"random", "user":" ","friend":"wormtail"},
                {"hostname":"colin"},
                {},
                {"hostname":"marvin"},
                {"hostname":"vogon"}
            ],[
                {"hostname":"beeblebrox", "user":" ","friend":"padfoot"},
                {"hostname":"trillian", "user":" "},
                {"hostname":"agrajag"},
                {"hostname":"krikkit", "user":" "},
                {"hostname":"almightybob"},
                {},
                {"hostname":"jynnan", "user":" "},
                {"hostname":"tonyx"}
            ],[
                {},{},{},
                {"hostname":"eddie"},
                {"hostname":"fenchurch", "user":" "},
                {},{},{}
            ],[
                {},{},{},
                {"hostname":"anangus"},
                {"hostname":"benjy", "user":" ","friend":"prongs"},
                {},{},{}
            ]
        ],
        num_machines=20,
        num_free=12,
        low_availability=False,
        last_update="1998-05-02 13:37")
