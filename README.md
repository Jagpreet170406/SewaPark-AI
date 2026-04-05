# ☬ SewaPark-AI
### AI-assisted Gurdwara Carpark Management System
**Sikh Sewaks Singapore · Nishkam Seva meets Engineering**

🧡💙 *Because seva doesn't end at the Gurdwara gates — it lives in every corner of the community it serves.*

---

## What is SewaPark-AI?

SewaPark-AI is a mobile-first carpark command system built for Gurdwara events. It was born out of real operational challenges faced during **Khalsa Week 2026** as Carpark IC for Sikh Sewaks Singapore — manpower shortages, stack parking violations, Ragi Jatha lot conflicts, and the eternal unmovable uncle at the drop-off zone. 😤

Rather than just writing an After Action Review, I built a system to fix it.

---

## Features

| Feature | Description |
|---|---|
| 🗺️ **Live Lot Map** | Real-time carpark occupancy across LHS, Center, RHS, Reserved, Slope, Bus Bay zones |
| 🚧 **Gate Control** | Manual open/close + auto-close at 95% capacity |
| ☬ **Ragi Arrival Mode** | One-tap alert that restricts drop-off zone, blasts all ICs, and starts a countdown |
| 📋 **Reserved Lot Booking** | Book lots for Ragi Jatha, Sewadars, Jathedars with QR + elderly button fallback |
| ◈ **Waitlist Queue** | Manage overflow Sangat, admit when lots free up |
| ⚠️ **Incident Logger** | Real-time logging by IC on the ground |
| 📊 **Auto AAR** | After Action Review auto-generated from incident logs, grouped by type and severity |
| 👥 **IC Roster + DND** | Manage on-duty ICs and notification preferences |
| 🏛️ **Multi-Gurdwara** | Supports Central Sikh Temple, Silat Road, and Dharmak Sabha Gurdwara |

---

## Tech Stack

- **Backend** — Python, Flask
- **Database** — SQLite
- **Frontend** — Jinja2, HTML/CSS/JS (mobile-first)
- **Design** — Dark tactical UI, optimised for sunlight readability on mobile

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/sewapark-ai.git
cd sewapark-ai
```

### 2. Install dependencies
```bash
# Windows
pip install -r requirements.txt

# Linux / Mac
pip install -r requirements.txt --break-system-packages
```

### 3. Initialise the database
```bash
python db_init.py       # Windows
python3 db_init.py      # Linux / Mac
```

This seeds all 3 Gurdwaras with their lot configurations and IC rosters.

### 4. Run the app
```bash
python app.py       # Windows
python3 app.py      # Linux / Mac
```

Open on your phone: `http://YOUR_LAPTOP_IP:5000`

> **Tip:** Run `ipconfig` (Windows) or `ip a` (Linux) to find your local IP. Make sure your phone and laptop are on the same WiFi.

---

## Project Structure

```
sewapark-ai/
├── app.py              # Flask routes + logic
├── db_init.py          # DB schema + seed data
├── requirements.txt
├── .gitignore
├── README.md
└── templates/
    ├── base.html       # Mobile-first base layout + nav
    ├── index.html      # Gurdwara selector
    ├── dashboard.html  # Live carpark command view
    ├── bookings.html   # Reserved lot management
    ├── waitlist.html   # Queue management
    ├── incidents.html  # Incident logger
    └── aar.html        # Auto After Action Review
```

---

## Supported Gurdwaras

| Gurdwara | Code | Lots |
|---|---|---|
| Central Sikh Temple | CST | 32 |
| Silat Road Gurdwara | SRG | 10 |
| Dharmak Sabha Gurdwara | DSG | 19 |

---

## Roadmap

- [ ] OpenCV + single gate camera for auto plate detection on entry/exit
- [ ] Push notifications bypass DND for critical IC alerts
- [ ] PWA support — install on homescreen like a native app
- [ ] Auto-export AAR to `.docx`
- [ ] Smart lighting reminder — alert IC before 10pm lights-off during events
- [ ] Darbar display integration — flash vehicle plate on Gurdwara screen

---

## Why This Exists

This project is **nishkam seva** — selfless service. Built voluntarily, not for marks or money, but because the Gurdwara community deserves tools as good as any corporate operation.

Every feature in this app came from a real problem faced on the ground. The Ragi Arrival Mode exists because a Ragi Jatha van once couldn't get through. The incident logger exists because the AAR was being written from memory at 1am. The elderly assist button exists because not everyone can scan a QR code.

**Waheguru Ji Ka Khalsa, Waheguru Ji Ki Fateh** ☬

---

*Built by Jagpreet Singh · Sikh Sewaks Singapore · Cybersecurity & Digital Forensics, Nanyang Polytechnic*
