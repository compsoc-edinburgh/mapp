from flask import Blueprint, redirect, render_template

from flask_login import current_user, login_required

from map import flask_redis

bp = Blueprint("views", __name__, template_folder="templates")


@bp.route("/")
def index():
    if current_user.is_anonymous:
        return redirect("/about")

    return redirect("/site/6.06")


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route('/site/<which>', methods=['GET', 'POST'])
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


@bp.route("/demo")
def demo():
    return render_template(
        "site.html",
        room_key="Demo"
    )
