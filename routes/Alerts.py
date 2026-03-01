"""
Alert Configuration and Management Routes
Handles alert threshold configuration, KPI management, and alert retrieval
"""
from flask import Blueprint, request, jsonify
from app import db, socketio
from utils.decorators import token_required, log_action
from models.Analytics import PerformanceAlert, PerformanceAlertService, CustomKPI, CustomKPIService
from models.System_Settings import System_Settings, System_Settings_Service
from models.User import Notification
from utils.PerformanceAlerts import PerformanceAlertEngine, CustomKPIMonitor

alerts = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")


# ============================================================
# ALERT CONFIGURATION ENDPOINTS
# ============================================================

@alerts.route("/config", methods=["GET"])
@token_required(allowed_roles=["administrator"])
def get_alert_config():
    """Get current alert threshold configuration"""
    try:
        settings = System_Settings.get_default_settings()
        return jsonify({
            "status": "success",
            "data": {
                "alert_thresholds": settings.alert_thresholds or {},
                "kpi_definitions": settings.kpi_definitions or {}
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/config", methods=["PATCH"])
@token_required(allowed_roles=["administrator"])
@log_action("UPDATE", "ALERTS")
def update_alert_config():
    """Update alert threshold configuration"""
    try:
        data = request.get_json()
        settings = System_Settings.query.first()

        if not settings:
            settings = System_Settings()
            db.session.add(settings)

        # Update alert thresholds
        if "alert_thresholds" in data:
            settings.alert_thresholds = data.get("alert_thresholds", {})

        # Update KPI definitions if provided
        if "kpi_definitions" in data:
            settings.kpi_definitions = data.get("kpi_definitions", {})

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Alert configuration updated successfully",
            "data": {
                "alert_thresholds": settings.alert_thresholds or {},
                "kpi_definitions": settings.kpi_definitions or {}
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# KPI MANAGEMENT ENDPOINTS
# ============================================================

@alerts.route("/kpi/<int:dept_id>", methods=["GET"])
@token_required(allowed_roles=["administrator", "head"])
def get_department_kpis(dept_id):
    """Get all custom KPIs for a department"""
    try:
        kpis = CustomKPIService.get_department_kpis(dept_id)
        return jsonify({
            "status": "success",
            "data": [kpi.to_dict() for kpi in kpis]
        }), 200
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/kpi/<int:dept_id>", methods=["POST"])
@token_required(allowed_roles=["administrator", "head"])
@log_action("CREATE", "KPI")
def create_custom_kpi(dept_id):
    """Create a new custom KPI for a department"""
    try:
        data = request.get_json()

        required_fields = ["kpi_name", "target_value", "alert_threshold"]
        if not all(field in data for field in required_fields):
            return jsonify({
                "status": "error",
                "message": "Missing required fields: kpi_name, target_value, alert_threshold"
            }), 400

        kpi = CustomKPIService.create_kpi(
            department_id=dept_id,
            kpi_name=data.get("kpi_name"),
            target_value=data.get("target_value"),
            alert_threshold=data.get("alert_threshold"),
            description=data.get("description"),
            formula=data.get("formula")
        )

        return jsonify({
            "status": "success",
            "message": "KPI created successfully",
            "data": kpi.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/kpi/<int:kpi_id>", methods=["PATCH"])
@token_required(allowed_roles=["administrator", "head"])
@log_action("UPDATE","KPI")
def update_custom_kpi(kpi_id):
    """Update an existing custom KPI"""
    try:
        data = request.get_json()
        kpi = CustomKPIService.update_kpi(kpi_id, **data)

        if not kpi:
            return jsonify({"status": "error", "message": "KPI not found"}), 404

        return jsonify({
            "status": "success",
            "message": "KPI updated successfully",
            "data": kpi.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/kpi/<int:kpi_id>", methods=["DELETE"])
@token_required(allowed_roles=["administrator", "head"])
@log_action("DELETE","KPI")
def delete_custom_kpi(kpi_id):
    """Delete a custom KPI"""
    try:
        success = CustomKPIService.delete_kpi(kpi_id)

        if not success:
            return jsonify({"status": "error", "message": "KPI not found"}), 404

        return jsonify({
            "status": "success",
            "message": "KPI deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/kpi/<int:kpi_id>/value", methods=["PATCH"])
@token_required(allowed_roles=["administrator", "head"])
@log_action("UPDATE","KPI VALUE")
def update_kpi_value(kpi_id):
    """Update KPI current value and trigger alerts if needed"""
    try:
        data = request.get_json()

        if "current_value" not in data:
            return jsonify({"status": "error", "message": "Missing current_value"}), 400

        result = CustomKPIMonitor.update_kpi_value(
            kpi_id,
            data.get("current_value"),
            socketio=socketio
        )

        return jsonify({
            "status": result["status"],
            "message": result["message"],
            "alerts_generated": result.get("alerts_generated", 0)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# ALERT RETRIEVAL AND MANAGEMENT ENDPOINTS
# ============================================================

@alerts.route("/active", methods=["GET"])
@token_required()
def get_active_alerts(user_id=None):
    """Get all active (unread) alerts for the current user"""
    try:
        from flask_jwt_extended import get_jwt
        payload = get_jwt()
        user_id = payload.get("user_id")

        unread_alerts = PerformanceAlertService.get_user_alerts(user_id, unread_only=True)

        return jsonify({
            "status": "success",
            "data": [alert.to_dict() for alert in unread_alerts]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/history", methods=["GET"])
@token_required()
def get_alert_history():
    """Get all alerts (read and unread) for the current user"""
    try:
        from flask_jwt_extended import get_jwt
        payload = get_jwt()
        user_id = payload.get("user_id")

        all_alerts = PerformanceAlertService.get_user_alerts(user_id, unread_only=False)

        return jsonify({
            "status": "success",
            "data": [alert.to_dict() for alert in all_alerts]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/<int:alert_id>/read", methods=["PATCH"])
@token_required()
def mark_alert_as_read(alert_id):
    """Mark a single alert as read"""
    try:
        alert = PerformanceAlertService.mark_alert_as_read(alert_id)

        if not alert:
            return jsonify({"status": "error", "message": "Alert not found"}), 404

        return jsonify({
            "status": "success",
            "message": "Alert marked as read",
            "data": alert.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/mark-all-read", methods=["PATCH"])
@token_required()
def mark_all_alerts_as_read():
    """Mark all alerts as read for the current user"""
    try:
        from flask_jwt_extended import get_jwt
        payload = get_jwt()
        user_id = payload.get("user_id")

        unread_alerts = PerformanceAlertService.get_user_alerts(user_id, unread_only=True)
        alert_ids = [alert.id for alert in unread_alerts]

        if alert_ids:
            PerformanceAlertService.mark_alerts_as_read(alert_ids)

        return jsonify({
            "status": "success",
            "message": f"Marked {len(alert_ids)} alerts as read"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/<int:alert_id>", methods=["DELETE"])
@token_required()
def delete_alert(alert_id):
    """Delete a specific alert"""
    try:
        success = PerformanceAlertService.delete_alert(alert_id)

        if not success:
            return jsonify({"status": "error", "message": "Alert not found"}), 404

        return jsonify({
            "status": "success",
            "message": "Alert deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# MANUAL ALERT CHECK ENDPOINTS (for testing/triggering)
# ============================================================

@alerts.route("/check-now", methods=["POST"])
@token_required(allowed_roles=["administrator"])
def trigger_manual_alert_check():
    """Manually trigger the daily alert check (admin only)"""
    try:
        result = PerformanceAlertEngine.perform_daily_alert_check(socketio=socketio)

        return jsonify({
            "status": result["status"],
            "message": result["message"],
            "alerts_generated": result.get("alerts_generated", {})
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@alerts.route("/check-kpis", methods=["POST"])
@token_required(allowed_roles=["administrator"])
def trigger_kpi_check():
    """Manually trigger KPI alert check (admin only)"""
    try:
        result = CustomKPIMonitor.check_all_kpis(socketio=socketio)

        return jsonify({
            "status": result["status"],
            "alerts_generated": result.get("alerts_generated", 0),
            "critical_kpis_checked": result.get("critical_kpis_checked", 0)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# SOCKET.IO EVENT HANDLERS
# ============================================================

@socketio.on("connect")
def handle_connect():
    """Handle client connection and send pending alerts"""
    try:
        from flask_jwt_extended import decode_token
        # This would need to be implemented based on your auth setup
        print(f"Client connected to alerts namespace")
    except Exception as e:
        print(f"Error on connect: {str(e)}")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    print("Client disconnected from alerts namespace")
