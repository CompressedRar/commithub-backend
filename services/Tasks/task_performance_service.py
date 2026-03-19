from app import db, socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from sqlalchemy import func
from flask import jsonify
from collections import defaultdict
from models.Tasks import Main_Task, Sub_Task, Output, Assigned_Department


class TaskPerformanceService:

    # ------------------------------------------------------------------
    # Static rating helpers (formula-free fallback)
    # ------------------------------------------------------------------

    def calculateQuantity(target_acc, actual_acc):
        if target_acc == 0:
            return 0
        ratio = actual_acc / target_acc
        if ratio >= 1.3:
            return 5
        elif ratio >= 1.01:
            return 4
        elif ratio >= 0.90:
            return 3
        elif ratio >= 0.70:
            return 2
        return 1

    def calculateEfficiency(target_mod, actual_mod):
        calc = actual_mod
        if calc == 0:
            return 5
        elif calc <= 2:
            return 4
        elif calc <= 4:
            return 3
        elif calc <= 6:
            return 2
        return 1

    def calculateTimeliness(target_time, actual_time):
        if target_time == 0:
            return 0
        ratio = ((target_time - actual_time) / target_time) + 1
        if ratio >= 1.3:
            return 5
        elif ratio >= 1.15:
            return 4
        elif ratio >= 0.9:
            return 3
        elif ratio >= 0.51:
            return 2
        return 1

    def calculateAverage(quantity, efficiency, timeliness):
        q = min(quantity or 0, 5)
        e = min(efficiency or 0, 5)
        t = min(timeliness or 0, 5)
        return (q + e + t) / 3

    # ------------------------------------------------------------------
    # Sub-task field updates
    # ------------------------------------------------------------------

    def calculate_sub_tasks_rating(sub_tasks_array):
        try:
            for sub_id in sub_tasks_array:
                sub_t = Sub_Task.query.get(sub_id)
                sub_t.auto_calculate_ratings()
        
            db.session.commit()

            return jsonify(message="Task updated"), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Data does not exists"), 400
        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def update_sub_task_fields(sub_task_id, field, value):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        try:
            ipcr = Sub_Task.query.get(sub_task_id)

            FORMULA_FIELDS = {
                "target_acc": ("quantity", lambda s: (int(value), s.actual_acc)),
                "target_time": ("timeliness", lambda s: (int(value), s.actual_time)),
                "target_mod": ("efficiency", lambda s: (int(value), s.actual_mod)),
                "actual_acc": ("quantity", lambda s: (s.target_acc, int(value))),
                "actual_time": ("timeliness", lambda s: (s.target_time, int(value))),
                "actual_mod": ("efficiency", lambda s: (s.target_mod, int(value))),
            }

            if field in FORMULA_FIELDS:
                setattr(ipcr, field, int(value))
                db.session.commit()
                if settings.enable_formula or False:
                    metric, get_args = FORMULA_FIELDS[field]
                    target, actual = get_args(ipcr)
                    ipcr.calculate_with_override(metric, target, actual)

            elif field == "actual_deadline":
                ipcr.actual_deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))

            elif field in ("quantity", "efficiency", "timeliness"):
                setattr(ipcr, field, int(value))
                db.session.commit()

            elif field == "average":
                ipcr.average = float(value)

            ipcr.average = TaskPerformanceService.calculateAverage(
                ipcr.quantity, ipcr.efficiency, ipcr.timeliness
            )

            db.session.commit()

            return jsonify(message="Task updated"), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Data does not exists"), 400
        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_task_user_averages(task_id):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        results = (
            db.session.query(
                Output.user_id,
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("overall_average"),
            )
            .join(Sub_Task, Output.id == Sub_Task.output_id)
            .filter(Output.main_task_id == task_id, Output.period == settings.current_period_id)
            .group_by(Output.user_id)
            .all()
        )

        return [
            {
                "user_id": row.user_id,
                "avg_quantity": round(row.avg_quantity or 0, 2),
                "avg_efficiency": round(row.avg_efficiency or 0, 2),
                "avg_timeliness": round(row.avg_timeliness or 0, 2),
                "overall_average": round(row.overall_average or 0, 2),
            }
            for row in results
        ]

    def get_department_subtask_percentage(main_task_id):
        main_task = Main_Task.query.get(main_task_id)
        if not main_task:
            return []

        dept_count = defaultdict(int)
        total_users = 0

        for output in main_task.outputs:
            if not output.user or not output.user.department:
                continue
            dept_count[output.user.department.name] += 1
            total_users += 1

        if total_users == 0:
            return []

        return [
            {
                "name": dept,
                "count": count,
                "percentage": round((count / total_users) * 100, 2),
            }
            for dept, count in dept_count.items()
        ]

    def calculate_main_task_performance(main_task_id):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()
        main_task = Main_Task.query.get(main_task_id)

        empty = {"quantity": 0, "efficiency": 0, "timeliness": 0, "overall_average": 0}

        if not main_task:
            return jsonify(empty), 404

        totals = {"quantity": 0, "efficiency": 0, "timeliness": 0, "average": 0}
        count = 0

        for sub_task in main_task.sub_tasks:
            if settings.enable_formula:
                totals["quantity"] += sub_task.calculateQuantity()
                totals["efficiency"] += sub_task.calculateEfficiency()
                totals["timeliness"] += sub_task.calculateTimeliness()
            else:
                totals["quantity"] += sub_task.quantity
                totals["efficiency"] += sub_task.efficiency
                totals["timeliness"] += sub_task.timeliness
            totals["average"] += sub_task.calculateAverage()
            count += 1

        if count == 0:
            return jsonify(empty), 200

        return jsonify({
            "quantity": round(totals["quantity"] / count, 2),
            "efficiency": round(totals["efficiency"] / count, 2),
            "timeliness": round(totals["timeliness"] / count, 2),
            "overall_average": round(totals["average"] / count, 2),
        }), 200

    def calculate_user_performance(user_id):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        results = (
            db.session.query(
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("avg_overall"),
            )
            .join(Output, Output.id == Sub_Task.output_id)
            .filter(Output.user_id == user_id, Output.period == settings.current_period_id)
            .first()
        )

        if not results or results.avg_quantity is None:
            return {"user_id": user_id, "quantity": 0, "efficiency": 0, "timeliness": 0, "overall_average": 0}

        return {
            "user_id": user_id,
            "quantity": round(results.avg_quantity or 0, 2),
            "efficiency": round(results.avg_efficiency or 0, 2),
            "timeliness": round(results.avg_timeliness or 0, 2),
            "overall_average": round(results.avg_overall or 0, 2),
        }

    def _build_task_summary(task, settings):
        """Compute performance totals for a single main task across its sub_tasks."""
        totals = {"quantity": 0, "efficiency": 0, "timeliness": 0, "average": 0}
        count = 0

        for sub_task in task.sub_tasks:
            target_working_days = 0
            actual_working_days = 0

            if task.timeliness_mode == "timeframe":
                timeliness = sub_task.calculate_with_override(
                    "timeliness", sub_task.target_time, sub_task.actual_time
                )
            elif sub_task.actual_deadline and sub_task.main_task.target_deadline:
                days_late = (sub_task.actual_deadline - sub_task.main_task.target_deadline).days
                actual_working_days = days_late
                target_working_days = 1
                timeliness = sub_task.timeliness
            else:
                timeliness = 0

            quantity = sub_task.quantity
            efficiency = sub_task.efficiency

            if settings.enable_formula:
                quantity = sub_task.calculate_with_override(
                    "quantity", sub_task.target_acc, sub_task.actual_acc
                )
                efficiency = sub_task.calculate_with_override(
                    "efficiency", sub_task.target_mod, sub_task.actual_mod
                )
                timeliness = sub_task.calculate_with_override(
                    "timeliness", target_working_days, actual_working_days
                )

            totals["quantity"] += quantity
            totals["efficiency"] += efficiency
            totals["timeliness"] += timeliness
            totals["average"] += sub_task.calculateAverage()
            count += 1

        base = {
            "task_id": task.id,
            "category_id": task.category_id,
            "task_name": task.mfo,
        }

        if count > 0:
            return {**base, **{
                "average_quantity": round(totals["quantity"] / count, 2),
                "average_efficiency": round(totals["efficiency"] / count, 2),
                "average_timeliness": round(totals["timeliness"] / count, 2),
                "overall_average": round(totals["average"] / count, 2),
            }}

        return {**base, "average_quantity": 0, "average_efficiency": 0,
                "average_timeliness": 0, "overall_average": 0}

    def get_all_tasks_average_summary():
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()
        all_tasks = Main_Task.query.filter_by(status=1, period=settings.current_period_id).all()
        data = [TaskPerformanceService._build_task_summary(task, settings) for task in all_tasks]
        return jsonify(data), 200

    def calculate_all_tasks_average_summary():
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()
        all_tasks = Main_Task.query.filter_by(status=1, period=settings.current_period_id).all()
        return [TaskPerformanceService._build_task_summary(task, settings) for task in all_tasks]

    @staticmethod
    def get_user_performance_history(user_id, start_date=None, end_date=None):
        from datetime import datetime as dt, timedelta
        from models.PCR import IPCR

        try:
            start = (
                dt.strptime(start_date, "%Y-%m-%d").date()
                if isinstance(start_date, str) and start_date
                else dt.now().date() - timedelta(days=365)
            )
            end = (
                dt.strptime(end_date, "%Y-%m-%d").date()
                if isinstance(end_date, str) and end_date
                else dt.now().date()
            )

            rows = (
                db.session.query(
                    func.date(Sub_Task.created_at).label("date"),
                    func.avg(Sub_Task.quantity).label("avg_qty"),
                    func.avg(Sub_Task.efficiency).label("avg_eff"),
                    func.avg(Sub_Task.timeliness).label("avg_time"),
                    func.count(Sub_Task.id).label("count"),
                )
                .join(IPCR)
                .filter(
                    IPCR.user_id == user_id,
                    Sub_Task.created_at >= start,
                    Sub_Task.created_at <= end,
                    Sub_Task.status == 1,
                )
                .group_by(func.date(Sub_Task.created_at))
                .order_by(func.date(Sub_Task.created_at))
                .all()
            )

            data = []
            for row in rows:
                avg_qty = float(row.avg_qty or 0)
                avg_eff = float(row.avg_eff or 0)
                avg_time = float(row.avg_time or 0)
                data.append({
                    "date": row.date.strftime("%Y-%m-%d"),
                    "period": row.date.strftime("%Y-%m"),
                    "quantity": round(avg_qty, 2),
                    "efficiency": round(avg_eff, 2),
                    "timeliness": round(avg_time, 2),
                    "average": round((avg_qty + avg_eff + avg_time) / 3, 2),
                    "task_count": int(row.count),
                })

            if data:
                summary = {
                    "avg_quantity": round(sum(d["quantity"] for d in data) / len(data), 2),
                    "avg_efficiency": round(sum(d["efficiency"] for d in data) / len(data), 2),
                    "avg_timeliness": round(sum(d["timeliness"] for d in data) / len(data), 2),
                    "overall_average": round(sum(d["average"] for d in data) / len(data), 2),
                    "total_tasks": sum(d["task_count"] for d in data),
                    "periods": len(data),
                }
            else:
                summary = {
                    "avg_quantity": 0, "avg_efficiency": 0,
                    "avg_timeliness": 0, "overall_average": 0,
                    "total_tasks": 0, "periods": 0,
                }

            return jsonify({"status": "success", "data": data, "summary": summary}), 200

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
