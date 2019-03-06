from map import app, flask_redis, ldap
from .user import check_uun_hash
from typing import List, Optional
import time
import hashlib
import json, re
from flask import render_template, request, jsonify, redirect, make_response
from flask_login import login_user, logout_user, login_required, current_user
import csv
from collections import defaultdict

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


def get_cascaders() -> List[str]:
    return list(flask_redis.smembers("cascaders.users"))


def find_cascader(cascaders: List[str], hash: str) -> Optional[str]:
    for uun in cascaders:
        if check_uun_hash(uun, hash):
            return uun
    return None


def get_cascader_elsewhere_count(cascaders: List[str], notRoom: str) -> int:
    rooms = filter(lambda name: name != notRoom, flask_redis.smembers("forresthill-rooms"))
    rooms = map(lambda name: flask_redis.hgetall(name), rooms)

    count: int = 0

    for room in rooms:
        room_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
        for machineName in room_machines:
            machine = flask_redis.hgetall(machineName)
            if machine['user']:
                uun = find_cascader(cascaders, machine['user'])
                if uun:
                    count += 1

    return count


def map_routine(which_room):
    room = flask_redis.hgetall(str(which_room))
    room_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
    machines = {m: flask_redis.hgetall(m) for m in room_machines}
    num_rows = max([int(machines[m]['row']) for m in machines])
    num_cols = max([int(machines[m]['col']) for m in machines])

    num_machines = len(machines.keys())
    num_used = 0

    rows = []
    uuns = set()

    cascaders = get_cascaders()
    cascaders_here = set()

    for r in range(0, num_rows+1):
        unsorted_cells = []
        for c in range(0, num_cols+1):
            default_cell = {'hostname': None, 'col': c, 'row': r}
            cell = [v for (k, v) in machines.items() if int(v['row']) == r and int(v['col']) == c]
            if not cell:
                cell = default_cell
            else:
                cell = cell[0]

            try:
                if cell['user'] is not "" or cell['status'] == "offline":
                    num_used += 1
            except Exception:
                pass

            if 'user' in cell:
                if cell['user'] == "":
                    del cell['user']
                else:
                    uun = find_cascader(cascaders, cell['user'])
                    if uun:
                        cascaders_here.add(uun)
                        cell["cascader"] = uun
                    # else:
                        # del cell["cascader"]

                    uun = current_user.get_friend(cell['user'])
                    if uun:
                        uuns.add(uun)
                        cell["user"] = uun
                    else:
                        cell["user"] = "-"

            unsorted_cells.append(cell)

        cells = unsorted_cells
        rows.append(cells)

    uuns.update(cascaders_here)

    uun_names = ldap.get_names(list(uuns))

    for y in range(len(rows)):
        for x in range(len(rows[y])):
            cell = rows[y][x]
            if "user" in cell:
                uun = cell["user"]
                if uun in uun_names:
                    rows[y][x]["friend"] = uun_names[uun]

            if "cascader" in cell:
                uun = cell["cascader"]
                if uun in uun_names:
                    rows[y][x]["cascader"] = uun_names[uun]

    num_free = num_machines - num_used

    low_availability = num_free <= 0.3 * num_machines

    last_update = float(flask_redis.get("last-update"))

    # Annotate friends with "here" if they are here
    room_key = room['key']
    friends = get_friend_rooms()
    friends_here, friends_elsewhere = (0, 0)
    for i in range(len(friends)):
        if friends[i]['room_key'] == room_key:
            friends[i]['here'] = True
            friends_here += 1
        else:
            friends_elsewhere += 1
    
    return {
        "friends"          : friends,
        "friends_here_count": friends_here,
        "friends_elsewhere_count": friends_elsewhere,
        "cascaders_here_count": len(cascaders_here),
        "cascaders_elsewhere_count": get_cascader_elsewhere_count(cascaders, which_room),
        "room"             : room,
        "rows"             : rows,
        "num_free"         : num_free,
        "num_machines"     : num_machines,
        "low_availability" : low_availability,
        "last_update"      : last_update
    }


def rooms_list():
    """Returns a tuple of (name, uun) (TODO: swap order)"""
    rooms = list(flask_redis.smembers("forresthill-rooms"))
    rooms.sort()
    for i in range(len(rooms)):
        room = rooms[i]
        rooms[i] = (room, flask_redis.hget(room, "name"))

    return rooms

def room_machines(which):
    machines = flask_redis.lrange(which + "-machines", 0, -1)
    return machines

def get_friends():
    friends = flask_redis.smembers(current_user.get_username() + "-friends")
    friends = list(friends)

    with ldap.conn() as ldap_conn:
        friend_names = ldap.get_names_bare(friends, ldap_conn)

        for i in range(len(friends)):
            uun = friends[i]
            friend = uun

            if uun in friend_names:
                friend = friend_names[uun]

            friends[i] = (friend, uun)
    return friends

