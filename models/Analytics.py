from datetime import datetime
from app import db

class PerformanceAlert(db.Model):
    """Model for tracking performance metric alerts"""
    __tablename__ = "performance_alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    metric_type = db.Column(db.String(50), nullable=False)  # quantity, efficiency, timeliness
    current_value = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    alert_level = db.Column(db.String(20), nullable=False)  # warning, critical
    message = db.Column(db.Text, nullable=True)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<PerformanceAlert {self.id} - {self.metric_type} - {self.alert_level}>"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'department_id': self.department_id,
            'metric_type': self.metric_type,
            'current_value': round(float(self.current_value), 2) if self.current_value else 0,
            'threshold': round(float(self.threshold), 2) if self.threshold else 0,
            'alert_level': self.alert_level,
            'message': self.message,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CustomKPI(db.Model):
    """Model for custom KPI definitions per department"""
    __tablename__ = "custom_kpis"

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    kpi_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    formula = db.Column(db.JSON, nullable=True)  # Formula definition for calculation
    target_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0)
    alert_threshold = db.Column(db.Float, nullable=False)  # Below this triggers alert
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<CustomKPI {self.id} - {self.kpi_name} - {self.department_id}>"

    def to_dict(self):
        return {
            'id': self.id,
            'department_id': self.department_id,
            'kpi_name': self.kpi_name,
            'description': self.description,
            'target_value': round(float(self.target_value), 2) if self.target_value else 0,
            'current_value': round(float(self.current_value), 2) if self.current_value else 0,
            'alert_threshold': round(float(self.alert_threshold), 2) if self.alert_threshold else 0,
            'variance_pct': round(((self.current_value - self.target_value) / self.target_value * 100), 2) if self.target_value else 0,
            'status': self._get_status(),
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def _get_status(self):
        """Determine KPI status based on current vs target and threshold"""
        if self.current_value >= self.target_value:
            return 'on_track'
        elif self.current_value >= self.alert_threshold:
            return 'at_risk'
        else:
            return 'critical'


class PerformanceAlertService:
    """Service class for managing performance alerts"""

    @staticmethod
    def create_alert(user_id, department_id, metric_type, current_value, threshold, alert_level, message=None):
        """Create a new performance alert"""
        alert = PerformanceAlert(
            user_id=user_id,
            department_id=department_id,
            metric_type=metric_type,
            current_value=current_value,
            threshold=threshold,
            alert_level=alert_level,
            message=message
        )
        db.session.add(alert)
        db.session.commit()
        return alert

    @staticmethod
    def get_user_alerts(user_id, unread_only=True):
        """Get alerts for a specific user"""
        query = PerformanceAlert.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(read=False)
        return query.order_by(PerformanceAlert.created_at.desc()).all()

    @staticmethod
    def mark_alert_as_read(alert_id):
        """Mark an alert as read"""
        alert = PerformanceAlert.query.get(alert_id)
        if alert:
            alert.read = True
            db.session.commit()
            return alert
        return None

    @staticmethod
    def mark_alerts_as_read(alert_ids):
        """Mark multiple alerts as read"""
        PerformanceAlert.query.filter(PerformanceAlert.id.in_(alert_ids)).update(
            {PerformanceAlert.read: True},
            synchronize_session=False
        )
        db.session.commit()

    @staticmethod
    def delete_alert(alert_id):
        """Delete an alert"""
        alert = PerformanceAlert.query.get(alert_id)
        if alert:
            db.session.delete(alert)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_recent_alerts(department_id, days=7):
        """Get recent alerts for a department"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        return PerformanceAlert.query.filter(
            PerformanceAlert.department_id == department_id,
            PerformanceAlert.created_at >= cutoff_date
        ).order_by(PerformanceAlert.created_at.desc()).all()


class CustomKPIService:
    """Service class for managing custom KPIs"""

    @staticmethod
    def create_kpi(department_id, kpi_name, target_value, alert_threshold, description=None, formula=None):
        """Create a new custom KPI"""
        kpi = CustomKPI(
            department_id=department_id,
            kpi_name=kpi_name,
            target_value=target_value,
            alert_threshold=alert_threshold,
            description=description,
            formula=formula
        )
        db.session.add(kpi)
        db.session.commit()
        return kpi

    @staticmethod
    def get_department_kpis(department_id, enabled_only=True):
        """Get all KPIs for a department"""
        query = CustomKPI.query.filter_by(department_id=department_id)
        if enabled_only:
            query = query.filter_by(enabled=True)
        return query.all()

    @staticmethod
    def update_kpi(kpi_id, **kwargs):
        """Update a KPI"""
        kpi = CustomKPI.query.get(kpi_id)
        if kpi:
            for key, value in kwargs.items():
                if hasattr(kpi, key):
                    setattr(kpi, key, value)
            kpi.updated_at = datetime.now()
            db.session.commit()
            return kpi
        return None

    @staticmethod
    def update_kpi_current_value(kpi_id, current_value):
        """Update only the current value of a KPI"""
        kpi = CustomKPI.query.get(kpi_id)
        if kpi:
            kpi.current_value = current_value
            kpi.updated_at = datetime.now()
            db.session.commit()
            return kpi
        return None

    @staticmethod
    def delete_kpi(kpi_id):
        """Delete a KPI"""
        kpi = CustomKPI.query.get(kpi_id)
        if kpi:
            db.session.delete(kpi)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_kpi_by_id(kpi_id):
        """Get a specific KPI"""
        return CustomKPI.query.get(kpi_id)

    @staticmethod
    def get_all_critical_kpis():
        """Get all KPIs that are in critical status"""
        return CustomKPI.query.filter(
            CustomKPI.enabled == True,
            CustomKPI.current_value < CustomKPI.alert_threshold
        ).all()
