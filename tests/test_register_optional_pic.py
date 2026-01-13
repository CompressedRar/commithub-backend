from models.User import Users, User


def test_register_without_profile_picture(db_session):
    user_data = {
        "first_name": "Picless",
        "middle_name": "A",
        "last_name": "User",
        "position": 1,
        "department": 1,
        "role": "faculty",
        "email": "picless@example.com",
    }

    res, status = Users.add_new_user(user_data, None)

    assert status == 200

    # verify user exists and profile_picture_link is None (backend uses default display)
    u = User.query.filter_by(email="picless@example.com").first()
    assert u is not None
    assert u.profile_picture_link is None