def get_friend_rooms():
    rooms = map(lambda name: flask_redis.hgetall(name), flask_redis.smembers("forresthill-rooms"))
    rooms = sorted(rooms, key=lambda x: x['key'])

    friends_rooms = set()
    if current_user.is_authenticated:
        for room in rooms:
            room_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
            for machineName in room_machines:
                machine = flask_redis.hgetall(machineName)
                if current_user.has_friend(machine['user']):
                    uun = current_user.get_friend(machine['user'])
                    friends_rooms.add((uun, room['key'], room['name']))
        friends_rooms = list(friends_rooms)

        # uun -> name
        names = ldap.get_names([f[0] for f in friends_rooms])
        for i in range(len(friends_rooms)):
            uun, b, c = friends_rooms[i]
            if uun in names:
                friends_rooms[i] = {
                    'uun': uun,
                    'name': names[uun],
                    'room_key': b,
                    'room_name': c
                }

        friends_rooms.sort(key=lambda x: x['name'])

    return friends_rooms

@app.route("/")
def index():
    if current_user.is_anonymous:
        return redirect("/about")

    return redirect("/site/6.06")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/site/<which>', methods=['GET', 'POST'])
@login_required
def site(which):
    default = "drillhall"
    if which == "":
        which = default

    room = flask_redis.hgetall(str(which))
    if room == {}:
        return '404'
        
    return render_template('site.html',
                           room_key=room['key'])

# WARNING!!!! THIS METHOD IS UNAUTHENTICATED!!!!!
@app.route('/api/refresh')
def refresh_data():
    """
    Returns a new update
    """
    default = "drillhall"
    which = request.args.get('site', '')

    # SENSITIVE CODE!!!!
    # THIS IS_ANONYMOUS CHECK IS WHAT GUARDS
    # AGAINST NON-LOGGED IN ACCESS
    is_demo = True
    if current_user.is_anonymous or which == "":
        this = get_demo_json()
    else:
        try:
            this = map_routine(which)
            is_demo = False
        except KeyError:
            this = get_demo_json()

    resp = make_response(jsonify(this))
    if not is_demo:
        resp.cache_control.max_age = 60

    return resp

@app.route("/login", methods=['GET'])
def login():
    url = "https://weblogin.inf.ed.ac.uk/cosign-bin/cosign.cgi?cosign-betterinformatics.com&" + request.url_root
    return redirect(url + request.args.get('next', '/'))


@app.route("/flip_dnd", methods=['POST'])
@login_required
def flip_dnd():
    current_user.set_dnd(not current_user.get_dnd())
    return redirect(request.form.get('next', '/'))


@app.route("/api/cascaders")
@login_required
def route_get_cascaders():
    if current_user.is_disabled:
        return jsonify([])

    cascaders = get_cascaders()

    rooms = map(lambda name: flask_redis.hgetall(name), flask_redis.smembers("forresthill-rooms"))
    result = []

    for room in rooms:
        room_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
        for machineName in room_machines:
            machine = flask_redis.hgetall(machineName)
            if machine['user']:
                uun = find_cascader(cascaders, machine['user'])
                if uun:
                    result.append({
                        'uun': uun,
                        'room': room['name'],
                    })

    uuns = [f['uun'] for f in result]

    # uun -> name
    names = ldap.get_names(uuns)

    # uun -> tagline
    taglines = flask_redis.hmget("cascaders.taglines", uuns)

    for i in range(len(result)):
        uun = result[i]['uun']
        if uun in names:
            result[i]['name'] = names[uun]
        result[i]['tagline'] = taglines[i]

    return jsonify(result)

@app.route("/api/cascaders/me", methods=['POST'])
@login_required
def route_post_cascaders():
    # Tagline, enabled
    content = request.json

    enabled = content['enabled']
    tagline = content["tagline"][:100]

    current_user.cascade(enabled, tagline)

    return jsonify({"success": True})

@app.route("/api/cascaders/me", methods=['GET'])
@login_required
def route_get_cascaders_info():
    uun = current_user.get_username()

    return jsonify({
        "enabled": flask_redis.sismember("cascaders.users", uun),
        "tagline": flask_redis.hget("cascaders.taglines", uun),
    })

@app.route("/logout")
def logout():
    resp = make_response(redirect(request.args.get('next','/')))
    resp.set_cookie("cosign-betterinformatics.com", "", domain="betterinformatics.com", expires=0)
    return resp

