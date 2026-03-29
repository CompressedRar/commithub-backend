from models.Formula_engine import Formula_Engine


class PCRRatingService:

    def compute_rating_with_override(metric, target, actual, task_id, settings, dept_configs):
        engine = Formula_Engine()
        dept_cfg = dept_configs.get(task_id)
        formula = dept_cfg[metric] if (dept_cfg and dept_cfg["enable"]) else getattr(settings, f"{metric}_formula")
        res = engine.compute_rating(formula=formula, target=target, actual=actual)
        return res if res is not None else 0

    def compute_quantity_rating(target, actual, settings):
        return Formula_Engine().compute_rating(
            formula=settings.quantity_formula, target=target, actual=actual
        )

    def compute_efficiency_rating(target, actual, settings):
        return Formula_Engine().compute_rating(
            formula=settings.efficiency_formula, target=target, actual=actual
        )

    def compute_timeliness_rating(target, actual, settings):
        return Formula_Engine().compute_rating(
            formula=settings.timeliness_formula, target=target, actual=actual
        )

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
        q = min(quantity, 5)
        e = min(efficiency, 5)
        t = min(timeliness, 5)
        return float((q + e + t) / 3)
