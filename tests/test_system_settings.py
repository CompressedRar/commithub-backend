import pytest
from datetime import date, timedelta
from app import db
from models.System_Settings import System_Settings, System_Settings_Service


@pytest.fixture
def system_settings(app):
    settings = System_Settings(
        rating_thresholds={
            "outstanding": {"min": 1.30},
            "satisfactory": {"min": 0.90, "max": 1.14}
        }
    )
    db.session.add(settings)
    db.session.commit()
    return settings

def test_get_current_period_planning(system_settings):
    today = date.today()

    system_settings.planning_start_date = today - timedelta(days=1)
    system_settings.planning_end_date = today + timedelta(days=1)

    db.session.commit()

    result = system_settings.get_current_period()
    assert "planning" in result

def test_get_current_period_multiple(system_settings):
    today = date.today()

    system_settings.planning_start_date = today - timedelta(days=1)
    system_settings.planning_end_date = today + timedelta(days=1)

    system_settings.monitoring_start_date = today - timedelta(days=1)
    system_settings.monitoring_end_date = today + timedelta(days=1)

    db.session.commit()

    result = system_settings.get_current_period()
    assert "planning" in result
    assert "monitoring" in result

def test_get_current_period_none(system_settings):
    system_settings.planning_start_date = None
    system_settings.planning_end_date = None

    db.session.commit()

    assert system_settings.get_current_period() is None

def test_to_dict_contains_expected_fields(system_settings):
    data = system_settings.to_dict()

    assert "rating_thresholds" in data
    assert "quantity_formula" in data
    assert "current_phase" in data
    assert isinstance(data, dict)


"""SERVICES DITO """
def test_get_settings_success(app, system_settings):
    with app.app_context():
        response, status = System_Settings_Service.get_settings()

        assert status == 200
        assert response.json["status"] == "success"
        assert "data" in response.json

def test_get_settings_not_found(app):
    with app.app_context():
        response, status = System_Settings_Service.get_settings()

        assert status == 404
        assert response.json["status"] == "error"

def test_update_settings_creates_record(app):
    with app.app_context():
        payload = {
            "rating_thresholds": {"excellent": {"min": 1.4}},
            "current_period": "2025",
            "current_period_id": "OPCR-2025"
        }

        response, status = System_Settings_Service.update_settings(payload)

        assert status == 200
        assert response.json["data"]["current_period"] == "2025"

def test_update_settings_updates_existing(app, system_settings):
    with app.app_context():
        payload = {
            "current_president_fullname": "Juan Dela Cruz"
        }

        response, status = System_Settings_Service.update_settings(payload)

        assert status == 200
        assert response.json["data"]["current_president_fullname"] == "Juan Dela Cruz"

def test_check_if_rating_period_true(app, system_settings):
    today = date.today()

    system_settings.rating_start_date = today - timedelta(days=1)
    system_settings.rating_end_date = today + timedelta(days=1)

    db.session.commit()

    with app.app_context():
        result = System_Settings_Service.check_if_rating_period()
        assert result is True

def test_check_if_rating_period_false(app, system_settings):
    today = date.today()

    system_settings.rating_start_date = today - timedelta(days=10)
    system_settings.rating_end_date = today - timedelta(days=5)

    db.session.commit()

    with app.app_context():
        result = System_Settings_Service.check_if_rating_period()
        assert result is False
