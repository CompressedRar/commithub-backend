"""
Performance Alert Utility Module
Handles alert generation, threshold checking, and Socket.IO notification delivery
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from models.Analytics import PerformanceAlert, PerformanceAlertService, CustomKPI, CustomKPIService
from models.System_Settings import System_Settings
from models.User import Notification
from flask import jsonify


class PerformanceAlertEngine:
    """Engine for checking metrics against thresholds and generating alerts"""

    @staticmethod
    def check_metric_threshold(metric_value: float, metric_type: str,
                               thresholds: Dict = None) -> Optional[Tuple[str, float, float]]:
        """
        Check if a metric value breaches configured thresholds

        Args:
            metric_value: Current metric value
            metric_type: Type of metric (quantity, efficiency, timeliness)
            thresholds: Custom thresholds dict with warning and critical levels

        Returns:
            Tuple of (alert_level, threshold, variance) or None if no alert needed
            alert_level: 'critical' or 'warning' or None
        """
        if thresholds is None:
            settings = System_Settings.query.first()
            if not settings or not settings.alert_thresholds:
                return None
            thresholds = settings.alert_thresholds

        # Get thresholds for this metric type
        critical_key = f"{metric_type}_critical"
        warning_key = f"{metric_type}_warning"

        critical_threshold = thresholds.get(critical_key, 2.0)
        warning_threshold = thresholds.get(warning_key, 2.5)

        # Check thresholds (lower values trigger alerts)
        if metric_value < critical_threshold:
            variance = critical_threshold - metric_value
            return ('critical', critical_threshold, variance)
        elif metric_value < warning_threshold:
            variance = warning_threshold - metric_value
            return ('warning', warning_threshold, variance)

        return None

    @staticmethod
    def generate_alert(user_id: int, department_id: Optional[int],
                       metric_type: str, current_value: float,
                       threshold: float, alert_level: str,
                       message: str = None, socketio=None) -> PerformanceAlert:
        """
        Create an alert in the database and emit via Socket.IO

        Args:
            user_id: User ID to send alert to
            department_id: Associated department
            metric_type: Type of metric
            current_value: Current metric value
            threshold: Threshold that was breached
            alert_level: 'warning' or 'critical'
            message: Custom alert message
            socketio: Flask-SocketIO instance for real-time delivery

        Returns:
            Created PerformanceAlert object
        """
        if message is None:
            message = f"Department {metric_type.capitalize()} performance ({current_value:.2f}) below {alert_level} threshold ({threshold:.2f})"

        # Create alert in database
        alert = PerformanceAlertService.create_alert(
            user_id=user_id,
            department_id=department_id,
            metric_type=metric_type,
            current_value=current_value,
            threshold=threshold,
            alert_level=alert_level,
            message=message
        )

        # Send via Socket.IO if available
        if socketio:
            PerformanceAlertEngine.send_alert_via_socketio(alert, socketio)

        return alert

    @staticmethod
    def send_alert_via_socketio(alert: PerformanceAlert, socketio) -> None:
        """
        Emit alert to user via Socket.IO real-time websocket

        Args:
            alert: PerformanceAlert object
            socketio: Flask-SocketIO instance
        """
        alert_data = {
            'alert_id': alert.id,
            'user_id': alert.user_id,
            'department_id': alert.department_id,
            'metric_type': alert.metric_type,
            'current_value': round(float(alert.current_value), 2),
            'threshold': round(float(alert.threshold), 2),
            'alert_level': alert.alert_level,
            'message': alert.message,
            'created_at': alert.created_at.isoformat()
        }

        # Emit to specific user's room or broadcast if no user-specific room
        socketio.emit('performance_alert', alert_data, to=f"user_{alert.user_id}")

    @staticmethod
    def trigger_escalation(alert_id: int, socketio=None, hours_threshold: int = 24) -> Optional[PerformanceAlert]:
        """
        Escalate unread alerts after specified hours

        Args:
            alert_id: Alert ID to escalate
            socketio: Flask-SocketIO instance
            hours_threshold: Hours before escalation (default 24)

        Returns:
            Escalated alert or None if not found
        """
        alert = PerformanceAlert.query.get(alert_id)
        if not alert or alert.read:
            return None

        # Check if alert is old enough for escalation
        hours_since_creation = (datetime.now() - alert.created_at).total_seconds() / 3600
        if hours_since_creation < hours_threshold:
            return None

        # Update alert with escalation message
        escalation_message = f"[ESCALATED] {alert.message}"
        alert.message = escalation_message
        alert = PerformanceAlertService.update_kpi(alert_id, message=escalation_message)

        # Re-emit escalated alert
        if socketio and alert:
            PerformanceAlertEngine.send_alert_via_socketio(alert, socketio)

        return alert

    @staticmethod
    def perform_daily_alert_check(socketio=None) -> Dict:
        """
        Daily automated check for performance metrics against thresholds
        Should be scheduled to run once per day

        Args:
            socketio: Flask-SocketIO instance

        Returns:
            Summary of alerts generated
        """
        from models.Departments import Department
        from models.PCR import Sub_Task
        from sqlalchemy import func

        settings = System_Settings.query.first()
        if not settings or not settings.alert_thresholds:
            return {'status': 'error', 'message': 'No alert thresholds configured'}

        alerts_generated = {
            'quantity': 0,
            'efficiency': 0,
            'timeliness': 0,
            'total': 0
        }

        # Get current period
        current_period = settings.current_period_id

        try:
            # Get latest metrics per department per metric type
            departments = Department.query.all()

            for dept in departments:
                # Query latest performance data for this department
                latest_metrics = (
                    Sub_Task.query
                    .join(Department)
                    .filter(
                        Sub_Task.period == current_period,
                        Sub_Task.status == 1,
                        Department.id == dept.id
                    )
                    .with_entities(
                        func.avg(Sub_Task.quantity).label('avg_quantity'),
                        func.avg(Sub_Task.efficiency).label('avg_efficiency'),
                        func.avg(Sub_Task.timeliness).label('avg_timeliness')
                    )
                    .first()
                )

                if not latest_metrics:
                    continue

                # Check quantity
                if latest_metrics.avg_quantity:
                    result = PerformanceAlertEngine.check_metric_threshold(
                        float(latest_metrics.avg_quantity),
                        'quantity',
                        settings.alert_thresholds
                    )
                    if result:
                        alert_level, threshold, variance = result
                        # Get admin users for this department
                        admins = get_alert_recipients(dept.id, settings.alert_thresholds)
                        for admin_id in admins:
                            PerformanceAlertEngine.generate_alert(
                                user_id=admin_id,
                                department_id=dept.id,
                                metric_type='quantity',
                                current_value=float(latest_metrics.avg_quantity),
                                threshold=threshold,
                                alert_level=alert_level,
                                socketio=socketio
                            )
                        alerts_generated['quantity'] += len(admins)

                # Check efficiency
                if latest_metrics.avg_efficiency:
                    result = PerformanceAlertEngine.check_metric_threshold(
                        float(latest_metrics.avg_efficiency),
                        'efficiency',
                        settings.alert_thresholds
                    )
                    if result:
                        alert_level, threshold, variance = result
                        admins = get_alert_recipients(dept.id, settings.alert_thresholds)
                        for admin_id in admins:
                            PerformanceAlertEngine.generate_alert(
                                user_id=admin_id,
                                department_id=dept.id,
                                metric_type='efficiency',
                                current_value=float(latest_metrics.avg_efficiency),
                                threshold=threshold,
                                alert_level=alert_level,
                                socketio=socketio
                            )
                        alerts_generated['efficiency'] += len(admins)

                # Check timeliness
                if latest_metrics.avg_timeliness:
                    result = PerformanceAlertEngine.check_metric_threshold(
                        float(latest_metrics.avg_timeliness),
                        'timeliness',
                        settings.alert_thresholds
                    )
                    if result:
                        alert_level, threshold, variance = result
                        admins = get_alert_recipients(dept.id, settings.alert_thresholds)
                        for admin_id in admins:
                            PerformanceAlertEngine.generate_alert(
                                user_id=admin_id,
                                department_id=dept.id,
                                metric_type='timeliness',
                                current_value=float(latest_metrics.avg_timeliness),
                                threshold=threshold,
                                alert_level=alert_level,
                                socketio=socketio
                            )
                        alerts_generated['timeliness'] += len(admins)

            alerts_generated['total'] = sum([
                alerts_generated['quantity'],
                alerts_generated['efficiency'],
                alerts_generated['timeliness']
            ])

            return {
                'status': 'success',
                'message': f"Daily alert check completed",
                'alerts_generated': alerts_generated
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error during daily alert check: {str(e)}"
            }


def get_alert_recipients(department_id: int, alert_thresholds: Dict) -> List[int]:
    """
    Get list of user IDs that should receive alerts for a department

    Args:
        department_id: Department ID
        alert_thresholds: Alert threshold configuration

    Returns:
        List of user IDs to send alerts to
    """
    from models.User import Users

    # Get roles that should receive alerts
    alert_roles = alert_thresholds.get('alert_to_roles', ['administrator', 'head'])

    # Find users with these roles in this department
    recipients = Users.query.filter(
        Users.role.in_(alert_roles),
        Users.department_id == department_id
    ).with_entities(Users.id).all()

    return [r[0] for r in recipients]


class CustomKPIMonitor:
    """Monitor custom KPIs and generate alerts when thresholds are breached"""

    @staticmethod
    def check_all_kpis(socketio=None) -> Dict:
        """
        Check all custom KPIs against their thresholds

        Args:
            socketio: Flask-SocketIO instance

        Returns:
            Summary of alerts generated
        """
        critical_kpis = CustomKPIService.get_all_critical_kpis()

        alerts_generated = 0

        for kpi in critical_kpis:
            # Get department admins
            from models.User import Users
            admins = Users.query.filter(
                Users.role.in_(['administrator', 'head']),
                Users.department_id == kpi.department_id
            ).all()

            for admin in admins:
                message = f"KPI '{kpi.kpi_name}' is in critical status ({kpi.current_value:.2f} < {kpi.alert_threshold:.2f})"

                PerformanceAlertEngine.generate_alert(
                    user_id=admin.id,
                    department_id=kpi.department_id,
                    metric_type='custom_kpi',
                    current_value=kpi.current_value,
                    threshold=kpi.alert_threshold,
                    alert_level='critical',
                    message=message,
                    socketio=socketio
                )
                alerts_generated += 1

        return {
            'status': 'success',
            'alerts_generated': alerts_generated,
            'critical_kpis_checked': len(critical_kpis)
        }

    @staticmethod
    def update_kpi_value(kpi_id: int, new_value: float, socketio=None) -> Dict:
        """
        Update a KPI's current value and check if alert should be triggered

        Args:
            kpi_id: KPI ID to update
            new_value: New current value
            socketio: Flask-SocketIO instance

        Returns:
            Update status and any alerts generated
        """
        kpi = CustomKPIService.update_kpi_current_value(kpi_id, new_value)

        if not kpi:
            return {'status': 'error', 'message': 'KPI not found'}

        # Check if alert should be triggered
        if new_value < kpi.alert_threshold:
            # Generate alerts for admins
            from models.User import Users
            admins = Users.query.filter(
                Users.role.in_(['administrator', 'head']),
                Users.department_id == kpi.department_id
            ).all()

            alert_count = 0
            for admin in admins:
                PerformanceAlertEngine.generate_alert(
                    user_id=admin.id,
                    department_id=kpi.department_id,
                    metric_type='custom_kpi',
                    current_value=new_value,
                    threshold=kpi.alert_threshold,
                    alert_level='critical' if new_value < kpi.target_value else 'warning',
                    message=f"KPI '{kpi.kpi_name}' alert: {new_value:.2f} < {kpi.alert_threshold:.2f}",
                    socketio=socketio
                )
                alert_count += 1

            return {
                'status': 'success',
                'message': 'KPI updated and alerts generated',
                'alerts_generated': alert_count
            }

        return {
            'status': 'success',
            'message': 'KPI updated, no alerts triggered',
            'alerts_generated': 0
        }
