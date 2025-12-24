from factories import create_user


def test_user_to_dict_contains_expected_fields(db_session):
    user = create_user()

    data = user.to_dict()

    assert data["id"] == user.id
    assert data["first_name"] == "John"
    assert data["email"] == "john@example.com"
    assert "avg_performance" in data
    assert "created_at" in data

from models.User import Users
from factories import create_user

def test_check_email_if_exists_found(client, db_session):
    create_user(email="taken@example.com")

    res, status = Users.check_email_if_exists("taken@example.com")

    assert status == 200
    assert res.json["message"] == "Email was already taken."

def test_check_email_if_exists_available(client):
    res, status = Users.check_email_if_exists("free@example.com")

    assert status == 200
    assert res.json["message"] == "Available"

def test_get_user_success(client, db_session):
    user = create_user()

    res, status = Users.get_user(user.id)

    assert status == 200
    assert res.json["id"] == user.id

def test_get_user_not_found(client):
    res, status = Users.get_user(999)

    assert status == 400
    assert "There is no user" in res.json["error"]

from unittest.mock import patch

@patch("models.Users.PasswordHasher.verify")
def test_authenticate_user_success(mock_verify, client, db_session):
    mock_verify.return_value = True

    user = create_user(email="login@test.com", password="hashed")

    login_data = {
        "email": "login@test.com",
        "password": "secret"
    }

    res, status = Users.authenticate_user(login_data)

    assert status == 200
    assert "token" in res.json

@patch("models.Users.PasswordHasher.verify")
def test_authenticate_user_wrong_password(mock_verify, client, db_session):
    mock_verify.return_value = False

    create_user(email="login@test.com", password="hashed")

    login_data = {
        "email": "login@test.com",
        "password": "wrong"
    }

    res, status = Users.authenticate_user(login_data)

    assert status == 400

@patch("models.Users.send_email")
@patch("models.Users.socketio.emit")
@patch("models.Users.Notification_Service.notify_user")
def test_reset_password(
    mock_notify, mock_emit, mock_send, client, db_session
):
    user = create_user()

    res, status = Users.reset_password(user.id)

    assert status == 200
    mock_send.assert_called_once()
    mock_notify.assert_called_once()
