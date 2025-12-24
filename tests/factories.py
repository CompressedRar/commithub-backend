from models.User import User
from app import db
import pytest


@pytest.fixture
def create_user(**kwargs):
    user = User(
        first_name=kwargs.get("first_name", "John"),
        last_name=kwargs.get("last_name", "Doe"),
        email=kwargs.get("email", "john@example.com"),
        password=kwargs.get("password", "hashed"),
        role=kwargs.get("role", "faculty"),
        account_status=kwargs.get("account_status", 1),
        department_id=kwargs.get("department_id", 1),
        position_id=kwargs.get("position_id", 1)
    )
    db.session.add(user)
    db.session.commit()
    return user
