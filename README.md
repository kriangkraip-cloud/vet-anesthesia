# 🏥 VetAnesthesia Records

A modern web-based anesthetic monitoring and record management system for veterinary clinics.

**Features:**
- 📋 Patient signalment & case information
- 💊 Drug administration tracking (premedication, induction, local anesthesia)
- 📊 Intraoperative monitoring with dual-axis charts
- 🩸 IV fluid therapy tracking
- 🚨 Emergency drug/event logging
- 📄 Export to PDF/DOCX with monitoring graphs
- 👥 Multi-user support with role-based access
- 💾 Database backup & restore

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
docker compose up -d
# Open http://localhost:8100
```

### Option 2: Manual Install
```bash
pip3 install -r requirements.txt
bash start.sh
# Open http://localhost:8100
```

---

## 📖 Installation & Deployment

See **[INSTALL.md](INSTALL.md)** for:
- Full Docker installation
- Manual installation
- First admin setup
- Backup/restore
- Deploying online (Railway, Render, Oracle Cloud)

---

## 🔑 Default Login

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin1234` |

⚠️ **Change password immediately after first login!**

---

## 📊 Key Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/records` | List anesthetic records |
| `GET /api/patients` | List patients |
| `POST /api/records/{id}/drugs` | Add drug entry |
| `POST /api/records/{id}/monitoring` | Add monitoring entry |
| `GET /api/export/{id}/pdf` | Export record as PDF |
| `GET /api/backup/download` | Download database backup |
| `POST /api/backup/restore` | Restore from backup |

---

## 🛠 Tech Stack

- **Backend:** FastAPI (Python 3.9+)
- **Database:** SQLite
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Charts:** Chart.js (browser), Matplotlib (exports)
- **Export:** ReportLab (PDF), python-docx (DOCX)

---

## 📦 Database

All data (patients, records, drugs, monitoring, users) is stored in a single SQLite database file (`anesthesia.db`).

**Backup:** Use the web UI or `bash scripts/backup.sh`

**Restore:** Use the web UI or `bash scripts/restore.sh /path/to/backup.db`

---

## 🌐 Deploying Online

### Railway.app (Free, Easy)
```bash
git push origin main
# Railway auto-deploys from GitHub
```

### Render.com (Free)
Connect GitHub → Select repo → Deploy

### Oracle Cloud Always Free
Free tier: 2 CPU, 1 GB RAM, 100 GB storage (never expires)

See [INSTALL.md](INSTALL.md) for detailed steps.

---

## 🔒 Security Notes

- Login required for all data access
- Passwords hashed with bcrypt
- JWT tokens for session management
- Database stored locally (not exposed)
- Deploy with HTTPS in production

---

## 📝 License

Proprietary - For veterinary use only

---

## 📧 Support

For issues or questions, refer to [INSTALL.md](INSTALL.md) Troubleshooting section.
