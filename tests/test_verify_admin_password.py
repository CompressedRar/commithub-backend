from factories import create_user
from models.User import Users
from unittest.mock import patch


def test_verify_admin_password_success(client, db_session, create_user):
    user = create_user(email="admin@test.com", role="administrator", password="hashed")
    token = Users.generate_token(user.to_dict())

    with patch("models.Users.PasswordHasher.verify") as mock_verify:
        mock_verify.return_value = True
        res = client.post("/api/v1/auth/verify-admin-password", json={"password": "secret"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json.get("message") == "Verified"


def test_verify_admin_password_wrong(client, db_session, create_user):
    user = create_user(email="admin2@test.com", role="administrator", password="hashed")
    token = Users.generate_token(user.to_dict())

    with patch("models.Users.PasswordHasher.verify") as mock_verify:
        mock_verify.side_effect = Exception("mismatch")
        res = client.post("/api/v1/auth/verify-admin-password", json={"password": "wrong"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert "Invalid password" in res.json.get("error")
