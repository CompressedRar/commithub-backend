from app import db
from sqlalchemy import func
from flask import jsonify

from models.Tasks import Sub_Task
from models.PCR import IPCR
from models.User import User
from models.Departments import Department
from services.PCR.pcr_rating_service import PCRRatingService


class PCRAnalyticsService:

    def get_department_performance_summary():
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()
        period = settings.current_period_id

        avg_q = func.avg(Sub_Task.quantity)
        avg_e = func.avg(Sub_Task.efficiency)
        avg_t = func.avg(Sub_Task.timeliness)

        results = (
            db.session.query(
                Department.id.label("dept_id"),
                Department.name.label("name"),
                avg_q.label("Quantity"),
                avg_e.label("Efficiency"),
                avg_t.label("Timeliness"),
                ((func.coalesce(avg_q, 0) + func.coalesce(avg_e, 0) + func.coalesce(avg_t, 0)) / 3.0).label("Average"),
            )
            .join(User, User.department_id == Department.id)
            .join(IPCR, IPCR.user_id == User.id)
            .join(Sub_Task, Sub_Task.ipcr_id == IPCR.id)
            .filter(Sub_Task.period == period, Sub_Task.status == 1, IPCR.status == 1)
            .group_by(Department.id)
            .all()
        )

        result_map = {r.dept_id: r for r in results}
        data = []

        for dept in Department.query.all():
            match = result_map.get(dept.id)
            if match:
                data.append({
                    "name": dept.name,
                    "Quantity": round(match.Quantity or 0, 2),
                    "Efficiency": round(match.Efficiency or 0, 2),
                    "Timeliness": round(match.Timeliness or 0, 2),
                    "Average": round(match.Average or 0, 2),
                })
            else:
                data.append({"name": dept.name, "Quantity": 0, "Efficiency": 0, "Timeliness": 0, "Average": 0})

        return jsonify(data), 200

    @staticmethod
    def get_performance_history(dept_id, start_date, end_date, metric_type="average"):
        try:
            from datetime import datetime as dt, timedelta

            start = dt.strptime(start_date, "%Y-%m-%d").date() if isinstance(start_date, str) else start_date
            end = dt.strptime(end_date, "%Y-%m-%d").date() if isinstance(end_date, str) else end_date

            rows = (
                db.session.query(
                    func.date(Sub_Task.created_at).label("created_at"),
                    func.avg(Sub_Task.quantity).label("avg_qty"),
                    func.avg(Sub_Task.efficiency).label("avg_eff"),
                    func.avg(Sub_Task.timeliness).label("avg_time"),
                )
                .join(IPCR, Sub_Task.ipcr_id == IPCR.id)
                .join(User, IPCR.user_id == User.id)
                .join(Department, User.department_id == Department.id)
                .filter(Department.id == dept_id, Sub_Task.created_at >= start, Sub_Task.created_at <= end, Sub_Task.status == 1)
                .group_by(func.date(Sub_Task.created_at))
                .order_by(func.date(Sub_Task.created_at))
                .all()
            )

            data = []
            for row in rows:
                qty = float(row.avg_qty or 0)
                eff = float(row.avg_eff or 0)
                time_ = float(row.avg_time or 0)
                value = {"quantity": qty, "efficiency": eff, "timeliness": time_}.get(
                    metric_type, (qty + eff + time_) / 3
                )

                trend = "stable"
                if data:
                    prev = data[-1]["value"]
                    if value > prev * 1.05:
                        trend = "improving"
                    elif value < prev * 0.95:
                        trend = "declining"

                data.append({
                    "date": row.created_at.strftime("%Y-%m-%d"),
                    "value": round(value, 2),
                    "trend_direction": trend,
                })

            return jsonify({"status": "success", "data": data}), 200

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @staticmethod
    def get_performance_trends(dept_id, timeframe="monthly", periods=12):
        try:
            from utils.TrendAnalysis import TrendAnalysis

            rows = (
                db.session.query(
                    func.date(Sub_Task.created_at).label("date"),
                    func.avg(Sub_Task.quantity).label("avg_qty"),
                    func.avg(Sub_Task.efficiency).label("avg_eff"),
                    func.avg(Sub_Task.timeliness).label("avg_time"),
                )
                .join(IPCR, Sub_Task.ipcr_id == IPCR.id)
                .join(User, IPCR.user_id == User.id)
                .join(Department, User.department_id == Department.id)
                .filter(Department.id == dept_id, Sub_Task.status == 1)
                .group_by(func.date(Sub_Task.created_at))
                .order_by(func.date(Sub_Task.created_at))
                .all()
            )

            data_by_period = {}
            for row in rows:
                if timeframe == "monthly":
                    key = row.date.strftime("%Y-%m")
                elif timeframe == "quarterly":
                    q = (row.date.month - 1) // 3 + 1
                    key = f"{row.date.year}-Q{q}"
                else:
                    key = str(row.date.year)

                data_by_period.setdefault(key, {"qty": [], "eff": [], "time": []})
                data_by_period[key]["qty"].append(float(row.avg_qty or 0))
                data_by_period[key]["eff"].append(float(row.avg_eff or 0))
                data_by_period[key]["time"].append(float(row.avg_time or 0))

            historical = []
            for period, vals in sorted(data_by_period.items()):
                avg_q = sum(vals["qty"]) / len(vals["qty"]) if vals["qty"] else 0
                avg_e = sum(vals["eff"]) / len(vals["eff"]) if vals["eff"] else 0
                avg_t = sum(vals["time"]) / len(vals["time"]) if vals["time"] else 0
                historical.append({
                    "period": period,
                    "actual": round((avg_q + avg_e + avg_t) / 3, 2),
                    "quantity": round(avg_q, 2),
                    "efficiency": round(avg_e, 2),
                    "timeliness": round(avg_t, 2),
                })

            values = [d["actual"] for d in historical]
            ma3 = TrendAnalysis.calculate_moving_average(values, 3)
            ma6 = TrendAnalysis.calculate_moving_average(values, 6)
            for i, item in enumerate(historical):
                item["moving_avg_3"] = ma3[i]
                item["moving_avg_6"] = ma6[i]

            for fc in TrendAnalysis.forecast_next_period(
                [{"date": d["period"], "value": d["actual"]} for d in historical],
                periods_ahead=max(1, periods - len(historical)),
            ):
                historical.append({
                    "period": f"Forecast+{fc['period']}",
                    "actual": fc["forecasted_value"],
                    "moving_avg_3": None, "moving_avg_6": None,
                    "forecast": True,
                    "confidence_lower": fc["confidence_lower"],
                    "confidence_upper": fc["confidence_upper"],
                })

            return jsonify({"status": "success", "data": historical}), 200

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @staticmethod
    def get_comparative_analytics(dept_ids, metric_type="average", date_range=None):
        try:
            from datetime import datetime as dt, timedelta

            if not dept_ids:
                return jsonify({"status": "error", "message": "No departments specified"}), 400

            dept_list = [int(x.strip()) for x in dept_ids.split(",")] if isinstance(dept_ids, str) else dept_ids
            start = dt.now().date() - timedelta(days=365 if date_range == "last_year" else 90)

            comparative = []
            for dept_id in dept_list:
                dept = Department.query.get(dept_id)
                if not dept:
                    continue

                m = (
                    db.session.query(
                        func.avg(Sub_Task.quantity).label("qty"),
                        func.avg(Sub_Task.efficiency).label("eff"),
                        func.avg(Sub_Task.timeliness).label("time"),
                    )
                    .join(IPCR).join(User)
                    .filter(User.department_id == dept_id, Sub_Task.created_at >= start, Sub_Task.status == 1)
                    .first()
                )

                q = float(m.qty or 0) if m else 0
                e = float(m.eff or 0) if m else 0
                t = float(m.time or 0) if m else 0

                comparative.append({
                    "department": dept.name,
                    "department_id": dept.id,
                    "quantity": round(q, 2),
                    "efficiency": round(e, 2),
                    "timeliness": round(t, 2),
                    "average": round((q + e + t) / 3, 2),
                    "trend": "stable",
                })

            sort_key = metric_type if metric_type in ("quantity", "efficiency", "timeliness") else "average"
            comparative.sort(key=lambda x: x[sort_key], reverse=True)

            return jsonify({"status": "success", "data": comparative}), 200

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @staticmethod
    def get_performance_forecast(dept_id, periods_ahead=3):
        try:
            from utils.TrendAnalysis import TrendAnalysis
            from datetime import datetime as dt, timedelta

            rows = (
                db.session.query(
                    func.date(Sub_Task.created_at).label("date"),
                    func.avg(Sub_Task.quantity).label("avg_qty"),
                    func.avg(Sub_Task.efficiency).label("avg_eff"),
                    func.avg(Sub_Task.timeliness).label("avg_time"),
                )
                .join(IPCR, Sub_Task.ipcr_id == IPCR.id)
                .join(User, IPCR.user_id == User.id)
                .join(Department, User.department_id == Department.id)
                .filter(Department.id == dept_id, Sub_Task.created_at >= dt.now().date() - timedelta(days=365), Sub_Task.status == 1)
                .group_by(func.date(Sub_Task.created_at))
                .order_by(func.date(Sub_Task.created_at))
                .all()
            )

            if not rows:
                return jsonify({"status": "error", "message": "Insufficient data for forecasting"}), 400

            historical = [
                {"date": row.date.strftime("%Y-%m-%d"), "value": ((float(row.avg_qty or 0) + float(row.avg_eff or 0) + float(row.avg_time or 0)) / 3)}
                for row in rows
            ]

            return jsonify({"status": "success", "data": TrendAnalysis.forecast_next_period(historical, periods_ahead)}), 200

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @staticmethod
    def get_kpi_status(dept_id):
        try:
            from models.Analytics import CustomKPIService
            kpis = CustomKPIService.get_department_kpis(dept_id, enabled_only=True)
            return jsonify({"status": "success", "data": [kpi.to_dict() for kpi in kpis]}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
