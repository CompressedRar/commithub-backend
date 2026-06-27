# CommitHub Backend Setup Guide

## Overview

The CommitHub backend uses a multi-script approach to initialize a fresh database with foundation data. This guide explains the seeding process, available tools, and how to verify your setup.

## Architecture & Dependency Order

The backend database has **34 models organized in 8 dependency levels**. Data must be created in a specific order to maintain referential integrity:

### Setup Sequence

1. **Level 0: Foundation** (No dependencies)
   - `System_Settings` — Global configuration, rating scales, alert thresholds
   - `Position` — Job roles (Faculty, Office Head, College President, Super Admin)
   - `Category` — Task classifications (Core Function, Strategic, Support)
   - `Department` — Organizational structure

2. **Level 1: Authentication** (Depends on Level 0)
   - `Profile` — Login credentials and authentication account
   - `User` — Individual user accounts linked to profiles

3. **Level 2+: Business Logic** (Depends on Levels 0-1)
   - Tasks, Performance Reviews (IPCR/OPCR), Forms, Analytics, etc.

## Available Tools

### 1. Standalone Seed Script (`seed_database.py`)

**Purpose:** Initialize a fresh database with interactive setup prompts.

**Usage:**
```bash
python seed_database.py
```

**Features:**
- ✓ Interactive prompts for organization details
- ✓ Automatic table creation
- ✓ Complete foundation data setup
- ✓ Password hashing (Argon2)
- ✓ Data validation & verification
- ✓ Automatic rollback on error
- ✓ Colored terminal output with progress indicators

**What It Creates:**
```
System Settings (1)
├── Rating thresholds (1-5 scale)
├── Alert thresholds (qty/efficiency/timeliness)
├── Period dates (planning/monitoring/rating phases)
└── Organization leadership names

Positions (4)
├── Faculty
├── Office Head
├── College President
└── Super Admin

Categories (3)
├── Core Function
├── Strategic
└── Support

Department (1)
└── Root organization department

Admin Account
├── Profile (email + hashed password)
└── User (Administrator role)
```

**Interactive Prompts:**
```
Organization name:                    [College]
College President's full name:        [Dr. Juan dela Cruz]
Administrative officer's full name:   [Maria Santos]
Admin account email:                  [admin@commithub.local]
```

### 2. Flask CLI Commands

**Purpose:** Run setup and verification from Flask CLI.

#### Command: `flask seed-db`
```bash
flask seed-db
```
- Interactive setup (same as standalone script)
- Integrated with Flask environment
- Auto-rollback on errors
- Can run from project root

#### Command: `flask verify-db`
```bash
flask verify-db
```
- Quick verification of database state
- Checks all foundation tables
- Verifies expected data counts
- Validates admin account
- Returns exit code (0=pass, 1=fail)

### 3. Verification Script (`verify_setup.py`)

**Purpose:** Comprehensive database integrity checks (post-setup or anytime).

**Usage:**
```bash
python verify_setup.py
```

**Checks Performed:**

| Category | Checks |
|----------|--------|
| **Table Existence** | All required tables exist |
| **Data Counts** | Expected record counts per table |
| **Foundation Data** | Specific positions, categories, settings |
| **Foreign Keys** | No orphaned records (referential integrity) |
| **Unique Constraints** | No duplicate emails, department names, positions |
| **Admin Account** | Administrator exists with valid profile |
| **System Status** | Overall readiness for production |

**Output Example:**
```
✓ PASS: Table 'profiles' exists (3 records)
✓ PASS: System Settings count = 1
✓ PASS: Position 'Faculty' exists
✓ PASS: All users have valid references
✗ FAIL: Current phase not set
```

## Step-by-Step Setup (Fresh Database)

### 1. Ensure Database Exists
```bash
# Via MySQL CLI
mysql -u root -p
> CREATE DATABASE commithub_production;
> EXIT;
```

