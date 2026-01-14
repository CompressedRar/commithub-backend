import jwt
from unittest.mock import patch


def test_department_ipcr_forbidden_for_faculty(client, db_session, create_user):
    user = create_user(role="faculty")
    token = jwt.encode({"id": user.id, "role": "faculty"}, "priscilla", algorithm="HS256")

    res = client.get(f"/api/v1/department/ipcr/{1}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_department_ipcr_allowed_for_head(client, db_session, create_user):
    user = create_user(role="head")
    token = jwt.encode({"id": user.id, "role": "head"}, "priscilla", algorithm="HS256")

    with patch("routes.Department.Department_Service.get_all_department_ipcr") as mock_ipcr:
        mock_ipcr.return_value = ({"items": []}, 200)
        res = client.get(f"/api/v1/department/ipcr/{1}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.get_json()["items"] == []