# CommitHub Setup - Quick Reference

## 🚀 Quick Start (3 Steps)

### 1. Fresh Database? Run Seed Script
```bash
# Option A: Interactive standalone script
python seed_database.py

# Option B: Flask CLI (same interactive prompts)
flask seed-db
```

### 2. Verify Everything Works
```bash
# Comprehensive checks
python verify_setup.py

# Quick CLI check
flask verify-db
```

### 3. Start Server & Login
```bash
python app.py
# Visit: http://localhost:5000
# Login with: admin@commithub.local / commithubnc
```

---

## 📋 What Gets Created

| Item | Count | Purpose |
|------|-------|---------|
| System Settings | 1 | Global config, rating scales, alert thresholds |
| Positions | 4 | Faculty, Office Head, College President, Super Admin |
| Categories | 3 | Core Function, Strategic, Support |
| Department | 1+ | Root organization department |
| Profile | 1+ | Admin login credentials (hashed password) |
| User | 1+ | Admin account (administrator role) |

---

## 🛠️ Common Commands

| Task | Command |
|------|---------|
| **Fresh Setup** | `python seed_database.py` |
| **Verify Database** | `python verify_setup.py` |
| **Quick CLI Verify** | `flask verify-db` |
| **Flask CLI Setup** | `flask seed-db` |
| **Start Server** | `python app.py` or `flask run` |
| **Run Migrations** | `flask db upgrade head` |
| **Reset Database** | `flask db downgrade base` then `flask db upgrade head` |

---

## 🔑 Default Credentials After Setup

```
Email:    admin@commithub.local
Password: commithubnc

⚠️ CHANGE THIS PASSWORD IMMEDIATELY!
```

---

## 📊 Database Structure (Simplified)

```
System_Settings (singleton)
├── Rating scales (1-5)
├── Alert thresholds
└── Period dates

Positions (4)
└── Faculty, Head, President, Admin

Categories (3)
└── Core, Strategic, Support

Department (1)
└── Root organization

Profile (1)
└── Admin email + hashed password

User (1)
└── Admin (administrator role)
```

---

## ✅ Verification Checklist

After running setup, verify these pass:

- [ ] `System_Settings` count = 1
- [ ] `Position` count >= 4
- [ ] `Category` count >= 3
- [ ] `Department` count >= 1
- [ ] `Profile` count >= 1
- [ ] `User` count >= 1
- [ ] No orphaned foreign keys
- [ ] Admin user exists
- [ ] Default password hashed with Argon2

Run `python verify_setup.py` to auto-check all ✓

---

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| "Database already seeded" | Delete data: `DELETE FROM profiles;` then retry |
| "ModuleNotFoundError" | Activate venv: `.venv\Scripts\Activate.ps1` |
| "No database connection" | Check `.env` has valid `LOCAL_DATABASE_URL` |
| "Tables don't exist" | Run: `flask db upgrade head` |
| Foreign key errors | Run migrations BEFORE seeding |

---

## 🔄 Data Flow: First-Time Setup

```
┌─────────────────────────────────────┐
│ 1. Run seed_database.py             │
│    ↓ Gets org details interactively │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ 2. Creates Foundation Data          │
│    • System_Settings                │
│    • Positions                      │
│    • Categories                     │
│    • Department                     │
│    • Admin Profile & User           │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ 3. Verifies All Data                │
│    • Counts                         │
│    • Relationships                  │
│    • Constraints                    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ 4. System Ready! ✓                  │
│    • Login with admin credentials   │
│    • Configure settings             │
│    • Create users/departments       │
└─────────────────────────────────────┘
```

---

## 📁 Files Created/Modified

### Created:
- ✨ `seed_database.py` - Main setup script
- ✨ `verify_setup.py` - Verification script
- ✨ `cli.py` - Flask CLI commands
- 📖 `SETUP_GUIDE.md` - Full documentation
- 📋 `QUICK_REFERENCE.md` - This file

### Modified:
- 🔧 `app.py` - Added Flask CLI integration

---

## 🎯 Next Steps After Setup

1. **Login** as admin@commithub.local
2. **Change password** immediately (⚠ Security!)
3. **Configure System Settings**:
   - Update president/mayor names
   - Review period dates
   - Set alert thresholds
4. **Create additional users**
5. **Set up departments** (if not done)
6. **Assign office heads** to departments
7. **Create form templates** for tasks
8. **Assign tasks** to users

---

## 🔗 Related Files

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup documentation
- [DATABASE_DICTIONARY.md](DATABASE_DICTIONARY.md) - Complete schema
- [models/](models/) - All model definitions
- [routes/Auth.py](routes/Auth.py) - Authentication & password hashing

---

## 🤝 Support

For detailed information, see:
- **Full Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Database Schema**: [DATABASE_DICTIONARY.md](DATABASE_DICTIONARY.md)
- **Troubleshooting**: See SETUP_GUIDE.md → Troubleshooting section

---

**Version:** 1.0 | Last Updated: June 2026 | CommitHub Team
