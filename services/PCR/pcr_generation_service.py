from app import db, socketio
from flask import jsonify

from models.PCR import IPCR, OPCR, Assigned_PCR
from models.User import User
from services.PCR.pcr_rating_service import PCRRatingService
from services.tasks_service import Tasks_Service
from utils import ExcelHandler


class PCRGenerationService:

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _build_head_data(opcr, head=None):
        """Build the admin metadata block used in all OPCR exports."""
        opcr_data = opcr.to_dict()
        base_individuals = {
            k: {"name": opcr_data[k]["name"], "position": opcr_data[k]["position"], "date": ""}
            for k in ("approve", "discuss", "assess", "final")
        }
        base_individuals["confirm"] = {
            "name": "Hon. Maria Elena L. Germar",
            "position": "PMT Chairperson",
            "date": "",
        }

        if head:
            full = f"{head.first_name} {head.last_name}"
            return {
                "fullName": full,
                "givenName": head.first_name,
                "middleName": head.middle_name,
                "lastName": head.last_name,
                "position": head.position.name,
                "individuals": {
                    "review": {"name": full, "position": head.position.name, "date": ""},
                    **base_individuals,
                },
            }

        return {
            "fullName": "", "givenName": "", "middleName": "", "lastName": "", "position": "",
            "individuals": {
                "review": {"name": "", "position": "", "date": ""},
                **base_individuals,
            },
        }

    def _get_dept_configs(dept_id, period):
        from models.Tasks import Assigned_Department
        return {
            ad.main_task_id: {
                "enable": ad.enable_formulas,
                "quantity": ad.quantity_formula,
                "efficiency": ad.efficiency_formula,
                "timeliness": ad.timeliness_formula,
                "weight": float(ad.task_weight / 100),
            }
            for ad in Assigned_Department.query.filter_by(
                department_id=dept_id, period=period
            ).all()
        }

    def _build_task_dict(main_task, ad, is_draft=False):
        """Build the base task data structure for an OPCR task entry."""
        q = 0 if is_draft else (ad.quantity or 0)
        e = 0 if is_draft else (ad.efficiency or 0)
        t = 0 if is_draft else (ad.timeliness or 0)
        avg = Tasks_Service.calculateAverage(q, e, t)
        weight = ad.task_weight / 100

        return {
            "title": main_task.mfo,
            "summary": {"target": 0, "actual": 0},
            "corrections": {"target": 0, "actual": 0},
            "working_days": {"target": 0, "actual": 0},
            "description": {
                "target": main_task.target_accomplishment,
                "actual": 0 if is_draft else main_task.actual_accomplishment,
                "alterations": main_task.modification,
                "time": main_task.time_description,
                "timeliness_mode": main_task.timeliness_mode,
                "task_weight": weight,
            },
            "rating": {
                "a_dept_id": ad.id,
                "quantity": q, "efficiency": e, "timeliness": t,
                "average": avg,
                "weighted_avg": avg * weight if avg else 0,
            },
            "frequency": 0,
            "_task_id": main_task.id,
        }

    def _build_opcr_structures(opcr, settings, is_draft=False):
        """
        Build task_index, assigned, and categories from an OPCR's department tasks.
        Returns (task_index, assigned, categories).
        """
        from models.Tasks import Assigned_Department

        task_index = {}
        assigned = {}
        categories = {}

        dept_tasks = (
            Assigned_Department.query
            .filter_by(department_id=opcr.department_id, period=settings.current_period_id)
            .join(Assigned_Department.main_task)
            .all()
        )

        for ad in dept_tasks:
            mt = ad.main_task
            cat = mt.category
            if cat.status == 0 or mt.status == 0:
                continue

            categories.setdefault(cat.name, {"priority": cat.priority_order, "tasks": []})

            task = PCRGenerationService._build_task_dict(mt, ad, is_draft)
            task_index[mt.id] = task
            categories[cat.name]["tasks"].append(task)

        return task_index, assigned, categories

    def _aggregate_subtasks(opcr, task_index, assigned):
        """Aggregate actual data from sub_tasks into task_index."""
        for apcr in opcr.assigned_pcrs:
            ipcr = apcr.ipcr
            if ipcr.status == 0:
                continue

            user_name = f"{ipcr.user.first_name} {ipcr.user.last_name}"
            for sub in ipcr.sub_tasks:
                if sub.status == 0:
                    continue

                mfo = sub.main_task.mfo
                if user_name not in assigned.get(mfo, []):
                    assigned.setdefault(mfo, []).append(user_name)

                task = task_index.get(sub.main_task.id)
                if not task:
                    continue

                if (
                    sub.main_task.timeliness_mode == "deadline"
                    and sub.actual_deadline
                    and sub.main_task.target_deadline
                ):
                    actual_days = (sub.actual_deadline - sub.main_task.target_deadline).days
                else:
                    actual_days = sub.actual_time or 0

                task["summary"]["target"] += sub.target_acc
                task["summary"]["actual"] += sub.actual_acc
                task["corrections"]["target"] += sub.target_mod
                task["corrections"]["actual"] += sub.actual_mod
                task["working_days"]["target"] += sub.target_time
                task["working_days"]["actual"] += actual_days
                task["frequency"] += 1

    def _compute_task_ratings(task, settings, dept_configs, check_rating_period=False):
        """Apply formula overrides and return updated (q, e, t, avg)."""
        q = task["rating"]["quantity"] or 0
        e = task["rating"]["efficiency"] or 0
        t = task["rating"]["timeliness"] or 0

        print(task["_task_id"])
        """settings.enable_formula and not check_rating_period"""
        if settings.enable_formula and check_rating_period:
            tid = task["_task_id"]
            q = PCRRatingService.compute_rating_with_override("quantity", task["summary"]["target"], task["summary"]["actual"], tid, settings, dept_configs)
            e = PCRRatingService.compute_rating_with_override("efficiency", task["corrections"]["target"], task["corrections"]["actual"], tid, settings, dept_configs)
            t = PCRRatingService.compute_rating_with_override("timeliness", task["working_days"]["target"], task["working_days"]["actual"], tid, settings, dept_configs)
        
        return q, e, t, PCRRatingService.calculateAverage(q, e, t)

    def _finalize_data(categories, settings, dept_configs, check_rating_period=False, is_draft=False):
        """Flatten categories into data list, apply ratings, strip _task_id."""
        data = []
        for cat_name, meta in sorted(
            categories.items(), key=lambda x: x[1]["priority"], reverse=True
        ):
            for task in meta["tasks"]:
                task.pop("_task_id", None)

            data.append({cat_name: meta["tasks"]})
        return data

    # ------------------------------------------------------------------
    # OPCR views (JSON response)
    # ------------------------------------------------------------------

    @staticmethod
    def compute_and_save_opcr_ratings(opcr_id):
        """
        Manually trigger the calculation of ratings based on current 
        subtask accomplishments and save them to the database.
        """
        from models.System_Settings import System_Settings
        from models.Tasks import Assigned_Department

        opcr = OPCR.query.get_or_404(opcr_id)
        settings = System_Settings.get_default_settings()
        dept_configs = PCRGenerationService._get_dept_configs(opcr.department_id, settings.current_period_id)

        # 1. Build structures and aggregate actuals from IPCR subtasks
        task_index, assigned, categories = PCRGenerationService._build_opcr_structures(opcr, settings)
        PCRGenerationService._aggregate_subtasks(opcr, task_index, assigned)

        # 2. Iterate through aggregated tasks and update the DB
        for task_id, task_data in task_index.items():
            # Only compute if there is activity (frequency > 0)
            if task_data["frequency"] > 0:
                print("computing opcr task")
                q, e, t, avg = PCRGenerationService._compute_task_ratings(
                    task_data, settings, dept_configs, True
                )

                # 3. Update the Assigned_Department record
                ad_id = task_data["rating"]["a_dept_id"]
                assigned_dept_record = Assigned_Department.query.get(ad_id)
                
                if assigned_dept_record:
                    print(q, e, t)
                    assigned_dept_record.quantity = q
                    assigned_dept_record.efficiency = e
                    assigned_dept_record.timeliness = t

                    db.session.commit()

                    # Weighted average calculation is usually handled during export/view, 
                    # but we store the raw Q, E, T here.

        try:
            db.session.commit()
            socketio.emit("rating", "test")
            return jsonify({"message": "Ratings computed and saved successfully", "status": "success"}), 200
        except Exception as err:
            db.session.rollback()
            return jsonify({"message": str(err), "status": "error"}), 400

    def get_opcr(opcr_id):
        from models.System_Settings import System_Settings, System_Settings_Service

        opcr = OPCR.query.get(opcr_id)
        settings = System_Settings.get_default_settings()
        dept_configs = PCRGenerationService._get_dept_configs(opcr.department_id, settings.current_period_id)

        task_index, assigned, categories = PCRGenerationService._build_opcr_structures(opcr, settings)
        PCRGenerationService._aggregate_subtasks(opcr, task_index, assigned)

        is_rating = System_Settings_Service.check_if_rating_period()
        data = PCRGenerationService._finalize_data(categories, settings, dept_configs, is_rating)

        head = User.query.filter_by(department_id=opcr.department_id, role="head").first()
        head_data = PCRGenerationService._build_head_data(opcr, head)

        return jsonify(
            ipcr_data=data, assigned=assigned,
            admin_data=head_data, form_status=opcr.form_status,
        )

    def get_planned_opcr_by_department(department_id):
        from models.Tasks import Assigned_Department
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()
        task_index, assigned, categories = PCRGenerationService._build_planned_structures(
            department_id, settings
        )

        data = []
        for cat_name, meta in sorted(
            categories.items(), key=lambda x: x[1]["priority"], reverse=True
        ):
            for task in meta["tasks"]:
                task.pop("_task_id", None)
            data.append({cat_name: meta["tasks"]})

        head = User.query.filter_by(department_id=department_id, role="head").first()
        opcr = OPCR.query.filter_by(department_id=department_id).all()[-1]
        head_data = PCRGenerationService._build_head_data(opcr, head)

        return jsonify(ipcr_data=data, assigned=assigned, admin_data=head_data, form_status=1)

    def get_master_opcr():
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            period = str(settings.current_period_id)
            opcrs = OPCR.query.filter_by(status=1, isMain=True, period=period).all()

            if not opcrs:
                return jsonify(error="There is no OPCR to consolidate"), 400

            data, assigned, task_index = PCRGenerationService._build_master_data(opcrs, period, settings)

            head_data = PCRGenerationService._build_master_head_data(settings)
            return jsonify(ipcr_data=data, assigned=assigned, admin_data=head_data, form_status="")

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # OPCR file generation
    # ------------------------------------------------------------------

    def generate_opcr(opcr_id):
        from models.System_Settings import System_Settings, System_Settings_Service

        opcr = OPCR.query.get(opcr_id)
        settings = System_Settings.get_default_settings()
        dept_configs = PCRGenerationService._get_dept_configs(opcr.department_id, settings.current_period_id)

        task_index, assigned, categories = PCRGenerationService._build_opcr_structures(opcr, settings)
        PCRGenerationService._aggregate_subtasks(opcr, task_index, assigned)

        is_rating = System_Settings_Service.check_if_rating_period()
        data = PCRGenerationService._finalize_data(categories, settings, dept_configs, is_rating)

        head = User.query.filter_by(department_id=opcr.department_id, role="head").first()
        head_data = PCRGenerationService._build_head_data(opcr, head)

        return ExcelHandler.createNewOPCR(data=data, assigned=assigned, admin_data=head_data)

    def generate_weighted_opcr(opcr_id):
        from models.System_Settings import System_Settings

        opcr = OPCR.query.get(opcr_id)
        settings = System_Settings.get_default_settings()
        dept_configs = PCRGenerationService._get_dept_configs(opcr.department_id, settings.current_period_id)

        task_index, assigned, categories = PCRGenerationService._build_opcr_structures(opcr, settings)
        PCRGenerationService._aggregate_subtasks(opcr, task_index, assigned)
        data = PCRGenerationService._finalize_data(categories, settings, dept_configs)

        head = User.query.filter_by(department_id=opcr.department_id, role="head").first()
        head_data = PCRGenerationService._build_head_data(opcr, head)

        return ExcelHandler.createNewWeightedOPCR(data=data, assigned=assigned, admin_data=head_data)

    def new_generate_opcr(opcr_id, is_weighted=False, is_draft=False):
        from models.System_Settings import System_Settings, System_Settings_Service

        opcr = OPCR.query.get(opcr_id)
        if not opcr:
            return None

        settings = System_Settings.get_default_settings()
        dept_configs = PCRGenerationService._get_dept_configs(opcr.department_id, settings.current_period_id)

        task_index, assigned, categories = PCRGenerationService._build_opcr_structures(opcr, settings, is_draft)
        if not is_draft:
            PCRGenerationService._aggregate_subtasks(opcr, task_index, assigned)

        is_rating = System_Settings_Service.check_if_rating_period()
        data = PCRGenerationService._finalize_data(categories, settings, dept_configs, is_rating, is_draft)

        head = User.query.filter_by(department_id=opcr.department_id, role="head").first()
        head_data = PCRGenerationService._build_head_data(opcr, head)

        if is_weighted:
            return ExcelHandler.createNewWeightedOPCR(data=data, assigned=assigned, admin_data=head_data)
        return ExcelHandler.createNewOPCR(data=data, assigned=assigned, admin_data=head_data)

    def generate_planned_opcr_by_department(department_id):
        task_index, assigned, categories = PCRGenerationService._build_planned_structures(
            department_id, PCRGenerationService._get_settings()
        )

        data = []
        for cat_name, meta in sorted(
            categories.items(), key=lambda x: x[1]["priority"], reverse=True
        ):
            for task in meta["tasks"]:
                task.pop("_task_id", None)
            data.append({cat_name: meta["tasks"]})

        head = User.query.filter_by(department_id=department_id, role="head").first()
        opcr = OPCR.query.filter_by(department_id=department_id).all()[-1]
        head_data = PCRGenerationService._build_head_data(opcr, head)

        return ExcelHandler.createNewOPCR(data=data, assigned=assigned, admin_data=head_data)

    def generate_master_opcr():
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            period = settings.current_period_id
            opcrs = OPCR.query.filter_by(status=1, isMain=True, period=period).all()

            if not opcrs:
                return jsonify(error="There is no OPCR to consolidate"), 400

            data, assigned, task_index = PCRGenerationService._build_master_data(opcrs, period, settings)
            head_data = PCRGenerationService._build_master_head_data(settings)

            return jsonify(link=ExcelHandler.createNewMasterOPCR(
                data=data, assigned=assigned, admin_data=head_data
            )), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # Shared internal builders
    # ------------------------------------------------------------------

    def _get_settings():
        from models.System_Settings import System_Settings
        return System_Settings.get_default_settings()

    def _build_planned_structures(department_id, settings):
        """Build task structures for a planned (draft) OPCR with only target data."""
        from models.Tasks import Assigned_Department

        task_index = {}
        assigned = {}
        categories = {}

        dept_tasks = Assigned_Department.query.filter_by(
            department_id=department_id, period=settings.current_period_id
        ).all()

        for ad in dept_tasks:
            mt = ad.main_task
            cat = mt.category
            if mt.status == 0 or cat.status == 0:
                continue

            categories.setdefault(cat.name, {"priority": cat.priority_order, "tasks": []})
            assigned[mt.mfo] = [u["full_name"] for u in mt.get_users_by_dept(department_id)]

            task = {
                "title": mt.mfo,
                "summary": {"target": 0, "actual": 0},
                "corrections": {"target": 0, "actual": 0},
                "working_days": {"target": 0, "actual": 0},
                "description": {
                    "target": mt.target_accomplishment,
                    "actual": mt.actual_accomplishment,
                    "alterations": mt.modification,
                    "time": mt.time_description,
                    "timeliness_mode": mt.timeliness_mode,
                    "target_timeframe": mt.target_timeframe,
                    "target_deadline": str(mt.target_deadline) if mt.target_deadline else None,
                    "weight": float(ad.task_weight / 100),
                },
                "rating": {"quantity": 0, "efficiency": 0, "timeliness": 0, "average": 0},
                "type": cat.type,
                "frequency": 0,
                "_task_id": mt.id,
            }

            for sub in mt.sub_tasks:
                if sub.status == 0:
                    continue
                task["summary"]["target"] += sub.target_acc or 0
                task["corrections"]["target"] += sub.target_mod or 0
                task["working_days"]["target"] += sub.target_time or 0
                task["frequency"] += 1

            task_index[mt.id] = task
            categories[cat.name]["tasks"].append(task)

        return task_index, assigned, categories

    def _build_master_task_dict(main_task):
        return {
            "title": main_task.mfo,
            "summary": {"target": 0, "actual": 0},
            "corrections": {"target": 0, "actual": 0},
            "working_days": {"target": 0, "actual": 0},
            "description": {
                "target": main_task.target_accomplishment,
                "actual": main_task.actual_accomplishment,
                "alterations": main_task.modification,
                "time": main_task.time_description,
                "target_timeframe": main_task.target_timeframe,
                "target_dealine": main_task.target_deadline,
                "timeliness_mode": main_task.timeliness_mode,
            },
            "rating": {"quantity": 0, "efficiency": 0, "timeliness": 0, "average": 0},
            "frequency": 0,
            "_task_id": main_task.id,
        }

    def _build_master_data(opcrs, period, settings):
        """Build master OPCR data across all departments."""
        from models.Categories import Category

        task_index = {}
        data = []

        categories = Category.query.filter_by(status=1, period=period).order_by(
            Category.priority_order.desc()
        ).all()

        for cat in categories:
            task_list = []
            for mt in cat.main_tasks:
                if mt.status == 0:
                    continue
                task = PCRGenerationService._build_master_task_dict(mt)
                task_list.append(task)
                task_index[mt.id] = task
            data.append({cat.name: task_list})

        # Collect assigned users
        assigned = {}
        for opcr in opcrs:
            for apcr in opcr.assigned_pcrs:
                ipcr = apcr.ipcr
                if ipcr.status == 0 or ipcr.form_status == "draft":
                    continue
                for sub in ipcr.sub_tasks:
                    name = f"{ipcr.user.first_name} {ipcr.user.last_name}"
                    assigned.setdefault(sub.main_task.mfo, set()).add(name)

        assigned = {k: list(v) for k, v in assigned.items()}

        # Aggregate subtask data
        for opcr in opcrs:
            for apcr in opcr.assigned_pcrs:
                ipcr = apcr.ipcr
                if ipcr.status == 0 or ipcr.form_status == "draft":
                    continue
                for sub in ipcr.sub_tasks:
                    task = task_index.get(sub.main_task.id)
                    if not task:
                        continue

                    if (
                        sub.main_task.timeliness_mode == "deadline"
                        and sub.actual_deadline
                        and sub.main_task.target_deadline
                    ):
                        actual_days = (sub.actual_deadline - sub.main_task.target_deadline).days
                    else:
                        actual_days = sub.actual_time or 0

                    task["summary"]["target"] += sub.target_acc
                    task["summary"]["actual"] += sub.actual_acc
                    task["corrections"]["target"] += sub.target_mod
                    task["corrections"]["actual"] += sub.actual_mod
                    task["working_days"]["target"] += sub.target_time
                    task["working_days"]["actual"] += actual_days
                    task["frequency"] += 1

        # Compute ratings
        for task in task_index.values():
            if task["frequency"] == 0:
                continue

            q = e = t = 0
            if settings.enable_formula:
                q = PCRRatingService.compute_quantity_rating(task["summary"]["target"], task["summary"]["actual"], settings)
                e = PCRRatingService.compute_efficiency_rating(task["corrections"]["target"], task["corrections"]["actual"], settings)
                t = PCRRatingService.compute_timeliness_rating(task["working_days"]["target"], task["working_days"]["actual"], settings)

            avg = PCRRatingService.calculateAverage(q, e, t)
            task["rating"] = {"quantity": q, "efficiency": e, "timeliness": t, "average": avg}
            task.pop("_task_id", None)

        return data, assigned, task_index

    def _build_master_head_data(settings):
        president = settings.current_president_fullname
        mayor = settings.current_mayor_fullname
        return {
            "fullName": president,
            "givenName": "", "middleName": "", "lastName": "",
            "position": "College President",
            "individuals": {
                "review": {"name": president, "position": "College President", "date": ""},
                "approve": {"name": mayor, "position": "PMT Chairperson", "date": ""},
                "discuss": {"name": "", "position": "", "date": ""},
                "assess": {"name": "", "position": "Municipal Administrator", "date": ""},
                "final": {"name": mayor, "position": "PMT Chairperson", "date": ""},
                "confirm": {"name": mayor, "position": "PMT Chairperson", "date": ""},
            },
        }
