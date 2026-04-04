from fastapi import APIRouter, Request, HTTPException, Depends
from app.users import UserCreate, UserLogin
from pydantic import BaseModel
from email.message import EmailMessage

from app.deps import rate_limit, pwd_context, get_redis, get_pwd_context

import logging
import redis
import os
import secrets
import uuid
import smtplib

router = APIRouter()

class VerificationCode(BaseModel):
    id: str
    code: int

def send_verification_email(user: UserCreate) -> tuple[int, str]:
    # generate secure code
    code = str(secrets.randbelow(1_000_000)).zfill(6)
    # set code in redis
    success = redis_client.set(f"verification_code:{user.student_id}", code, nx=True, ex=600)
    if not success:
        return 400, "Student ID already in use."
    # grab email and password from session
    from_email = os.environ.get("EMAIL")
    if not from_email or not email_password:
        logging.error("EMAIL or EMAIL_PASSWORD environment variables not set, these must be sent to allow email verification.")
        return 500, "Email failed to send, please try again later, or report this to an admin if this continues."
    # create email
    msg = EmailMessage()
    msg["Subject"] = "MAPP Account Verification"
    msg["From"] = from_email
    msg["To"] = f"{user.student_id}@ed.ac.uk"
    msg.set_content(f"""Hello,

    Your verification code for MAPP is {code}. Please use this code to verify your account and
    access services. This code will expire in 10 minutes.

    Thanks,
    BetterInformatics Admins""")
    # send email, backing out if errors occur.
    try:
        with smtplib.SMTP("smtp-relay.gmail.com", 587) as smtp:
            smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"Failed to authenticate with email server.")
        return 500, "Email failed to send, please try again later, or report this to an admin if this continues."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error: {e}")
        return 500, "Email failed to send, please try again later, or report this to an admin if this continues."
    return 200, None

@router.post("/verify")
def auth_verify(code: VerificationCode, request: Request, redis_client=Depends(get_redis)):
    rate_limit("verify", 10, 60)(request, identifier=code.id)
    # grab student id
    student_id = redis_client.hget(f"user:{code.id}", "student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="User doesn't exist.")
    # grab verification code
    valid_code = redis_client.get(f"verification_code:{student_id}")
    if not valid_code:
        raise HTTPException(status_code=400, detail="Code expired or invalid.")
    # check code is correct
    formatted_presented_code = str(code.code).zfill(6)
    if not secrets.compare_digest(valid_code, formatted_presented_code):
        raise HTTPException(status_code=400, detail="Code expired or invalid.")
    # update database
    redis_client.hset(f"user:{code.id}", "account_class", "user")
    redis_client.delete(f"verification_code:{student_id}")
    # return success
    return {"status": "success", "message": "Account verified."}

@router.post("/resend_verification")
def auth_resend(request: Request, redis_client=Depends(get_redis)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authorization required.")
    rate_limit("verify", 1, 60)(request, identifier=user_id)
    pass

# signup as a user (different flow from POST /users, because this requires student id verification)
@router.post("/signup")
def auth_signup(user: UserCreate, request: Request, redis_client=Depends(get_redis), pwd_context=Depends(get_pwd_context)):
    rate_limit("login", 10, 300)(request, identifier=get_client_ip(request))
    # Set user_id, is atomic in redis
    user_id = str(uuid.uuid4()) # https://en.wikipedia.org/wiki/Universally_unique_identifier#Random_UUID_probability_of_duplicates
    success = redis_client.set(f"username:{user.username}", user_id, nx=True)
    if not success:
        raise HTTPException(status_code=400, detail="Username already in use.")
    success = redis_client.set(f"student_id:{user.student_id}", user_id, nx=True)
    if not success:
        raise HTTPException(status_code=400, detail="Student ID already in use.")
    # Try to send the verification email, if this fails, backout gracefully and present useful
    # error
    code, error_message = send_verification_email(user)
    if code != 200:
        redis_client.delete(f"username:{user.username}")
        redis_client.delete(f"student_id:{user.student_id}")
        raise HTTPException(status_code=code, detail=error_message)
    # Hash the password (argon2 includes salts for us)
    hashed = pwd_context.hash(user.password)
    # Add user to database
    redis_client.hset(f"user:{user_id}",
                      mapping={"username": user.username,
                               "password_hash": hashed,
                               "student_id": user.student_id,
                               "account_class": "unverified"})
    redis_client.sadd("users", user_id)
    return {"status": "success", "user_id": user_id, "message": "Must verify account through the email sent to your student ID."}

# Authenticate yourself as a user or worker
@router.post("/login")
def auth_login(user: UserLogin, request: Request, redis_client=Depends(get_redis), pwd_context=Depends(get_pwd_context)):
    rate_limit("login", 10, 60)(request, identifier=user.username)
    # grab user_id from username
    user_id = redis_client.get(f"username:{user.username}")
    if not user_id:
        logging.info(f"Non-existent user '{user.username}' attempted to authenticate.")
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    # grab user entry from database and verify password
    user_data = redis_client.hgetall(f"user:{user_id}")
    if not user_data:
        logging.error(f"Username {user.username} found in usernames, but {user_id} not found in users.")
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    hashed = user_data.get("password_hash")
    if not hashed:
        logging.error(f"User {user_id} found without password_hash.")
        raise HTTPException(status_code=500, detail=f"Corrupted user record.")
    if not pwd_context.verify(user.password, user_data.get("password_hash")):
        logging.info(f"User '{user.username}' failed login attempt with incorrect password.")
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    # if we've reached this point, the user has successfully logged in, so give them a valid session cookie.
    request.session["user_id"] = user_id
    return {'status': 'success', "user_id": user_id}


