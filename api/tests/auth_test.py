from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_full():
    # create user
    response = client.post("/users", json={
        "username": "z3r0d4y",
        "password": "s3cur3_p455w0rd",
        "student_id": "s123456"
    })
    assert response.status_code == 200

    # login as user
    response = client.post("/auth/login", json={
        "username": "z3r0d4y",
        "password": "s3cur3_p455w0rd",
    })
    assert response.status_code == 200 and response.json().get("user_id")
    user_id = response.json()["user_id"]

    # get user information
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json().get("user")
    assert response.json().get("user").get("username") == "z3r0d4y" and response.json().get("user").get("student_id") == "s123456"
    assert not response.json().get("user").get("password_hash")

    # edit user information
    response = client.patch(f"/users/{user_id}", json={
        "username": "n07_z3r0d4y",
    })
    assert response.status_code == 200

    # check updated user information is correct
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json().get("user")
    assert response.json().get("user").get("username") == "n07_z3r0d4y" and response.json().get("user").get("student_id") == "s123456"
    assert not response.json().get("user").get("password_hash")

    # try to edit student_id (should fail)
    response = client.patch(f"/users/{user_id}", json={
        "student_id": "not_my_student_id"
    })
    assert response.status_code == 403

    # delete user
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200

    # try to login as user (should fail)
    response = client.post("/auth/login", json={
        "username": "z3r0d4y",
        "password": "s3cur3_p455w0rd",
    })
    assert response.status_code == 400

    # create user again (should succeed)
    response = client.post("/users", json={
        "username": "z3r0d4y",
        "password": "m0r3_s3cur3_p455w0rd",
        "student_id": "s654321"
    })
    assert response.status_code == 200

    # login as user
    response = client.post("/auth/login", json={
        "username": "z3r0d4y",
        "password": "m0r3_s3cur3_p455w0rd",
    })
    assert response.status_code == 200 and response.json().get("user_id")
    user_id = response.json()["user_id"]

    # get user info again
    response = client.get(f"/users/{user_id}")
    assert response.json().get("user")
    assert response.json().get("user").get("username") == "z3r0d4y" and response.json().get("user").get("student_id") == "s654321"
    assert not response.json().get("user").get("password_hash")

    # delete user
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
