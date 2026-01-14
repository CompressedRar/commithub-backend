import jwt
from unittest.mock import patch
from models.AdminConfirmation import AdminConfirmation


def test_settings_patch_requires_confirmation(client, db_session, create_user):
    # create an admin user
    user = create_user(role="administrator", password="hashed")

    # create a confirmation token
    token_conf = AdminConfirmation.create_for_user(user.id, minutes=10)

    # sign a token using the secret expected by permissions decorator
    token = jwt.encode({"id": user.id, "role": "administrator"}, "priscilla", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}", "X-Admin-Confirmation": token_conf}

    # mock the actual service update to isolate auth/confirmation behavior
    with patch("routes.Settings.System_Settings_Service.update_settings") as mock_update:
        mock_update.return_value = ({"message": "ok"}, 200)

        res = client.patch(
            "/api/v1/settings/",
            json={"some_setting": "new_value"},
            headers=headers,
        )

        assert res.status_code == 200
        data = res.get_json()
        assert data["message"] == "ok"


def test_permissions_has_permission():
    from utils.permissions import has_permission

    assert has_permission("administrator", "settings.edit")
    assert has_permission("administrator", "settings.view")
    assert not has_permission("faculty", "settings.edit")


def test_get_settings_permission_enforced(client, db_session, create_user):
    # faculty should be forbidden
    user = create_user(role="faculty")
    token = jwt.encode({"id": user.id, "role": "faculty"}, "priscilla", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/settings/", headers=headers)
    assert res.status_code == 403


def test_get_settings_admin_allowed(client, db_session, create_user):
    user = create_user(role="administrator")
    token = jwt.encode({"id": user.id, "role": "administrator"}, "priscilla", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("routes.Settings.System_Settings_Service.get_settings") as mock_get:
        mock_get.return_value = ({"message": "ok"}, 200)
        res = client.get("/api/v1/settings/", headers=headers)
        assert res.status_code == 200
        assert res.get_json()["message"] == "ok"
