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

**Windows / macOS / Linux single-click:** see **[SETUP_GUIDE.md](./SETUP_GUIDE.md)**.

Reserved ports: **Backend :8082** · **Frontend :8083**

```bash
# Clone backend + frontend as siblings, then:
./run-local.sh          # macOS / Linux
# or
.\run-local.bat         # Windows
```

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
