from app import db

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Integer, default=1)
    type = db.Column(db.String(50), default="Core Function")
    description = db.Column(db.Text, nullable=True)
    period = db.Column(db.String(100), nullable=True)
    priority_order = db.Column(db.Integer, default=0)

    main_tasks = db.relationship("Main_Task", back_populates="category")

    tasks = db.relationship("Task", back_populates="category")

    def get_category_avg_rating(self):
        rated = [t.get_task_avg_rating() for t in self.main_tasks if t.status == 1]
        return sum(rated) / len(rated) if rated else 0

    def _base_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "type": self.type,
            "period_id": self.period,
            "description": self.description,
            "task_count": len(self.main_tasks),
            "average_rating": self.get_category_avg_rating(),
            "priority_order": self.priority_order,
        }

    def info(self):
        return self._base_dict()

    def to_dict(self):
        return {**self._base_dict(), "main_tasks": [t.info() for t in self.main_tasks]}
