# Form Builder Integration - Backend Setup Guide

## Overview

The form builder backend implementation follows **Separation of Concerns (SoC)** principles with clearly defined layers:

- **Models Layer** (`backend/models/FormTemplate.py`): Database schema and data structures
- **Services Layer** (`backend/services/FormTemplate*Service.py`): Business logic and validation
- **Routes Layer** (`backend/routes/FormTemplate*.py`): API endpoints

## Database Schema

### Tables Created

1. **form_templates** - Stores form template configurations
2. **form_input_fields** - Stores input fields for each template
3. **form_output_fields** - Stores computed/output fields
4. **form_submissions** - Stores user submissions
5. **form_field_values** - Stores field values for each submission

## Setup Instructions

### 1. Database Migration

Run the following commands from the `backend/` directory:

```bash
# Create migration
flask db migrate -m "Add form builder tables"

# Apply migration
flask db upgrade
```

This will create all necessary tables in your database.

### 2. Model Documentation

#### FormTemplate
Represents a form template with its complete configuration.

**Key Fields:**
- `id`: Primary key
- `name`: Unique template name
- `title`: Display title
- `subtitle`: Optional subtitle
- `description`: Optional description
- `logo_url`: Optional logo URL
- `grid_rows`, `grid_columns`: Grid layout configuration
- `field_mapping`: JSON field layout mapping
- `created_by`: User ID of creator
- `is_published`: Whether template is published for submissions
- `input_fields`: Relationship to input fields
- `output_fields`: Relationship to output fields
- `submissions`: Relationship to submissions

#### FormInputField
Represents an input field in a template.

**Key Fields:**
- `template_id`: Reference to parent template
- `field_id`: Unique field ID within template
- `title`: Field label
- `field_type`: String, Integer, Number, Email, Date, Boolean, TextArea, Dropdown
- `user_type`: Admin or User
- `is_required`: Required field flag
- `validation_rules`: JSON validation rules (min, max, pattern)

#### FormOutputField
Represents a computed field (e.g., formula calculation, case statement).

**Key Fields:**
- `template_id`: Reference to parent template
- `output_type`: IntegerModifier, CaseOutput, etc.
- `formula`: Formula string for calculations
- `cases`: JSON array of case conditions and results

#### FormSubmission
Represents a user's form submission.

**Key Fields:**
- `template_id`: Reference to template
- `submitted_by`: User ID of submitter
- `is_draft`: Draft submission flag
- `field_values`: Relationship to individual field values

#### FormFieldValue
Represents a single field value in a submission.

**Key Fields:**
- `submission_id`: Reference to submission
- `input_field_id`: Reference to field definition
- `value`: JSON-stored field value

## API Endpoints

### Form Templates

#### Create Template
```
POST /api/v1/form-templates
Authorization: Bearer <token>
Requires: administrator, head roles
```

**Request Body:**
```json
{
  "name": "template_unique_name",
  "title": "Template Title",
  "subtitle": "Optional subtitle",
  "description": "Optional description",
  "logoUrl": "https://...",
  "gridRows": 3,
  "gridColumns": 3,
  "fieldMapping": {},
  "inputFields": [
    {
      "id": "field_1",
      "title": "Field Name",
      "placeholder": "Enter value...",
      "type": "String",
      "user": "Admin",
      "required": true
    }
  ],
  "outputFields": [
    {
      "id": "output_1",
      "title": "Total Score",
      "type": "IntegerModifier",
      "formula": "field_1 * 2"
    }
  ]
}
```

#### Get Template
```
GET /api/v1/form-templates/{id}
Authorization: Bearer <token>
```

#### List Templates
```
GET /api/v1/form-templates?skip=0&limit=20&active=true
Authorization: Bearer <token>
```

#### Update Template
```
PUT /api/v1/form-templates/{id}
Authorization: Bearer <token>
Requires: administrator, head roles
```

#### Delete Template
```
DELETE /api/v1/form-templates/{id}
Authorization: Bearer <token>
Requires: administrator role
```

#### Publish Template
```
POST /api/v1/form-templates/{id}/publish
Authorization: Bearer <token>
Requires: administrator, head roles
```

#### Duplicate Template
```
POST /api/v1/form-templates/{id}/duplicate
Authorization: Bearer <token>
Requires: administrator, head roles

Request Body:
{
  "name": "new_template_name"
}
```

### Form Submissions

#### Create Submission
```
POST /api/v1/form-submissions
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "template_id": 1,
  "fieldValues": {
    "field_1": "value1",
    "field_2": "value2"
  },
  "isDraft": false
}
```

