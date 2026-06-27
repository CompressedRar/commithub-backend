## 📋 Database Setup Scripts

This directory contains utilities for setting up and verifying the CommitHub backend database.

### Scripts

#### `seed_database.py` - Initialize Database
Primary script for first-time database setup with foundation data.

**Usage:**
```bash
python seed_database.py
```

**Capabilities:**
- Interactive organization setup (name, president, admin)
- Automatic table creation
- Creates 6 foundation entities (System Settings, Positions, Categories, Department, Profile, User)
- Argon2 password hashing
- Full data validation
- Auto-rollback on errors
- Colored terminal output with progress

**What It Does:**
1. Checks for existing data (prevents duplicates)
2. Gets organization details interactively
3. Creates all database tables
4. Seeds System Settings with default config
5. Creates 4 default positions
6. Creates 3 task categories
7. Creates root department
8. Creates admin profile and user account
9. Verifies all data integrity

**Output:**
```
=======================================
      CommitHub Database Seeding       
=======================================

ℹ Database: mysql+pymysql://root:password@localhost:3305/commithub_production

[0] Checking for existing data...
✓ Database is clean. Proceeding with seeding.

[Organization Setup]
Organization name: [College]
College President: [Dr. Juan dela Cruz]
Admin officer: [Maria Santos]
Admin email: [admin@commithub.local]

[1] Creating System Settings...
✓ System Settings created (ID: 1)

[2] Creating Positions...
✓ Created 4 positions

[3] Creating Categories...
✓ Created 3 categories

[4] Creating Departments...
✓ Created root department: 'College' (ID: 1)

[5] Creating Admin Profile and User Account...
✓ Created Profile: admin@commithub.local
✓ Created User: Maria Santos (Administrator)
✓ Default password: 'commithubnc'
⚠ Change this password immediately after first login!

[6] Verifying Setup...
✓ System Settings: 1 ✓
✓ Positions: 4 ✓
✓ Categories: 3 ✓
✓ Departments: 1 ✓
✓ Profiles: 1 ✓
✓ Users: 1 ✓

=======================================
           Setup Complete!             
=======================================

Your CommitHub backend is ready to use!
```

---

#### `verify_setup.py` - Comprehensive Verification
Post-setup verification to ensure database integrity.

**Usage:**
```bash
python verify_setup.py
```

**Capabilities:**
- Table existence checks
- Data count validation
- Foundation data verification
- Foreign key relationship checks
- Unique constraint validation
- Admin account verification
- System readiness assessment
- Detailed pass/fail reporting

**Checks:**
1. All required tables exist
2. Expected record counts (System Settings=1, Positions=4, etc.)
3. Specific foundation data (positions, categories)
4. Foreign key integrity (no orphaned records)
5. Unique constraints (no duplicate emails, department names)
6. Admin account exists and is accessible
7. Overall system readiness

**Output Example:**
```
============================================================
              CommitHub Database Verification              
============================================================

1. TABLE EXISTENCE CHECKS
────────────────────────────────────────────────────────
  [✓ PASS] Table 'profiles' exists
           3 records
  [✓ PASS] Table 'users' exists
           1 records
  [✓ PASS] Table 'positions' exists
           4 records
  ... (more tables)

2. DATA COUNT CHECKS
────────────────────────────────────────────────────────
  [✓ PASS] System Settings (should be 1)
           Found: 1, Expected: exactly 1
  [✓ PASS] Positions (should be 4)
           Found: 4, Expected: at least 4
  ... (more checks)

3. FOUNDATION DATA CHECKS
────────────────────────────────────────────────────────
  Positions:
  [✓ PASS]   Position 'Faculty'
  [✓ PASS]   Position 'Office Head'
  [✓ PASS]   Position 'College President'
  [✓ PASS]   Position 'Super Admin'

  ... (more foundation data)

4. FOREIGN KEY RELATIONSHIP CHECKS
────────────────────────────────────────────────────────
  [✓ PASS] All users have valid profile references
           Orphaned users: 0
  ... (more relationship checks)

5. UNIQUE CONSTRAINT CHECKS
────────────────────────────────────────────────────────
  [✓ PASS] Profile emails are unique
           Duplicate emails: 0
  ... (more unique checks)

6. ADMIN ACCOUNT CHECKS
────────────────────────────────────────────────────────
  [✓ PASS] Administrator user exists

  Admin Details:
    Name: Maria Santos
    Email: admin@commithub.local
    Role: administrator
    Department: College

  [✓ PASS] Admin has valid profile
  [✓ PASS] Default password is correctly hashed

7. SYSTEM STATUS SUMMARY
────────────────────────────────────────────────────────

  Total Records:
    Users: 1
    Departments: 1
    Positions: 4
    Categories: 3

  [✓ PASS] System is ready for production
           All foundation data is in place

============================================================
                  Verification Complete                    
============================================================

✓ ALL CHECKS PASSED
The database setup is valid and ready to use!
```

