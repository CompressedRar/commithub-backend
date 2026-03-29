from app import db
from sqlalchemy import func, case, cast, Float, and_
from flask import jsonify
from models.Categories import Category
from models.Tasks import Sub_Task, Main_Task


class CategoryPerformanceService:

    def _get_valid_subtasks(main_task, period):
        """Yield sub_tasks that are active, in the current period, with an active IPCR."""
        for sub in main_task.sub_tasks:
            if sub.status == 1 and sub.period == period and sub.ipcr and sub.ipcr.status == 1:
                yield sub

    def _subtask_ratings(sub, enable_formula):
        """Return (quantity, efficiency, timeliness) for a sub_task."""
        if enable_formula:
            return sub.calculateQuantity(), sub.calculateEfficiency(), sub.calculateTimeliness()
        return sub.quantity, sub.efficiency, sub.timeliness

    def _avg_task_metrics(main_task, period, enable_formula):
        """
        Average quantity/efficiency/timeliness across valid sub_tasks for one task.
        Returns (q, e, t, count).
        """
        q_sum = e_sum = t_sum = count = 0
        for sub in CategoryPerformanceService._get_valid_subtasks(main_task, period):
            q, e, t = CategoryPerformanceService._subtask_ratings(sub, enable_formula)
            q_sum += q if q else 0
            e_sum += e if e else 0
            t_sum += t if t else 0
            count += 1
        return q_sum, e_sum, t_sum, count

    def get_task_average_summary(category_id):
        """
        SQL-based summary of stored sub_task ratings for each active main task
        in the given category. Fast path — does not invoke formula recalculation.
        """
        from models.System_Settings import System_Settings
        from models.PCR import IPCR

        settings = System_Settings.get_default_settings()

        cond = and_(
            Sub_Task.status == 1,
            Sub_Task.period == settings.current_period_id,
            IPCR.status == 1,
        )

        qty_col = case((cond, Sub_Task.quantity), else_=None)
        eff_col = case((cond, Sub_Task.efficiency), else_=None)
        tim_col = case((cond, Sub_Task.timeliness), else_=None)
        avg_col = case((cond, Sub_Task.average), else_=None)

        results = (
            db.session.query(
                Main_Task.id.label("task_id"),
                Main_Task.mfo.label("task_name"),
                func.avg(qty_col).label("avg_quantity"),
                func.avg(eff_col).label("avg_efficiency"),
                func.avg(tim_col).label("avg_timeliness"),
                func.avg(avg_col).label("avg_overall"),
            )
            .outerjoin(Sub_Task, Sub_Task.main_task_id == Main_Task.id)
            .outerjoin(IPCR, IPCR.id == Sub_Task.ipcr_id)
            .filter(
                Main_Task.category_id == category_id,
                Main_Task.status == 1,
                Main_Task.period == settings.current_period_id,
            )
            .group_by(Main_Task.id)
            .all()
        )

        data = [
            {
                "task_id": int(r.task_id),
                "task_name": r.task_name,
                "average_quantity": round(float(r.avg_quantity or 0), 2),
                "average_efficiency": round(float(r.avg_efficiency or 0), 2),
                "average_timeliness": round(float(r.avg_timeliness or 0), 2),
                "overall_average": round(float(r.avg_overall or 0), 2),
            }
            for r in results
        ]

        return jsonify(data), 200

    def calculate_category_performance(category_id):
        """
        Average of per-task averages across all active tasks in the category.
        Each task contributes equally regardless of subtask count.
        """
        from models.System_Settings import System_Settings

        category = Category.query.get(category_id)
        settings = System_Settings.get_default_settings()

        empty = {"quantity": 0, "efficiency": 0, "timeliness": 0, "overall_average": 0}

        if not category:
            return jsonify(empty), 200

        q_total = e_total = t_total = overall_total = task_count = 0

        for task in category.main_tasks:
            if task.status != 1 or task.period != settings.current_period_id:
                continue

            q_sum, e_sum, t_sum, count = CategoryPerformanceService._avg_task_metrics(
                task, settings.current_period_id, settings.enable_formula
            )
            if count == 0:
                continue

            q_avg = q_sum / count
            e_avg = e_sum / count
            t_avg = t_sum / count

            q_total += q_avg
            e_total += e_avg
            t_total += t_avg
            overall_total += (q_avg + e_avg + t_avg) / 3
            task_count += 1

        if task_count == 0:
            return jsonify(empty), 200

        return jsonify({
            "quantity": round(q_total / task_count, 2),
            "efficiency": round(e_total / task_count, 2),
            "timeliness": round(t_total / task_count, 2),
            "overall_average": round(overall_total / task_count, 2),
        }), 200

    def calculate_category_performance_per_department(category_id):
        """
        Per-department averages for the category.
        Each main task contributes equally to a department's score.
        """
        from models.System_Settings import System_Settings

        category = Category.query.get(category_id)
        settings = System_Settings.get_default_settings()

        if not category:
            return jsonify([]), 200

        # dept_name -> {quantity_total, efficiency_total, timeliness_total, overall_total, task_count}
        depts = {}

        for task in category.main_tasks:
            if task.status != 1 or task.period != settings.current_period_id:
                continue

            # Aggregate subtask ratings per department for this task
            task_dept = {}
            for sub in task.sub_tasks:
                if sub.status != 1 or sub.period != settings.current_period_id:
                    continue
                if not sub.output or not sub.output.user or not sub.ipcr or sub.ipcr.status != 1:
                    continue

                if not sub.output.user.department:
                    continue

                dept_name = sub.output.user.department.name

                
                if dept_name not in task_dept:
                    task_dept[dept_name] = {"q": 0.0, "e": 0.0, "t": 0.0, "count": 0}

                q, e, t = CategoryPerformanceService._subtask_ratings(sub, settings.enable_formula)
                task_dept[dept_name]["q"] += q if q else 0
                task_dept[dept_name]["e"] += e if e else 0
                task_dept[dept_name]["t"] += t if t else 0
                task_dept[dept_name]["count"] += 1

            # Fold per-task averages into global dept accumulators
            for dept_name, vals in task_dept.items():
                if vals["count"] == 0:
                    continue

                q_avg = vals["q"] / vals["count"]
                e_avg = vals["e"] / vals["count"]
                t_avg = vals["t"] / vals["count"]
                overall = (q_avg + e_avg + t_avg) / 3

                if dept_name not in depts:
                    depts[dept_name] = {"q": 0.0, "e": 0.0, "t": 0.0, "overall": 0.0, "task_count": 0}

                depts[dept_name]["q"] += q_avg
                depts[dept_name]["e"] += e_avg
                depts[dept_name]["t"] += t_avg
                depts[dept_name]["overall"] += overall
                depts[dept_name]["task_count"] += 1

        response = [
            {
                "name": dept_name,
                "quantity": round(v["q"] / v["task_count"], 2),
                "efficiency": round(v["e"] / v["task_count"], 2),
                "timeliness": round(v["t"] / v["task_count"], 2),
                "average": round(v["overall"] / v["task_count"], 2),
            }
            for dept_name, v in depts.items()
            if v["task_count"] > 0
        ]

        return jsonify(response), 200
