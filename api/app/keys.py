from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from app.deps import worker_required, admin_required, get_redis

import logging
import redis
import os
import secrets

router = APIRouter()

class KeyCreate(BaseModel):
    name: str|None = None
    value: str|None = None

class KeyEdit(BaseModel):
    name: str|None = None
    value: str|None = None

# CRUD keys:
# by default only admins can list / write / delete keys,
# but they're readable by workers
@router.get("/")
def get_keys(request: Request, authed_user=Depends(admin_required), redis_client=Depends(get_redis)):
    # return list of keys
    users = redis_client.smembers("keys")
    return {'status': 'success', 'keys': list(users)}

@router.post("/")
def post_keys(key: KeyEdit, request: Request, authed_user=Depends(admin_required), redis_client=Depends(get_redis)):
    # generate id and set name -> id mapping
    key_id = str(uuid.uuid4())
    success = redis_client.set(f"key_name:{key.name}", key_id, nx=True)
    if not success:
        raise HTTPException(status_code=400, detail="Name already in use.")
    # set key and add it
    redis_client.hset(f"key:{key_id}", mapping={
        "name": key.name,
        "value": key.value
    })
    redis_client.sadd("keys", key_id)
    # return key_id
    return {"status": "success", "key_id": key_id}

@router.get("/{id}")
def get_key(id: str, request: Request, authed_user=Depends(worker_required), redis_client=Depends(get_redis)):
    key_data = redis_client.hgetall(f"key:{id}")
    if not key_data:
        raise HTTPException(status_code=404, detail="Key with ID not found.")
    return {"status": "success", "key": key_data}

@router.patch("/{id}")
def patch_key(id: str, key: KeyEdit, request: Request, authed_user=Depends(admin_required), redis_client=Depends(get_redis)):
    key_data = redis_client.hgetall(f"key:{id}")
    if not key_data:
        raise HTTPException(status_code=404, detail="Key with ID not found.")
    if key.name:
        # create new name record
        success = redis_client.set(f"key_name:{key.name}", id, nx=True)
        if not success:
            raise HTTPException(status_code=400, detail="Key name already in use.")
        # set name
        redis_client.hset(f"key:{id}", "name", key.name)
        # delete old name record
        if not (name := key_data.get("name")):
            logging.error(f"Malformed key record with no name with id '{id}'")
            raise HTTPException(status_code=500, detail="Malformed key record without name.")
        redis_client.delete(f"key_name:{name}")
    if key.value:
        redis_client.hset(f"key:{id}", "value", key.value)
    return {"status": "success"}

@router.delete("/{id}")
def delete_key(id: str, request: Request, authed_user=Depends(admin_required), redis_client=Depends(get_redis)):
    # check key actually exists
    key_data = redis_client.hgetall(f"key:{id}")
    if not key_data:
        raise HTTPException(status_code=404, detail="Key with ID not found.")
    redis_client.delete(f"key:{id}")
    # remove from list
    redis_client.srem("keys", id)
    # try to delete name mapping record
    if not (name := key_data.get("name")):
        logging.error(f"Malformed key record with no name with id '{id}'")
        raise HTTPException(status_code=500, detail="Malformed key record with not name.")
    redis_client.delete(f"key_name:{name}")
    return {"status": "success"}