---

#### `cli.py` - Flask CLI Commands
Integration module for Flask CLI commands.

**Automatically registers these commands:**

```bash
flask seed-db      # Run setup interactively (same as seed_database.py)
flask verify-db    # Quick verification (like verify_setup.py)
```

**Installation:**
Automatically loaded via `app.py` - no manual setup needed!

**Example:**
```bash
$ flask seed-db
# Interactive setup prompts...

$ flask verify-db
# Quick verification output...
```

---

### Required Dependencies

```
Flask>=2.0.0
Flask-SQLAlchemy>=3.0.0
Flask-Migrate>=3.0.0
argon2-cffi>=21.0.0
click>=8.0.0  (automatically included with Flask)
python-dotenv>=0.19.0
```

Install via:
```bash
pip install -r requirements.txt
```

---

### Setup Workflow

```
Step 1: Prepare Database
  └─ Create database schema
  └─ Run migrations (flask db upgrade head)

Step 2: Seed Foundation Data
  └─ python seed_database.py
  └─ OR: flask seed-db
  └─ Provide organization details
  └─ System creates all foundation entities

Step 3: Verify Setup
  └─ python verify_setup.py
  └─ OR: flask verify-db
  └─ Confirms all data integrity

Step 4: Start Application
  └─ python app.py
  └─ Login with admin credentials
  └─ Change default password ⚠️
  └─ Configure system settings
```

---

### Common Errors & Solutions

#### Error: "Database already seeded"
**Cause:** Foundation data already exists  
**Solution:**
```bash
# Option 1: Fresh database
DROP DATABASE commithub_production;
CREATE DATABASE commithub_production;
flask db upgrade head
python seed_database.py

# Option 2: Delete existing data
DELETE FROM profiles;
DELETE FROM users;
DELETE FROM system_settings;
DELETE FROM positions;
DELETE FROM categories;
DELETE FROM departments;
python seed_database.py
```

#### Error: "ModuleNotFoundError: No module named 'app'"
**Cause:** Virtual environment not activated or wrong directory  
**Solution:**
```bash
# Navigate to backend directory
cd backend/

# Activate virtual environment
.venv\Scripts\Activate.ps1      # Windows
source .venv/bin/activate        # macOS/Linux

# Run script
python seed_database.py
```

#### Error: "No database connection"
**Cause:** Invalid connection string in `.env`  
**Solution:**
```bash
# Check .env file contains:
LOCAL_DATABASE_URL=mysql+pymysql://root:password@host:port/database

# Verify MySQL is running:
mysql -u root -p

# Test connection:
python -c "from app import create_app; app = create_app(); print('✓ Connected')"
```

#### Error: "Tables don't exist"
**Cause:** Migrations not applied  
**Solution:**
```bash
# Run migrations first
flask db upgrade head

# Then seed
python seed_database.py
```

---

### Security Notes

⚠️ **Important:**

1. **Default Password**
   - Default: `commithubnc`
   - Hashed using Argon2 (industry standard)
   - **CHANGE IMMEDIATELY** after first login

2. **Database Credentials**
   - Never commit `.env` to version control
   - Use strong passwords for database user
   - Restrict database access to backend server

3. **Admin Account**
   - Only administrator should have this account
   - Use separate user accounts for daily work
   - Regularly audit admin activity via Logs

---

### Files Modified

- `app.py` — Added `from cli import init_cli; init_cli(app)` before return
- `.env` — Ensure `LOCAL_DATABASE_URL` is set

---

### Full Documentation

For detailed information, see:
- [SETUP_GUIDE.md](SETUP_GUIDE.md) — Complete setup documentation
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) — Quick command reference
- [DATABASE_DICTIONARY.md](DATABASE_DICTIONARY.md) — Database schema

---

### Troubleshooting Scripts

```bash
# Full verification with detailed checks
python verify_setup.py

# Quick CLI verification
flask verify-db

# Check Flask can import all models
python -c "from models import *; print('✓ All models imported')"

# List all users
python -c "from app import create_app, db; from models.User import User; \
           app = create_app(); ctx = app.app_context(); ctx.push(); \
           users = User.query.all(); print(f'Users: {len(users)}'); \
           [print(f'  {u.full_name()} ({u.role})') for u in users]"
```

---

### Support

**Questions or Issues?**

1. Check `verify_setup.py` output for specific failures
2. Review [SETUP_GUIDE.md](SETUP_GUIDE.md) troubleshooting section
3. Check database logs: `SELECT * FROM logs ORDER BY created_at DESC LIMIT 10;`
4. Verify database connection: `mysql -u root -p -h localhost --port 3305 commithub_production`

---

**Version:** 1.0  
**Last Updated:** June 2026  
**CommitHub Backend Team**
