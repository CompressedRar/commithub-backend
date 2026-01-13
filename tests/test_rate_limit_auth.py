def test_rate_limit_login(client):
    # Allow 5 requests, 6th should be rate limited (429)
    for i in range(5):
        res = client.post("/api/v1/auth/login", data={"email": "noone@example.com", "password": "x"})
    res = client.post("/api/v1/auth/login", data={"email": "noone@example.com", "password": "x"})
    assert res.status_code == 429


def test_rate_limit_verify_otp(client):
    # Allow 10 requests, 11th should be rate limited
    payload = {"email": "noone@example.com", "otp": "000000"}
    for i in range(10):
        res = client.post("/api/v1/auth/verify-otp", json=payload)
    res = client.post("/api/v1/auth/verify-otp", json=payload)
    assert res.status_code == 429


def test_rate_limit_reset_password(client, db_session):
    # Create a user and call reset more than allowed
    from models.User import Users
    from factories import create_user
    user = create_user()
    for i in range(3):
        res, status = Users.reset_password(user.id)
    # calling via route
    res = client.patch(f"/api/v1/users/reset-password/{user.id}")
    assert res.status_code == 429
