from map import app, flask_redis, ldap

from flask import render_template, request, jsonify, redirect
from flask.ext.login import login_user, logout_user, login_required


@app.route('/')
@login_required
def index():
    room = flask_redis.hgetall("drillhall")
    dh_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
    machines = {m: flask_redis.hgetall(m) for m in dh_machines}
    num_rows = max([int(machines[m]['row']) for m in machines])
    num_cols = max([int(machines[m]['col']) for m in machines])

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
            unsorted_cells.append(cell)

        cells = unsorted_cells
        rows.append(cells)

    return render_template('index.html', room=room, rows=rows)


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


@app.route("/who")
def whois():
    dh_machines = flask_redis.lrange("drillhall-machines", 0, -1)
    machines = {m: flask_redis.hgetall(m) for m in dh_machines}

    return jsonify(users=[v['user'] for (k, v) in machines.iteritems() if "user" in v])


@app.route('/update', methods=['POST'])
def update():
    content = request.json
    host = content['hostname']
    user = content['user']
    ts = content['timestamp']
    active = content['active']

    pipe = flask_redis.pipeline()
    pipe.hset(host, "user", user)
    pipe.hset(host, "timestamp", ts)
    pipe.hset(host, "active", active)
    pipe.execute()

    return jsonify(status="ok")