### 2. Set Environment Variables
```bash
# .env file
LOCAL_DATABASE_URL=mysql+pymysql://root:password@localhost:3305/commithub_production
```

### 3. Run Migrations
```bash
flask db upgrade
# OR
alembic upgrade head
```

### 4. Run Seed Script
```bash
# Option A: Standalone script (recommended for clean setup)
python seed_database.py

# Option B: Flask CLI (if you prefer CLI approach)
flask seed-db
```

### 5. Verify Setup
```bash
# Comprehensive verification
python verify_setup.py

# OR Quick CLI verification
flask verify-db
```

### 6. Start Server
```bash
python app.py
# OR
flask run
```

### 7. Login
```
Email:    admin@commithub.local (or your chosen email)
Password: commithubnc
```

**⚠ Change password immediately after first login!**

## Data Model Summary

### System_Settings
Singleton configuration for the entire system:
```python
{
    "rating_thresholds": {
        "1": {"min": 0, "max": 1.5, "label": "Poor"},
        "2": {"min": 1.5, "max": 2.5, "label": "Below Average"},
        "3": {"min": 2.5, "max": 3.5, "label": "Average"},
        "4": {"min": 3.5, "max": 4.5, "label": "Good"},
        "5": {"min": 4.5, "max": 5, "label": "Excellent"}
    },
    "alert_thresholds": {
        "quantity": {"warning": 70, "critical": 50},
        "efficiency": {"warning": 70, "critical": 50},
        "timeliness": {"warning": 70, "critical": 50}
    },
    "current_period_id": "2024-Q1",
    "current_president_fullname": "Dr. Juan dela Cruz",
    "planning_start_date": "2024-01-01",
    "planning_end_date": "2024-03-31",
    "monitoring_start_date": "2024-04-01",
    "monitoring_end_date": "2024-09-30",
    "rating_start_date": "2024-10-01",
    "rating_end_date": "2024-12-31",
    "enable_formula": False
}
```

### User Roles
Four predefined roles with hierarchical permissions:

| Role | Title | Permissions |
|------|-------|-------------|
| `administrator` | Super Admin | All system operations |
| `president` | College President | All organizational operations |
| `head` | Office Head | Department-level operations |
| `faculty` | Faculty Member | Personal operations only |

### User Hierarchy
```
Root Department (College)
└── Super Admin (administrator)
    ├── College President (president)
    └── Office Heads (head)
        └── Faculty Members (faculty)
```

## Configuration

### Default Settings
```python
# Password Hashing
Algorithm:     Argon2
Default PWD:   "commithubnc"

# Rating Scale
Type:          1-5 numeric scale
Default:       Average = 3.0

# Alert Thresholds
Quantity:      Warning @ 70%, Critical @ 50%
Efficiency:    Warning @ 70%, Critical @ 50%
Timeliness:    Warning @ 70%, Critical @ 50%

# Period Dates (Calendar Year)
Planning:      Jan 1 - Mar 31
Monitoring:    Apr 1 - Sep 30
Rating:        Oct 1 - Dec 31

# Positions (All with 0.0 weights)
Faculty, Office Head, College President, Super Admin

# Categories (With priority ordering)
1. Core Function
2. Strategic
3. Support
```

## Troubleshooting

### Error: "Database already seeded"
**Solution:** Delete all data from database or reset migrations:
```bash
# Option 1: Drop all tables
flask db downgrade base
flask db upgrade head
python seed_database.py

# Option 2: Delete specific tables
mysql> USE commithub_production;
mysql> DELETE FROM profiles;
mysql> DELETE FROM positions;
mysql> DELETE FROM categories;
mysql> DELETE FROM departments;
mysql> DELETE FROM system_settings;
```

### Error: "ModuleNotFoundError: No module named 'app'"
**Solution:** Ensure virtual environment is activated and run from backend directory:
```bash
cd backend/
.venv\Scripts\Activate.ps1      # Windows PowerShell
source .venv/bin/activate        # macOS/Linux bash
python seed_database.py
```

