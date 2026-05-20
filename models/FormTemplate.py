from app import db
from datetime import datetime
import json


class FormTemplate(db.Model):
    """
    Represents a form template with configuration, fields, and layout.
    Stores the template structure for creating dynamic forms.
    """
    __tablename__ = "form_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Form configuration (stored as JSON)
    logo_url = db.Column(db.Text, nullable=True)
    
    # Grid configuration (rows, columns)
    grid_rows = db.Column(db.Integer, default=3)
    grid_columns = db.Column(db.Integer, default=3)
    
    # Field mapping configuration (JSON: grid layout with field positions and spans)
    field_mapping = db.Column(db.JSON, nullable=True)
    column_mapping = db.Column(db.JSON, nullable=True)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)
    
    # Relationships
    creator = db.relationship("User", backref="form_templates")
    input_fields = db.relationship("FormInputField", back_populates="template", cascade="all, delete-orphan")
    output_fields = db.relationship("FormOutputField", back_populates="template", cascade="all, delete-orphan")
    submissions = db.relationship("FormSubmission", back_populates="template", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Serialize template to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "logo_url": self.logo_url,
            "grid_rows": self.grid_rows,
            "grid_columns": self.grid_columns,
            "field_mapping": self.field_mapping,
            "column_mapping": self.column_mapping,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "is_published": self.is_published,
            "input_fields": [f.to_dict() for f in self.input_fields],
            "output_fields": [f.to_dict() for f in self.output_fields],
        }
    
    def to_dict_summary(self):
        """Serialize template summary with essential fields for template listing"""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "is_published": self.is_published,
            "inputFields": [f.to_dict() for f in self.input_fields],
        }


class FormInputField(db.Model):
    """
    Represents an input field in a form template.
    These are fields where users/admins provide data.
    """
    __tablename__ = "form_input_fields"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("form_templates.id"), nullable=False)
    
    # Field configuration
    field_id = db.Column(db.String(50), nullable=False)  # Unique within template (e.g., "field_1234567890")
    title = db.Column(db.String(255), nullable=False)
    placeholder = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    name = db.Column(db.String(100), nullable=True)  # Database field name for user inputs
    
    # Field type: String, Integer, Number, Email, Date, Boolean, TextArea, Dropdown, etc.
    field_type = db.Column(db.String(50), nullable=False)
    
    # User type: Admin or User
    user_type = db.Column(db.String(50), default="Admin", nullable=False)
    
    # Validation rules
    is_required = db.Column(db.Boolean, default=False)
    validation_rules = db.Column(db.JSON, nullable=True)  # e.g., {"min": 0, "max": 100, "pattern": "..."}
    
    # Display configuration
    order = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    template = db.relationship("FormTemplate", back_populates="input_fields")
    field_values = db.relationship("FormFieldValue", back_populates="input_field", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Serialize input field to dictionary"""
        return {
            "id": self.id,
            "field_id": self.field_id,
            "title": self.title,
            "placeholder": self.placeholder,
            "description": self.description,
            "name": self.name,
            "type": self.field_type,
            "user": self.user_type,
            "required": self.is_required,
            "validation_rules": self.validation_rules,
            "order": self.order,
        }


class FormOutputField(db.Model):
    """
    Represents an output/computed field in a form template.
    These are fields computed from input fields (e.g., calculations, case statements).
    """
    __tablename__ = "form_output_fields"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("form_templates.id"), nullable=False)
    
    # Field configuration
    field_id = db.Column(db.String(50), nullable=False)  # Unique within template
    title = db.Column(db.String(255), nullable=False)
    
    # Output field type: IntegerModifier, CaseOutput, etc.
    output_type = db.Column(db.String(50), nullable=False)
    
    # Reference to input field (if applicable)
    input_field_name = db.Column(db.String(100), nullable=True)
    
    # Configuration based on output type
    formula = db.Column(db.Text, nullable=True)  # For IntegerModifier
    cases = db.Column(db.JSON, nullable=True)    # For CaseOutput: [{"condition": "...", "result": "..."}]
    
    # Display configuration
    order = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    template = db.relationship("FormTemplate", back_populates="output_fields")
    
    def to_dict(self):
        """Serialize output field to dictionary"""
        return {
            "id": self.id,
            "field_id": self.field_id,
            "title": self.title,
            "type": self.output_type,
            "input_field_name": self.input_field_name,
            "formula": self.formula,
            "cases": self.cases,
            "order": self.order,
        }


class FormSubmission(db.Model):
    """
    Represents a user's submission of a form.
    Contains references to the filled field values.
    """
    __tablename__ = "form_submissions"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("form_templates.id"), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Submission metadata
    submission_date = db.Column(db.DateTime, default=datetime.now)
    is_draft = db.Column(db.Boolean, default=False)  # Whether submission is saved as draft
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    template = db.relationship("FormTemplate", back_populates="submissions")
    submitted_user = db.relationship("User", backref="form_submissions")
    field_values = db.relationship("FormFieldValue", back_populates="submission", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Serialize submission to dictionary"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "submitted_by": self.submitted_by,
            "submission_date": self.submission_date.isoformat(),
            "is_draft": self.is_draft,
            "field_values": [fv.to_dict() for fv in self.field_values],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class FormFieldValue(db.Model):
    """
    Represents a single field value in a form submission.
    Links field values to their input field definitions.
    """
    __tablename__ = "form_field_values"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("form_submissions.id"), nullable=False)
    input_field_id = db.Column(db.Integer, db.ForeignKey("form_input_fields.id"), nullable=False)
    
    # Field value (stored as JSON to support various types)
    value = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    submission = db.relationship("FormSubmission", back_populates="field_values")
    input_field = db.relationship("FormInputField", back_populates="field_values")
    
    def to_dict(self):
        """Serialize field value to dictionary"""
        return {
            "id": self.id,
            "input_field_id": self.input_field_id,
            "field_name": self.input_field.title if self.input_field else None,            
            "value": self.value,
        }


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("form_templates.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Store ADMIN field values
    values = db.Column(db.JSON, nullable=True)

    user_input_fields = db.relationship("FormInputField", secondary="form_templates", primaryjoin="Task.template_id==FormTemplate.id", secondaryjoin="FormInputField.template_id==FormTemplate.id", viewonly=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    template = db.relationship("FormTemplate")
    responses = db.relationship("TaskResponse", back_populates="task", cascade="all, delete-orphan")

    category = db.relationship("Category", back_populates="tasks")

    def to_dict(self):

        return {
            "id": self.id,
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "values": self.values,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "input_fields": [
                f.to_dict()
                for f in self.template.input_fields
                if f.user_type == "User"
            ]   
        }

class TaskResponse(db.Model):
    """
    Represents a user's submission of a form.
    Contains references to the filled field values.
    """
    __tablename__ = "task_responses"

    id = db.Column(db.Integer, primary_key=True)
    submitted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    values = db.Column(db.JSON, nullable=True)  # Store all field values as JSON for easy access
    
    # Relationships
    submitted_user = db.relationship("User", back_populates="task_responses")
    task = db.relationship("Task", back_populates="responses")

    def to_dict(self):
        """Serialize submission to dictionary"""
        return {
            "id": self.id,
            "submitted_by": self.submitted_by,
            "values": self.values,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class TaskAssignment(db.Model):
    __tablename__ = "task_assignments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    task = db.relationship("Task", backref="assignments")
    user = db.relationship("User", backref="task_assignments")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }