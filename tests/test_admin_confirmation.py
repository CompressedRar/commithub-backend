import jwt
from unittest.mock import patch
from models.AdminConfirmation import AdminConfirmation


def test_verify_admin_password_returns_token(client, db_session, create_user):
    # create an admin user
    user = create_user(role="administrator", password="hashed")

    # sign a token using the secret expected by token_required
    token = jwt.encode({"id": user.id, "role": "administrator"}, "priscilla", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("routes.Auth.PasswordHasher.verify") as mock_verify:
        mock_verify.return_value = True

        res = client.post(
            "/api/v1/auth/verify-admin-password",
            json={"password": "secret"},
            headers=headers,
        )

        assert res.status_code == 200
        data = res.get_json()
        assert "confirmation_token" in data

        # ensure db record exists
        conf = AdminConfirmation.query.filter_by(user_id=user.id, token=data["confirmation_token"]).first()
        assert conf is not None
        assert conf.used == False