@app.route("/api/rooms")
@app.route("/api/rooms/<which>")
def rooms(which=""):
    if not which:
        return jsonify({'rooms':rooms_list()})
    else:
        if which == "all":
            which = ",".join([r[0] for r in rooms_list()])
        machines = []
        for room in which.split(","):
            machines.extend(room_machines(room))
        return jsonify({"machines":machines})
    

@app.route('/api/update_schema', methods=['POST'])
def update_schema():
    content = request.json

    try:
        key = content['callback-key']
    except Exception:
        key = ""

    if key not in flask_redis.lrange("authorised-key", 0, -1):
        # HTTP 401 Not Authorised
        print("******* CLIENT ATTEMPTED TO USE BAD KEY *******")
        raise APIError("Given key is not an authorised API key")

    try:
        sheetInput = content['machines']
    except Exception:
        raise APIError("no machines?")

    try:
        resetAll = content['resetAll'] == True
    except Exception:
        raise APIError("Expected resetAll key")

    try:
        dropOnly = content['dropOnly'] == True
    except Exception:
        raise APIError("Expected dropOnly key")

    roomKeys = ['site', 'key', 'name']

    pipe = flask_redis.pipeline()
    sites = defaultdict(list)

    for sheet in sheetInput:
        preader = csv.reader(sheet['csv'].split('\r\n'), delimiter=',')

        room = {}
        machines = []

        for rownumber, row in enumerate(preader):
            for colnumber, cell_value in enumerate(row):
                # handle header rows first
                if rownumber == 0:
                    if colnumber < len(roomKeys):
                        expected = roomKeys[colnumber]
                        if expected != cell_value:
                            raise APIError("[Sheet %s] Invalid header '%s' in cols[%s], expected '%s" % (sheet['name'], cell_value, colnumber, expected))
                    continue
                elif rownumber == 1:
                    if colnumber >= len(roomKeys):
                        continue
                    if cell_value == "":
                        raise APIError("[Sheet %s] Invalid value in col[%s] row[%s], expected non-empty string" % (sheet['name'], colnumber, rownumber))
                    colName = roomKeys[colnumber]
                    room[colName] = cell_value
                    continue
                elif rownumber == 2:
                    if cell_value != "":
                        raise APIError("[Sheet %s] Invalid value '%s' in rows[%s], expected empty row" % (sheet['name'], cell_value, rownumber))
                    continue

                hostname = cell_value

                if hostname != "" and not dropOnly:
                    machines.append({
                        'hostname': hostname,
                        'col': colnumber,
                        'row': rownumber-3, # -3 required because first 3 rows are headers
                        'user': '',
                        'timestamp': '',
                        'status': 'offline',
                        'site': room['site'],
                        'room': room['key'],
                    })

        # if we aren't resetting the entire schema, reset just this room first
        if not resetAll:
            schema_reset_room(pipe, room['site'], room['key'], dropFromSite=True)

        # if dropping only, continue
        if dropOnly:
            continue

        # add site to list of sites
        pipe.sadd('mapp.sites', room['site'])
        # add room to site
        pipe.sadd(room['site']+'-rooms', room['key'])
        # add room dict
        pipe.hmset(room['key'], room)
        # add room machine listing
        pipe.lpush(room['key'] + '-machines', *map(lambda m: m['hostname'], machines))
        # add each machine
        for m in machines:
            pipe.hmset(m['hostname'], m)

        sites[room['site']].append(room)

    if resetAll:
        schema_reset(site="forresthill")

    pipe.execute()

    return jsonify({'success': True})

"""
    schema_reset completely resets the schema for a site.

    - list site rooms
        - list room machines
            - remove machine entries
        - remove room entry
    - remove site entry

"""
def schema_reset(site):
    siteKey = site + "-rooms"
    pipe = flask_redis.pipeline()

    for room in flask_redis.smembers(siteKey):
        schema_reset_room(pipe, site, room)

    pipe.delete(site)
    pipe.srem("mapp.sites", site)

    pipe.execute()

def schema_reset_room(pipe, site, room, dropFromSite=False):
    roomKey = room+"-machines"
    machines = flask_redis.lrange(roomKey, 0, -1)
    if len(machines) > 0:
        pipe.delete(*machines)
    pipe.delete(roomKey)
    pipe.delete(room)

    if dropFromSite:
        pipe.srem(site+'-rooms', room)


@app.route('/api/update', methods=['POST'])
def update():
    content = request.json

    try:
        key = content['callback-key']
    except Exception:
        key = ""

    if key not in flask_redis.lrange("authorised-key", 0, -1):
        # HTTP 401 Not Authorised
        print("******* CLIENT ATTEMPTED TO USE BAD KEY *******")
        raise APIError("Given key is not an authorised API key") 

    pipe = flask_redis.pipeline()
    
    try:
        for machine in content['machines']:
            host   = machine['hostname']
            user   = machine['user']
            ts     = machine['timestamp']
            status = machine['status']

            pipe.hset(host, "user", user)
            pipe.hset(host, "timestamp", ts)
            pipe.hset(host, "status", status)

    except Exception:
        print("Malformed JSON content")
        raise APIError("Malformed JSON content", status_code=400)

    pipe.set("last-update", time.time())
    pipe.execute()

    return jsonify(status="ok")