#### Get Submission
```
GET /api/v1/form-submissions/{id}
Authorization: Bearer <token>
```

#### Get Template Submissions
```
GET /api/v1/form-submissions/template/{template_id}?skip=0&limit=20&includeDrafts=false
Authorization: Bearer <token>
Requires: administrator, head roles
```

#### Get User Submissions
```
GET /api/v1/form-submissions/user/{user_id}?templateId=1&skip=0&limit=20
Authorization: Bearer <token>
```

#### Update Submission
```
PUT /api/v1/form-submissions/{id}
Authorization: Bearer <token>

Request Body:
{
  "fieldValues": {
    "field_1": "updated_value"
  },
  "isDraft": false
}
```

#### Delete Submission
```
DELETE /api/v1/form-submissions/{id}
Authorization: Bearer <token>
```

#### Get Submission Stats
```
GET /api/v1/form-submissions/template/{template_id}/stats
Authorization: Bearer <token>
Requires: administrator, head roles
```

## Service Layer

### FormTemplateService

**Methods:**
- `create_template(data, created_by)` - Create new template
- `get_template(template_id)` - Get template by ID
- `get_all_templates(skip, limit, is_active)` - List templates with pagination
- `update_template(template_id, data)` - Update template
- `delete_template(template_id)` - Delete template
- `publish_template(template_id)` - Publish template

### FormSubmissionService

**Methods:**
- `validate_field_value(input_field, value)` - Validate field value
- `create_submission(template_id, submitted_by, field_values, is_draft)` - Create submission
- `get_submission(submission_id)` - Get submission by ID
- `get_template_submissions(template_id, skip, limit, include_drafts)` - List template submissions
- `get_user_submissions(user_id, template_id, skip, limit)` - List user submissions
- `update_submission(submission_id, field_values, is_draft)` - Update submission
- `delete_submission(submission_id)` - Delete submission
- `get_submission_stats(template_id)` - Get submission statistics

## Features

### Field Validation

The system supports multiple validation types:

1. **Type Validation** - Ensures values match field type (String, Integer, Email, etc.)
2. **Required Fields** - Checks if required fields are populated
3. **Custom Rules** - Pattern matching, min/max values for numeric fields
4. **Email Validation** - Basic email format checking

### Draft Support

Forms can be saved as drafts for later completion using the `isDraft` flag.

### Audit Logging

All CRUD operations are logged using the `@log_action` decorator:
- CREATE_FORM_TEMPLATE
- UPDATE_FORM_TEMPLATE
- DELETE_FORM_TEMPLATE
- CREATE_FORM_SUBMISSION
- UPDATE_FORM_SUBMISSION
- DELETE_FORM_SUBMISSION

## Frontend Integration

The frontend should:

1. Use the form builder component to create templates
2. Send template data to `POST /api/v1/form-templates`
3. On form submission, send data to `POST /api/v1/form-submissions`
4. Support draft saving via `isDraft` flag
5. Retrieve submissions via `GET /api/v1/form-submissions/user/{userId}`

## Error Handling

All endpoints return appropriate HTTP status codes:

- `400` - Bad request (validation error)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not found
- `409` - Conflict (duplicate name, etc.)
- `500` - Server error

Error responses include detailed error messages:

```json
{
  "error": "Description of the error",
  "errors": ["Detailed error 1", "Detailed error 2"]
}
```

## Architecture Principles

### 1. Separation of Concerns
- **Models**: Data structure and relationships
- **Services**: Business logic, validation, error handling
- **Routes**: HTTP interface, request/response handling

### 2. Modularity
- Independent blueprint registration
- Standalone service classes
- Clear dependencies between layers

### 3. Scalability
- Pagination support
- Efficient queries
- JSON field support for flexible data

### 4. Security
- Role-based access control
- Token-based authentication
- Input validation at service layer
- Audit logging

## Future Enhancements

1. **Advanced Validation** - Regex patterns, cross-field validation
2. **Computed Fields** - Auto-calculation of output fields
3. **Field Versioning** - Track template changes
4. **Submission Export** - CSV/Excel export of submissions
5. **Templates Library** - Share templates across departments
6. **Conditional Fields** - Show/hide fields based on values
7. **File Uploads** - Support file field types
8. **Webhooks** - Trigger actions on submission

## Troubleshooting

### Migration Issues

If migration fails, ensure:
1. Database connection is working
2. All model imports are correct
3. SQLAlchemy is properly configured in app.py

### Validation Errors

Check:
1. Field types match expected values
2. Required fields are included
3. Numeric values are properly formatted

### Authorization Errors

Verify:
1. User has required role
2. JWT token is valid
3. Authorization header is properly formatted
