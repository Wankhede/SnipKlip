# ✂️ SnipKlip

Owned by Swapnil Wankhede.

**Empowering salons to grow smarter, faster, and digitally.**

SnipKlip is an all-in-one salon management platform built to simplify and automate the everyday operations of salons, spas, and beauty businesses.

Whether you're managing appointments, staff, customers, inventory, payments, or business insights, SnipKlip brings everything together in one powerful platform—so you can spend less time managing operations and more time creating exceptional customer experiences.

## 🚀 Why SnipKlip?

* 📅 Smart Appointment & Booking Management
* 👥 Customer & Staff Management
* 📦 Inventory & Product Tracking
* 💳 Billing & Payment Management
* 📊 Business Analytics & Reports
* 🔔 Automated Notifications & Reminders
* ☁️ Secure, Scalable & Cloud-Ready

Our mission is to transform the beauty and wellness industry through intuitive technology, helping businesses streamline operations, increase revenue, and deliver outstanding customer service.

---

# 🛠️ Project Setup (local)

**One command on Windows, macOS, and Linux** (Cursor, VS Code, or any terminal):

```bash
node run-local.js
```

That is the single entry point. It starts **backend + frontend**, installs packages, reclaiming ports **8082 / 8083**, and opens URLs as **http://localhost:...** (not `127.0.0.1`).

| How | What to run |
|-----|-------------|
| **Cursor / VS Code** | `Terminal` → `Run Task…` → **SnipKlip: Start** (also default build: **Cmd/Ctrl+Shift+B**) |
| **Any terminal** | `node run-local.js` |
| Stop / status / restart | `node run-local.js stop` · `status` · `restart` |

Full clone layout, prerequisites, and troubleshooting: **[SETUP_GUIDE.md](./SETUP_GUIDE.md)**.

> Under the hood, `run-local.js` calls `run-local.bat` (Windows) or `run-local.sh` (macOS/Linux). You only need the Node command (or the IDE task).

Reserved ports: **Backend :8082** · **Frontend :8083**

Legacy Ubuntu server notes remain below for production-style hosts.

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=app.settings.local
python manage.py runserver 127.0.0.1:8082 --settings=app.settings.local
```

---

# 📚 Resources

Getting started with Django? These resources will help you hit the ground running.

* 📖 **Django Official Documentation** – https://docs.djangoproject.com/
* 🚀 **Django for Beginners** – https://djangoforbeginners.com/
* 🌐 **Deploying Django with PostgreSQL, Gunicorn & Nginx** – https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04

Happy coding! 🎉
