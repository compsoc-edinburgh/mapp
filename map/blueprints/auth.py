from flask import Blueprint, make_response, redirect, request

from flask_login import current_user, login_required

bp = Blueprint('auth', __name__)
bp.config.from_object('config')


@bp.route("/login", methods=['GET'])
def login():
    url = ("https://weblogin.inf.ed.ac.uk/cosign-bin/cosign.cgi?cosign-betterinformatics.com&" +
           request.url_root)
    return redirect(url + request.args.get('next', '/'))


@bp.route("/flip_dnd", methods=['POST'])
@login_required
def flip_dnd():
    current_user.set_dnd(not current_user.get_dnd())
    return redirect(request.form.get('next', '/'))


@bp.route("/logout")
def logout():
    resp = make_response(redirect(request.args.get('next', '/')))
    resp.set_cookie("cosign-betterinformatics.com",
                    "",
                    domain="betterinformatics.com",
                    expires=0)
    return resp
