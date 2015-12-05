from map import app, flask_redis, ldap

import hashlib
from flask import render_template, request, jsonify, redirect
from flask.ext.login import login_user, logout_user, login_required, current_user


def map_routine(which_room):
    room = flask_redis.hgetall(str(which_room))
    dh_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
    machines = {m: flask_redis.hgetall(m) for m in dh_machines}
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
                if cell['user'] is not "":
                    num_used += 1
            except Exception:
                pass
            unsorted_cells.append(cell)

        cells = unsorted_cells
        rows.append(cells)

    num_free = num_machines - num_used

    reserved = flask_redis.smembers('reserved-machines')

    return {
        "room"         : room,
        "rows"         : rows,
        "reserved"     : reserved,
        "num_free"     : num_free,
        "num_machines" : num_machines
        }


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    this = map_routine("drillhall")
    return render_template('index.html', room=this['room'], rows=this['rows'], reserved=this['reserved'],
                           num_machines=this['num_machines'],  num_free=this['num_free'])

@app.route('/refresh')
@login_required
def refresh():
    this = map_routine("drillhall")
    return render_template('refresh.xml', room=this['room'], rows=this['rows'], reserved=this['reserved'],
                           num_machines=this['num_machines'],  num_free=this['num_free'])


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        if ldap.check_credentials(request.form['username'], request.form['password']):
            user=ldap.getuser(request.form['username'])
            login_user(user)
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")



class APIKeyNotAuthorised(Exception):
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


@app.errorhandler(APIKeyNotAuthorised)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
    

@app.route('/update', methods=['POST'])
def update():
    content = request.json

    try:
        key    = content['callback-key']
        host   = content['hostname']
        user   = content['user']
        ts     = content['timestamp']
        active = content['active']
    except Exception:
        raise APIKeyNotAuthorised("Malformed JSON POST data", status_code=400)

    if key not in flask_redis.lrange("authorised-key", 0, -1):
        # HTTP 401 Not Authorised
        print "BAD KEY*******"
        raise APIKeyNotAuthorised("Given key is not an authorised API key")

    pipe = flask_redis.pipeline()
    pipe.hset(host, "user", user)
    pipe.hset(host, "timestamp", ts)
    pipe.hset(host, "active", active)
    pipe.execute()

    return jsonify(status="ok")


@app.route("/friends", methods=['GET', 'POST'])
@login_required
def friends():
    if request.method == "POST":
       formtype = request.form.get('type')
       if formtype == "del":
           remove_friends = request.form.getlist('delfriends')
           flask_redis.srem(current_user.get_id() + "-friends", *remove_friends)
       elif formtype == "add":
           add_friend = request.form.get('newfriend')
           flask_redis.sadd(current_user.get_id() + "-friends", add_friend)

    friends = flask_redis.smembers(current_user.get_id() + "-friends")
    friends = list(friends)
    friends.sort()

    return jsonify(friendList=friends) #Set up for ajax responses

