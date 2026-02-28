# CommitHub Database Dictionary

**Last Updated:** February 27, 2026  
**Project:** CommitHub Backend (IPCR/OPCR Management System)

---

## Table of Contents
1. [User Management Models](#user-management-models)
2. [Task & Work Models](#task--work-models)
3. [PCR Performance Models](#pcr-performance-models)
4. [Document & Support Models](#document--support-models)
5. [System Configuration Models](#system-configuration-models)

---

## User Management Models

### 1. **User** Table
**Purpose:** Stores all system users with roles and departmental assignments

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique user identifier |
| first_name | String(50) | NOT NULL | | User's first name |
| middle_name | String(50) | Nullable | "" | User's middle name |
| last_name | String(50) | NOT NULL | | User's last name |
| email | String(50) | UNIQUE, NOT NULL | | User's email address |
| password | String(250) | NOT NULL | "commithubnc" | Hashed password |
| profile_picture_link | Text | Nullable | | URL/path to profile picture |
| created_at | DateTime | | now() | Account creation timestamp |
| role | Enum | | "faculty" | Role: faculty, head, president, administrator |
| active_status | Boolean | | True | Whether user is active |
| account_status | Integer | | 1 | Account state (1=active, 0=inactive) |
| position_id | Integer | FK → positions.id | 1 | Reference to position |
| managed_dept_id | Integer | Nullable | | Department managed by user (for heads) |
| department_id | Integer | FK → departments.id | 1 | User's department |
| recovery_email | String(255) | Nullable | | Backup email for password recovery |
| two_factor_enabled | Boolean | | False | 2FA activation status |

**Relationships:**
- one-to-one: Position (position_id)
- one-to-many: Department (department_id)
- one-to-many: Output, IPCR, Notification, Assigned_Task

---

### 2. **Position** Table
**Purpose:** Defines job positions and their performance weights

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique position identifier |
| name | String(50) | NOT NULL | | Position title |
| core_weight | Float | | 0.0 | Weight for core function performance (0-1) |
| strategic_weight | Float | | 0.0 | Weight for strategic function performance (0-1) |
| support_weight | Float | | 0.0 | Weight for support function performance (0-1) |
| status | Integer | | 1 | Status (1=active, 0=archived) |

**Relationships:**
- one-to-many: User

---

### 3. **Department** Table
**Purpose:** Organizational departments and their structure

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique department identifier |
| name | String(50) | UNIQUE, NOT NULL | | Department name |
| icon | String(50) | | "" | Icon identifier/name |
| manager_id | Integer | | 0 | User ID of department manager |
| status | Integer | | 1 | Status (1=active, 0=archived) |

**Relationships:**
- one-to-many: User, OPCR, Assigned_Department, Assigned_PCR

---

### 4. **Notification** Table
**Purpose:** System notifications for users

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique notification identifier |
| name | Text | NOT NULL | | Notification message/content |
| user_id | Integer | FK → users.id | | Target user |
| created_at | DateTime | | now() | When notification was created |
| read | Boolean | | False | Read status |

**Relationships:**
- many-to-one: User (user_id)

---

### 5. **AdminConfirmation** Table
**Purpose:** Token-based admin action confirmation (2FA-like)

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique confirmation identifier |
| user_id | Integer | FK → users.id, NOT NULL | | User requesting confirmation |
| token | String(128) | UNIQUE, NOT NULL | | Random hex token |
| expires_at | DateTime | NOT NULL | | Token expiration time |
| used | Boolean | | False | Whether token has been used |
| created_at | DateTime | | now() | When token was created |

**Relationships:**
- many-to-one: User (user_id)

**Token Lifecycle:** Default 10 minutes expiration, one-time use

---

### 6. **LoginOTP** Table
**Purpose:** One-time passwords for 2FA login authentication

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique OTP record identifier |
| user_id | Integer | FK → users.id, NOT NULL | | User requesting OTP |
| otp_hash | String(128) | NOT NULL | | SHA256 hash of OTP + salt |
| salt | String(64) | NOT NULL | | Random salt for hashing |
| expires_at | DateTime | NOT NULL | | OTP expiration time |
| used | Boolean | | False | Whether OTP has been consumed |
| created_at | DateTime | | now() | When OTP was generated |

**Relationships:**
- many-to-one: User (user_id)

**Security:** Uses salted hashing, default 5-minute expiration

---

### 7. **Log** Table
**Purpose:** Audit trail of all system actions

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique log entry identifier |
| user_id | Integer | Nullable | | User who performed action |
| full_name | String(50) | NOT NULL | | Full name of actor |
| department | String(50) | NOT NULL | | Department of actor |
| created_at | DateTime | | now() | When action occurred |
| action | String(50) | NOT NULL | | Type of action (create, update, delete, etc.) |
| target | String(50) | NOT NULL | | What was affected (user, task, etc.) |
| description | Text | Nullable | | Detailed action description |
| ip_address | String(45) | Nullable | | Source IP address |
| user_agent | String(255) | Nullable | | Browser/client user agent |

**Relationships:** None (audit-only)

---

## Task & Work Models

### 8. **Category** Table
**Purpose:** Classifies main tasks (Core Function, Strategic, Support)

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique category identifier |
| name | String(50) | NOT NULL | | Category name |
| status | Integer | | 1 | Status (1=active, 0=archived) |
| type | String(50) | | "Core Function" | Category type classification |
| description | Text | Nullable | | Category description |
| period | String(100) | Nullable | | Associated performance period |
| priority_order | Integer | | 0 | Display order (0=highest priority) |

**Relationships:**
- one-to-many: Main_Task

---

### 9. **Main_Task** Table
**Purpose:** Primary tasks assigned to departments/categories

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique task identifier |
| mfo | Text | NOT NULL | | Major Final Output description |
| time_description | Text | NOT NULL | | Description of time requirements |
| modification | Text | NOT NULL | | Modification details |
| target_accomplishment | Text | NOT NULL | | Target accomplishment criteria |
| actual_accomplishment | Text | NOT NULL | | Actual accomplishment description |
| time_taken | Integer | | 0 | Time consumed (in days/hours) |
| modifications_done | Integer | | 0 | Count of modifications made |
| created_at | DateTime | | now() | Task creation date |
| status | Integer | | 1 | Status (1=active, 0=archived) |
| assigned | Boolean | | False | Whether task is assigned |
| accomplishment_editable | Boolean | | False | Can accomplishment be edited? |
| time_editable | Boolean | | False | Can time be edited? |
| modification_editable | Boolean | | False | Can modifications be edited? |
| require_documents | Boolean | | False | Are supporting documents required? |
| category_id | Integer | FK → categories.id | | Parent category |
| period | String(100) | Nullable | | Performance period |
| target_quantity | Integer | | 0 | Target quantity to accomplish |
| target_efficiency | Integer | | 0 | Target efficiency rating (1-5) |
| target_deadline | DateTime | Nullable | | Target completion deadline |
| target_timeframe | Integer | | 0 | Target timeframe (days/hours) |
| timeliness_mode | String(100) | | "timeframe" | Mode: "timeframe" or "deadline" |
| description | Text | Nullable | | Task description |

**Relationships:**
- many-to-one: Category (category_id)
- one-to-many: Assigned_Department, Sub_Task, Output, Assigned_Task

---

### 10. **Assigned_Task** Table
**Purpose:** Assignment of tasks to individual users

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique assignment identifier |
| user_id | Integer | FK → users.id | | Assigned user |
| main_task_id | Integer | FK → main_tasks.id | | Assigned task |
| is_assigned | Boolean | | False | Assignment confirmation status |
| batch_id | Text | | "" | Batch/group identifier |
| status | Integer | | 1 | Status (1=active, 0=inactive) |
| period | String(100) | Nullable | | Performance period |
| assigned_quantity | Integer | | 0 | Quantity assigned to user |

**Relationships:**
- many-to-one: User (user_id), Main_Task (main_task_id)

---

### 11. **Assigned_Department** Table
**Purpose:** Assignment of tasks to departments with performance weights

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique assignment identifier |
| department_id | Integer | FK → departments.id | | Target department |
| main_task_id | Integer | FK → main_tasks.id | | Task assigned |
| batch_id | Text | | "" | Batch identifier |
| period | Text | | "" | Performance period |
| task_weight | Float | | 0.0 | Weight of task in evaluation (0-100%) |
| quantity_formula | JSON | | {} | Custom quantity calculation formula |
| efficiency_formula | JSON | | {} | Custom efficiency calculation formula |
| timeliness_formula | JSON | | {} | Custom timeliness calculation formula |
| quantity | Integer | Nullable | | Quantity rating |
| efficiency | Integer | Nullable | | Efficiency rating |
| timeliness | Integer | Nullable | | Timeliness rating |
| enable_formulas | Boolean | | False | Use department-specific formulas? |

**Relationships:**
- many-to-one: Department (department_id), Main_Task (main_task_id)

---

### 12. **Output** Table
**Purpose:** User outputs for specific tasks during a period

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique output identifier |
| user_id | Integer | FK → users.id | | User who created output |
| main_task_id | Integer | FK → main_tasks.id | | Associated task |
| ipcr_id | Integer | FK → ipcr.id | | Parent IPCR record |
| batch_id | Text | | "" | Batch identifier |
| period | String(100) | Nullable | | Performance period |
| status | Integer | | 1 | Status (1=active, 0=inactive) |
| assigned_quantity | Integer | | 0 | Quantity assigned for this output |

**Relationships:**
- many-to-one: User (user_id), Main_Task (main_task_id), IPCR (ipcr_id)
- one-to-one: Sub_Task (auto-created with output)

**Auto-Behavior:** When created, automatically generates a Sub_Task record

---

### 13. **Sub_Task** Table
**Purpose:** Detailed breakdown of output metrics (quantity, efficiency, timeliness)

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique subtask identifier |
| mfo | Text | NOT NULL | | Major Final Output reference |
| target_acc | Integer | | 0 | Target accomplishment quantity |
| target_time | Integer | | 0 | Target time duration |
| target_mod | Integer | | 0 | Target modifications count |
| actual_acc | Integer | | 0 | Actual accomplishment quantity |
| actual_time | Integer | | 0 | Actual time spent |
| actual_mod | Integer | | 0 | Actual modifications made |
| created_at | DateTime | | now() | Creation timestamp |
| status | Integer | | 1 | Status (1=active, 0=inactive) |
| quantity | Integer | | 0 | Computed quantity rating (1-5) |
| efficiency | Integer | | 0 | Computed efficiency rating (1-5) |
| timeliness | Integer | | 0 | Computed timeliness rating (1-5) |
| average | Integer | | 0 | Average of three ratings |
| output_id | Integer | FK → outputs.id, UNIQUE | | Parent output (one-to-one) |
| main_task_id | Integer | FK → main_tasks.id | | Reference to main task |
| ipcr_id | Integer | FK → ipcr.id | | Parent IPCR |
| period | String(100) | Nullable | | Performance period |
| batch_id | Text | NOT NULL | | Batch identifier |
| assigned_quantity | Integer | | 0 | Quantity assigned |
| actual_deadline | DateTime | Nullable | | When task was actually completed |

**Relationships:**
- one-to-one: Output (output_id)
- many-to-one: Main_Task (main_task_id), IPCR (ipcr_id)
- one-to-many: Supporting_Document

**Rating Calculation:** Ratings computed using Formula_Engine based on formulas in System_Settings

---

## PCR Performance Models

### 14. **IPCR** Table
**Purpose:** Individual Performance Commitment Review - per user performance evaluation

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique IPCR identifier |
| user_id | Integer | FK → users.id | | Employee being evaluated |
| opcr_id | Integer | FK → opcr.id, Nullable | | Parent organizational PCR |
| isMain | Boolean | | False | Is this the main IPCR? |
| status | Integer | | 1 | Status (1=active, 0=archived) |
| form_status | Text | | "draft" | Form state: draft, submitted, approved, etc. |
| batch_id | Text | | "" | Batch identifier |
| period | String(100) | Nullable | | Performance period |
| created_at | DateTime | | now() | Creation date |
| **Signatory Fields** | | | | |
| reviewed_by | Text | | "" | Reviewer's name |
| rev_position | Text | | "" | Reviewer's position |
| rev_date | DateTime | Nullable | | Review date |
| approved_by | Text | | "" | Approver's name |
| app_position | Text | | "" | Approver's position |
| app_date | DateTime | Nullable | | Approval date |
| discussed_with | Text | | "" | Discussion participant name |
| dis_position | Text | | "" | Discussion participant position |
| dis_date | DateTime | Nullable | | Discussion date |
| assessed_by | Text | | "" | Assessor's name |
| ass_position | Text | | "" | Assessor's position |
| ass_date | DateTime | Nullable | | Assessment date |
| final_rating_by | Text | | "" | Final rater's name |
| fin_position | Text | | "" | Final rater's position |
| fin_date | DateTime | Nullable | | Final rating date |
| confirmed_by | Text | | "" | Confirmer's name |
| con_position | Text | | "" | Confirmer's position |
| con_date | DateTime | Nullable | | Confirmation date |

**Relationships:**
- many-to-one: User (user_id), OPCR (opcr_id)
- one-to-many: Sub_Task, Output, Supporting_Document, Assigned_PCR

**Workflow:** Faculty → Head Review → President Approval → Discussion → Assessment → Final Rating → Confirmation

---

### 15. **OPCR** Table
**Purpose:** Organizational Performance Commitment Review - department-level evaluation

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique OPCR identifier |
| department_id | Integer | FK → departments.id | | Parent department |
| isMain | Boolean | | False | Is this the main OPCR? |
| status | Integer | | 1 | Status (1=active, 0=archived) |
| form_status | Text | | "draft" | Form state: draft, submitted, approved, etc. |
| created_at | DateTime | | now() | Creation date |
| period | String(100) | Nullable | | Performance period |
| **Signatory Fields** | | | | |
| reviewed_by | Text | | "" | Reviewer's name |
| rev_position | Text | | "" | Reviewer's position |
| rev_date | DateTime | Nullable | | Review date |
| approved_by | Text | | "" | Approver's name |
| app_position | Text | | "" | Approver's position |
| app_date | DateTime | Nullable | | Approval date |
| discussed_with | Text | | "" | Discussion participant |
| dis_position | Text | | "" | Participant position |
| dis_date | DateTime | Nullable | | Discussion date |
| assessed_by | Text | | "" | Assessor's name |
| ass_position | Text | | "" | Assessor's position |
| ass_date | DateTime | Nullable | | Assessment date |
| final_rating_by | Text | | "" | Final rater's name |
| fin_position | Text | | "" | Final rater's position |
| fin_date | DateTime | Nullable | | Final rating date |
| confirmed_by | Text | | "" | Confirmer's name |
| con_position | Text | | "" | Confirmer's position |
| con_date | DateTime | Nullable | | Confirmation date |

**Relationships:**
- many-to-one: Department (department_id)
- one-to-many: IPCR, OPCR_Rating, OPCR_Supporting_Document, Assigned_PCR

---

---

### 17. **Assigned_PCR** Table
**Purpose:** Junction table linking IPCR, OPCR, and Department

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique assignment identifier |
| ipcr_id | Integer | FK → ipcr.id, Nullable | | Individual PCR |
| opcr_id | Integer | FK → opcr.id, Nullable | | Organizational PCR |
| department_id | Integer | FK → departments.id, Nullable | | Department |
| period | String(100) | Nullable | | Performance period |

**Relationships:**
- many-to-one: IPCR (ipcr_id), OPCR (opcr_id), Department (department_id)

**Purpose:** Tracks which IPCRs and OPCRs are active per department and period

---

## Document & Support Models

### 18. **Supporting_Document** Table
**Purpose:** Supporting evidence documents for individual task completion

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique document identifier |
| file_type | Text | | "" | File MIME type (pdf, doc, etc.) |
| file_name | Text | | "" | Original filename |
| ipcr_id | Integer | FK → ipcr.id, Nullable | | Parent IPCR |
| sub_task_id | Integer | FK → sub_tasks.id, Nullable | | Associated subtask |
| batch_id | Text | | "" | Batch identifier |
| status | Integer | | 1 | Status (1=active, 0=deleted) |
| period | String(100) | Nullable | | Performance period |

**Relationships:**
- many-to-one: IPCR (ipcr_id), Sub_Task (sub_task_id)

**Storage:** Files stored in cloud storage, references stored in DB

---

## System Configuration Models

### 20. **System_Settings** Table
**Purpose:** Global system configuration and performance period settings (Singleton)

| Column | Data Type | Constraints | Default | Description |
|--------|-----------|-------------|---------|-------------|
| id | Integer | PK, Auto-increment | | Unique settings record (only 1) |
| **Rating Threshold Configuration** | | | | |
| rating_thresholds | JSON | NOT NULL | {} | Rating scale mappings (outstanding, satisfactory, etc.) |
| **Formula Configuration** | | | | |
| quantity_formula | JSON | | {} | Global quantity calculation formula |
| efficiency_formula | JSON | | {} | Global efficiency calculation formula |
| timeliness_formula | JSON | | {} | Global timeliness calculation formula |
| **Period Configuration** | | | | |
| current_period | String(100) | Nullable | | Current active period identifier |
| current_period_id | String(100) | Nullable | | Current period ID |
| current_phase | String(100) | Nullable | | Current phase (planning, monitoring, rating) |
| planning_start_date | Date | Nullable | | Planning phase start |
| planning_end_date | Date | Nullable | | Planning phase end |
| monitoring_start_date | Date | Nullable | | Monitoring phase start |
| monitoring_end_date | Date | Nullable | | Monitoring phase end |
| rating_start_date | Date | Nullable | | Rating phase start |
| rating_end_date | Date | Nullable | | Rating phase end |
| **Organization Officials** | | | | |
| current_president_fullname | String(255) | Nullable | | President's name |
| current_mayor_fullname | String(255) | Nullable | | Mayor/Executive's name |
| **Metadata** | | | | |
| created_at | DateTime | | now() | Creation timestamp |
| updated_at | DateTime | | now() | Last update timestamp |

**Relationships:** None (singleton configuration)

**Usage Pattern:** Only one record should exist; use `System_Settings.get_default_settings()` to retrieve

---

## Enum Types

### User Roles
```
- "faculty": Regular employee
- "head": Department head/manager
- "president": College/Organization president
- "administrator": System administrator
```

### Status Codes
```
- 1: Active
- 0: Inactive/Archived
```

### Form States
```
- "draft": Being prepared
- "submitted": Awaiting review
- "reviewed": Reviewed by supervisor
- "approved": Approved by authority
- "completed": Finalized
```

---

## Key Relationships Summary

### Data Flow: Task Assignment to Evaluation
```
Category
  ↓
Main_Task → Assigned_Department (assigns to department)
  ↓
Assigned_Task (assigns to user)
  ↓
Output (user creates output)
  ↓
Sub_Task (auto-created, contains metrics)
  ↓
IPCR (individual performance review)
  ↓
OPCR (organizational performance review)
  ↓
OPCR_Rating (department-level rating)
```

### Evaluation Workflow
```
IPCR Signatory Chain:
User → Reviewed (Head) → Approved (President) → 
Discussed → Assessed → Final Rating → Confirmed (Mayor)
```

---

## Indexes Recommended
- `users.email` (UNIQUE)
- `users.role` (frequently filtered)
- `main_tasks.category_id`
- `ipcr.user_id`, `ipcr.period`
- `opcr.department_id`, `opcr.period`
- `sub_tasks.ipcr_id`, `sub_tasks.main_task_id`
- `logs.created_at` (for audit queries)

---

## Notes
- All timestamps use `datetime.now()` for UTC consistency
- Foreign keys use CASCADE delete for dependent records
- JSON columns store formulas and configurations
- Period is String(100) to support flexible period naming (e.g., "2025-Q1", "2025-2026")
- Formula_Engine handles dynamic rating calculations

