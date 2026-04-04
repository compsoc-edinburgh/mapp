
from functools import wraps
from fastapi import Depends, HTTPException, Request
from passlib.context import CryptContext

import logging
import redis
import os

redis_client = redis.Redis(decode_responses=True)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_redis():
    return redis_client

def get_pwd_context():
    return pwd_context

def rate_limit(key_prefix: str, max_requests: int, window_seconds: int):
    """
    Usage:
        @app.post("/auth/login")
        def login(user: UserLogin, request: Request):
            rate_limit("login", 10, 60)(request, identifier=user.username)
            ...
    """
    def check(request: Request, identifier: str):
        key = f"rl:{key_prefix}:{identifier}"
        now = time.time()
        window_start = now - window_seconds

        pipe = redis_client.pipeline()
        # Drop entries outside the window
        pipe.zremrangebyscore(key, "-inf", window_start)
        # Count remaining entries (requests in the current window)
        pipe.zcard(key)
        # Record this attempt with a unique member so simultaneous requests
        # with the same timestamp don't collide and get deduplicated.
        member = f"{now:.6f}-{secrets.token_hex(4)}"
        pipe.zadd(key, {member: now})
        # Auto-expire the key so Redis doesn't accumulate stale rate-limit sets.
        pipe.expire(key, window_seconds)
        _, count, *_ = pipe.execute()

        if count >= max_requests:
            # Compute when the oldest entry in the window will fall out.
            oldest = redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            logging.warning(
                "Rate limit hit: prefix=%s identifier=%s count=%d limit=%d",
                key_prefix, identifier, count, max_requests,
            )
            raise HTTPException(
                status_code=429,
                detail="Too many requests, please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return check

def get_client_ip(request: Request) -> str:
    """Return the best-guess client IP, honouring X-Forwarded-For if present."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# some helpful authorization decorators
def get_current_user(request: Request):
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Authorization required.")

    user_data = redis_client.hgetall(f"user:{session_user_id}")
    if not user_data:
        logging.error(f"Valid session for {session_user_id=}, but user does not exist.")
        raise HTTPException(status_code=401, detail="Invalid session, user does not exist.")

    return session_user_id, user_data

def require_roles(*allowed_roles: str):
    async def dependency(request: Request):
        user_id, user_data = get_current_user(request)

        if user_data.get("account_class") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access resource."
            )

        return user_id, user_data  # optional: return useful info

    return dependency

admin_required = require_roles("admin")
worker_required = require_roles("admin", "worker")
user_required = require_roles("admin", "worker", "user")


