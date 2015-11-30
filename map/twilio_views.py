from map import flask_redis, app, braintree
from flask import request, redirect, render_template
import random
import twilio.twiml

# Try adding your own number to this list!

dh_machines = flask_redis.lrange("drillhall-machines", 0, -1)
machines = {m: flask_redis.hgetall(m) for m in dh_machines}
num_rows = max([int(machines[m]['row']) for m in machines])
num_cols = max([int(machines[m]['col']) for m in machines])
people_in_labs = [v['user'] for (k, v) in machines.iteritems() if "user" in v]

rows = []
for r in xrange(0, num_rows + 1):
    unsorted_cells = []
    for c in xrange(0, num_cols + 1):
        default_cell = {'hostname': None, 'col': c, 'row': r}
        cell = [v for (k, v) in machines.iteritems() if int(v['row']) == r and int(v['col']) == c]
        if not cell:
            cell = default_cell
        else:
            cell = cell[0]
        unsorted_cells.append(cell)
    cells = unsorted_cells
    rows.append(cells)
allMachines = ['venosa', 'trento', 'pavia', 'orlofsky', 'mereb', 'radames', 'vervecelli', 'ascoli', 'tivoli',
               'wideopen', 'twite', 'swanland', 'enna', 'gosforth', 'albenga', 'hart', 'stork', 'brujon', 'pharoah',
               'combeferre', 'remendado', 'escamillo', 'micaela', 'lavello', 'marsala', 'mantua', 'spoleto',
               'falconara', 'amelia', 'parrot', 'wigton', 'falcon', 'raven', 'ciociosan', 'lilas', 'roxanne',
               'yakuside', 'lesgles', 'goro', 'daae', 'owl', 'owl', 'penguin', 'lodi', 'luni', 'palermo', 'falke',
               'scarpia', 'cavaradossi', 'amneris', 'babet', 'amanasro', 'ceilingcat', 'danicaire', 'lowick',
               'seascale', 'ostiglia', 'allonby', 'yvan', 'claquesous', 'montparnarsse', 'tosca', 'spoletta',
               'enjolras', 'nehebka', 'parma', 'carmen', 'messina', 'rosilande', 'gabriel', 'aida', 'frosch',
               'thenardier', 'zoser', 'pollenzo', 'palestrina', 'ravenna', 'bechstein', 'mocha', 'bluthner', 'dove',
               'scarecrow', 'giry', 'savona', 'vicenza', 'velma', 'avellino', 'morales', 'pontremoli', 'velletri',
               'angelotti', 'joly', 'courfeyrac', 'crow', 'giudicelli', 'pipit']

callers = {
    "+447729837696": "James Friel",
    "+447578908062": "Angus Pearson",
}

friends = {
    "Angus Pearson": ["James Friel", "Andrew Smith", "William Mathewson"],
    "James Friel": ["Angus Pearson", "Hugh McGrade", "Andrew Smith", "Lisa Xie"],
    "Harry Reeder": ["Angus Pearson", "James Friel"]
}


def friendCount(person):
    friendcount = 0
    for i in range(0, len(friends.get(person))):
        if friends.get(person)[i] in people_in_labs:
            friendcount += 1
    return friendcount


def space(inpt, person):
    # find active friends
    list_of_active_friends = []
    person_machines = []
    for i in range(0, len(friends.get(person))):
        if friends.get(person)[i] in people_in_labs:
            list_of_active_friends.append(friends.get(person)[i])
            person_machines.append(
                [v for (k, v) in machines.iteritems() if "user" in v and v['user'] == friends.get(person)[i]])

        # l3 = [x for x in l1 if x not in l2]
    empty_pcs = [x for x in allMachines if x not in person_machines]  # check that works
    # find out where friends are
    # print person_machines
    if inpt == "avoid" or inpt == "Avoid":
        return random.choice(empty_pcs)
    if inpt == "find" or inpt == "Find":
        return random.choice(empty_pcs)
        # find a computer close by
    return "NONE becuase you can't send a text correctly"


print space("avoid", "Angus Pearson")


@app.route("/respond", methods=['GET', 'POST'])
def hello_monkey():
    message = "Error: we fucked up hard"
    """Respond and greet the caller by name."""
    if request.method == "POST":
        from_number = request.values.get('From')
        body = request.values.get('Body')
        if from_number in callers:
            print("Hitter")
            if body == "avoid" or body == "Avoid":
                hostname = space("avoid", callers.get(from_number));
                message = "To Escape your friends, try " + hostname
            elif body == "find" or body == "Find":
                message = "Dun Dun Dun"  # for testing purposes
                hostname = space("find", callers.get(from_number))
                friend = friendCount(callers.get(from_number))
                if friend == 0:
                    message = "None of your mates are in the lab, sit anywhere you like, loser"
                else:
                    message = str(friend) + " of your friends are in The Drill Hall, try " + hostname
            elif body == "busy" or body == "Busy":
                if people_in_labs > 15:
                    message = "It's pretty busy in here"
                else:
                    message = "It's very quiet in here"
            else:
                message = "You Nonce, use the right key words."
        else:
            print("not_registered")
            message = "Mate, you're not a registered user. Do you you even go here blud?"  # if the user does not have a profile
        resp = twilio.twiml.Response()
        resp.message(message)
        # print(message)
        # print(resp)
        # print(from_number)

        return str(resp)


@app.route("/carly", methods=['GET', 'POST'])
def hello_monkey1():
    """Respond to incoming requests."""
    from_number = request.values.get('FROM')
    if from_number in callers:
        name = callers.get(from_number)
    if people_in_labs > 15:
        pepnum = " everybody is in here. It's rammed"
    else:
        pepnum = " nobody is in here "
    resp = twilio.twiml.Response()
    resp.say("All right" + name + " there is currently " + pepnum)

    return str(resp)


# Here be Braintree Dragons

@app.route("/reserve/<machinename>")
def client_token(machinename):
    cltoken = braintree.ClientToken.generate()
    return render_template("reserve.html", client_token=cltoken, machine=machinename)


@app.route("/checkout", methods=["POST"])
def create_purchase():
    nonce = request.form["payment_method_nonce"]
    machine = request.form["machine"]

    result = braintree.Transaction.sale({
        "amount": "5.00",
        "payment_method_nonce": nonce
    })

    if result.is_success:
        flask_redis.sadd('reserved-machines', machine)

    return redirect("/")
