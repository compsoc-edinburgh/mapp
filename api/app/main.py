from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

import logging
import os
import secrets

from app.users import router as users_router
from app.auth import router as auth_router
from app.keys import router as keys_router

# Database:
# verification_code:{student_id} -> {code} (STRING)
# username:{username} -> {user_id} (STRING)
# users: {user_id_0}, {user_id_1}, ... (SET)
# user:{id} (HASH)
#  username
#  password_hash
#  student_id
#  api_key_hash
#  account_class: (one of admin, user, or worker)


app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(0x20) # invalidates sessions on restart, this is ok
)

app.include_router(users_router, prefix="/users")
app.include_router(auth_router, prefix="/auth")
app.include_router(keys_router, prefix="/keys")

# Global contexts

logging.basicConfig(level=logging.INFO)
load_dotenv()



