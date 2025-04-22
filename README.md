# 🖥️ Site Monitor

A simple Python GUI application for real-time monitoring of website availability. Visual indicators, logging, and multiple notification methods help ensure you're always informed about the status of your web services.

---

## 🚀 Features

- ⏱️ Periodic website status checks (custom interval)
- 🟢🟡🔴 Visual status indicators:
  - Green – working
  - Yellow – no response (timeout)
  - Red – not reachable
- 📊 CSV log of all checks with timestamps
- 📬 Email alerts (SMTP configurable)
- 💬 Slack notifications (via webhook URL)
- 🔔 Optional push notifications (Telegram, Pushover, or SMS via Twilio)
- 🖼️ Always-on-top GUI window
- 🛠️ GUI-based configuration (no config files editing needed)
- 💾 Settings persist between runs
- 👤 About menu with contact info

---

## 🛠 Installation

### Requirements
- Python 3.8+
- Required packages:
  ```bash
  pip install requests
### Run
python site_monitor.py

### 🧪 Build .exe (Windows)
To generate a standalone .exe file:

  Install PyInstaller:
    pip install pyinstaller

  pyinstaller --onefile --windowed site_monitor.py
  Output will be available in the dist/ folder.

### ⚙ Configuration
All settings are editable in the app GUI:
- Websites to monitor
- Interval between checks
- Email alert configuration
- Slack webhook URL
- Notification frequency & danger-only option
Saved in settings.json after changes.

