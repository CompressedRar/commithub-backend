from simpleeval import SimpleEval


class Formula_Engine:

    def _safe_eval(self, expression, variables):
        s = SimpleEval()
        s.names = variables
        s.functions = {}
        return float(s.eval(expression))

    def validate_formula(self, formula):
        """
        Validates formula structure, expression, and rating rules.
        Raises ValueError if invalid.
        """
        if "expression" not in formula:
            raise ValueError("Missing 'expression'")

        if "rating_scale" not in formula:
            raise ValueError("Missing 'rating_scale'")

        if not isinstance(formula["rating_scale"], dict):
            raise ValueError("'rating_scale' must be an object")

        self._validate_expression(formula["expression"])
        self._validate_rating_scale(formula["rating_scale"])
        self._dry_run(formula)

        return "Valid JSON"

    def _dry_run(self, formula):
        test_cases = [
            {"actual": 0, "target": 0},
            {"actual": 1, "target": 1},
            {"actual": 5, "target": 10},
            {"actual": 10, "target": 5},
        ]

        for case in test_cases:
            try:
                calc = self._safe_eval(formula["expression"], case)
                matched = any(
                    self._match_rules(calc, rules)
                    for rules in formula["rating_scale"].values()
                )
                if not matched:
                    raise ValueError("No rating matched for test case")
            except Exception as e:
                raise ValueError(f"Dry run failed: {str(e)}")

    def _validate_expression(self, expression):
        s = SimpleEval()
        s.names = {"actual": 1, "target": 1}
        s.functions = {}

        try:
            s.eval(expression)
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")

    def _validate_rating_scale(self, rating_scale):
        allowed_ops = {"lt", "lte", "gt", "gte", "eq"}

        for rating, rules in rating_scale.items():
            if not rating.isdigit():
                raise ValueError(f"Invalid rating key: {rating}")

            if not isinstance(rules, dict):
                raise ValueError(f"Rules for rating {rating} must be an object")

            for op, value in rules.items():
                if op not in allowed_ops:
                    raise ValueError(f"Invalid operator '{op}' in rating {rating}")
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Invalid value for rating {rating}")

    def _validate_no_overlap(self, rating_scale):
        ranges = []

        for rating, rules in rating_scale.items():
            low = float("-inf")
            high = float("inf")

            if "gt" in rules:
                low = rules["gt"]
            if "gte" in rules:
                low = rules["gte"]
            if "lt" in rules:
                high = rules["lt"]
            if "lte" in rules:
                high = rules["lte"]

            ranges.append((low, high, rating))

        ranges.sort()

        for i in range(len(ranges) - 1):
            curr_high = ranges[i][1]
            next_low = ranges[i + 1][0]

            if curr_high > next_low:
                raise ValueError(
                    f"Rating ranges overlap between {ranges[i][2]} and {ranges[i + 1][2]}"
                )

    def compute_rating(self, formula, target, actual):
        s = SimpleEval()
        s.names = {"target": target, "actual": actual}
        s.functions = {}

        try:
            calc = float(s.eval(formula["expression"]))
        except Exception as e:
            raise ValueError(f"Invalid Expression: {str(e)}")

        for rating, rules in formula["rating_scale"].items():
            if self._match_rules(calc, rules):
                return int(rating)

    def _match_rules(self, calc, rules):
        if "eq" in rules and calc != rules["eq"]:
            return False
        if "lt" in rules and not calc < rules["lt"]:
            return False
        if "lte" in rules and not calc <= rules["lte"]:
            return False
        if "gt" in rules and not calc > rules["gt"]:
            return False
        if "gte" in rules and not calc >= rules["gte"]:
            return False
        return True