### Error: "No Database Connection"
**Solution:** Verify database credentials in `.env`:
```bash
# Check database URL format
mysql+pymysql://username:password@host:port/database

# Test connection
mysql -u root -p -h localhost --port 3305
```

### Error: "All users have invalid references"
**Solution:** Run migrations before seeding:
```bash
flask db upgrade head
python seed_database.py
```

### Verify-setup shows failures
**Troubleshooting:**

| Failure | Cause | Fix |
|---------|-------|-----|
| Table doesn't exist | Migrations not run | `flask db upgrade head` |
| Count mismatch | Duplicate seed run | Delete data & retry |
| Missing positions | Old schema | Update position names |
| Foreign key errors | Orphaned records | Check data relationships |

## Advanced: Custom Setup

To modify the seed script for custom organization:

1. **Edit `seed_database.py`:**
   - Modify `get_organization_details()` prompts
   - Change default positions in `create_positions()`
   - Add custom categories in `create_categories()`

2. **Example: Add custom department:**
   ```python
   # In create_departments():
   dept = Department(name="IT Department", icon="server", status=1)
   db.session.add(dept)
   ```

3. **Example: Custom rating thresholds:**
   ```python
   # In create_system_settings():
   rating_thresholds = {
       "excellent": {"min": 4.5, "max": 5.0},
       "good": {"min": 3.5, "max": 4.5},
       # ... customize as needed
   }
   ```

## Security Considerations

⚠ **Important:**

1. **Default Password**
   - Change `commithubnc` immediately after first login
   - All users should have unique, strong passwords

2. **System Settings**
   - Update `current_president_fullname` and `current_mayor_fullname` via admin panel
   - Review and customize alert thresholds for your organization

3. **Database**
   - Use strong credentials in `.env`
   - Don't commit `.env` to version control
   - Backup database regularly

4. **Email Configuration**
   - Update MAIL_USERNAME and MAIL_PASSWORD in `app.py`
   - Use app-specific passwords (not personal Gmail passwords)

## What's NOT Included

The seed script creates only **foundation data**. These are created later via normal application workflows:

- ❌ Form Templates
- ❌ Tasks & Form Submissions
- ❌ Performance Reviews (IPCR/OPCR)
- ❌ Supporting Documents
- ❌ Logs (except setup logs)
- ❌ User-generated content

## Database Backup & Recovery

### Backup
```bash
mysqldump -u root -p commithub_production > backup.sql
```

### Restore
```bash
mysql -u root -p commithub_production < backup.sql
```

### Reset to Fresh State
```bash
# Drop and recreate database
mysql> DROP DATABASE commithub_production;
mysql> CREATE DATABASE commithub_production;

# Rerun migrations and seed
flask db upgrade head
python seed_database.py
```

## Performance Notes

**Typical Setup Times:**
- Fresh database creation: < 1 second
- Verification checks: < 2 seconds
- First login after setup: < 3 seconds

**Database Size (After Seeding):**
- Foundation tables: ~50 KB
- With 10 users: ~100 KB
- Production-ready: 10-50 MB (varies with data volume)

## Next Steps After Setup

1. ✓ Login as administrator
2. ✓ Change default password
3. ✓ Review System Settings (period dates, alert thresholds)
4. ✓ Create/assign additional users
5. ✓ Create departments and office heads
6. ✓ Set up task categories
7. ✓ Configure form templates
8. ✓ Start assigning tasks

## Support & Debugging

For issues, check:
1. [DATABASE_DICTIONARY.md](DATABASE_DICTIONARY.md) - Complete schema reference
2. [models/](models/) - Model definitions with relationships
3. [routes/](routes/) - API endpoint documentation
4. Run verification: `python verify_setup.py`

---

**Version:** 1.0  
**Last Updated:** June 2026  
**Maintained By:** CommitHub Team