@app.route("/api/update_available", methods=['POST'])
@login_required
def update_available():
    content = request.json
    date_format = "%Y-%m-%dT%H:%M:%S.%f"
    
    try:
        client_time = float(content['timestamp'])
    except Exception as e:
        raise APIError("Malformed JSON POST data", status_code=400)

    last_update = float(flask_redis.get("last-update"))
    user_behind = client_time < last_update

    return jsonify(status=str(user_behind))

@app.route("/api/friends", methods=['GET', 'POST'])
@login_required
def friends():
    if request.method == "POST":
       formtype = request.form.get('type')
       if formtype == "del":
           remove_friends = request.form.getlist('delfriends[]')
           flask_redis.srem(current_user.get_username() + "-friends", *remove_friends)
       elif formtype == "add":
           add_friend = request.form.get('uun')

           #if(re.match("^[A-Za-z]+\ [A-Za-z]+$", add_friend) == None):
           #    raise APIError("Friend name expected in [A-z]+\ [A-z]+ form.", status_code=400)
           flask_redis.sadd(current_user.get_username() + "-friends", add_friend)

    friends = get_friends()
    friends = map(lambda p: ("%s (%s)" % (p[0], p[1]), p[1]), friends)

    friends = sorted(friends, key=lambda s: s[0].lower())

    return jsonify(friendList=friends) #Set up for ajax responses


@app.route("/api/search", methods=['GET'])
@login_required
def search_friends():
    name = request.args.get('name', '')
    if len(name) < 2:
        return jsonify(people=[])

    people = sorted(ldap.search_name(name), key=lambda p: p['name'].lower())
    friends = get_friends()

    for person in people:
        if (person['name'], person['uun']) in friends:
            person['friend'] = True

    return jsonify(people=people) #Set up for ajax responses

    
@app.route("/demo")
def demo():
    return render_template(
        "site.html",
        room_key="Demo"
    )

def get_demo_friends():
    return [
        {
            'name': 'gryffindor',
            'room_key': 'godric\'s-hollow',
            'room_name': 'Godric\'s Hollow',
        },
        {
            'name': 'moony',
            'room_key': 'common-room',
            'room_name': 'Common Room',
            'here': True,
        },
        {
            'name': 'padfoot',
            'room_key': 'common-room',
            'room_name': 'Common Room',
            'here': True,
        },
        {
            'name': 'prongs',
            'room_key': 'common-room',
            'room_name': 'Common Room',
            'here': True,
        },
        {
            'name': 'wormtail',
            'room_key': 'common-room',
            'room_name': 'Common Room',
            'here': True,
        },
    ]

def get_demo_json():
    return {
        'friends': get_demo_friends(),
        'friends_here_count': 4,
        'friends_elsewhere_count': 1,
        'cascaders_here_count': 7,
        'cascaders_elsewhere_count': 0,
        'room':{"name":"Mapp Demo", "key":"demo"},
        'rows':[
            [
                {},
                {"hostname":"dish", "status": "offline"},
                {"hostname":"paulajennings", "status": "online"},
                {},{},{},{},{}
            ],[
                {"hostname":"dent", "status": "online"},
                {"hostname":"prefect", "status": "online"},
                {"hostname":"slartibartfast", "user":" ","friend":"moony"},
                {"hostname":"random", "user":" ","friend":"wormtail"},
                {"hostname":"colin", "status": "offline"},
                {},
                {"hostname":"marvin", "status": "online"},
                {"hostname":"vogon", "status": "online"}
            ],[
                {"hostname":"beeblebrox", "user":" ","friend":"padfoot"},
                {"hostname":"trillian", "user":" "},
                {"hostname":"agrajag", "status": "unknown"},
                {"hostname":"krikkit", "user":" "},
                {"hostname":"almightybob", "status": "online"},
                {},
                {"hostname":"jynnan", "user":" "},
                {"hostname":"tonyx", "status": "offline"}
            ],[
                {},{},{},
                {"hostname":"eddie", "status": "offline"},
                {"hostname":"fenchurch", "user":" "},
                {},{},{}
            ],[
                {},{},{},
                {"hostname":"anangus", "status": "offline"},
                {"hostname":"benjy", "user":" ","friend":"prongs"},
                {},{},{}
            ]
        ],
        'num_machines':20,
        'num_free':6,
        'low_availability':False,
        'last_update':"1998-05-02 13:37"
    }
