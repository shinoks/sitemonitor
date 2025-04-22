import tkinter as tk
from tkinter import messagebox, ttk
import requests
from threading import Thread
import time
import csv
import smtplib
from email.mime.text import MIMEText
import json
import os
from datetime import datetime

SETTINGS_FILE = 'settings.json'
# Domyślne ustawienia
DEFAULT_SETTINGS = {
    'sites': ['https://koriko.pl'],
    'check_interval': 20,
    'request_timeout': 30,
    'csv_log_file': 'site_availability.csv',
    'email_notifications': {
        'enabled': False,
        'interval': 3600,
        'only_on_danger': True,
        'smtp_server': '',
        'smtp_port': 587,
        'smtp_user': '',
        'smtp_pass': '',
        'from_addr': '',
        'to_addrs': []
    },
    'slack_notifications': {
        'enabled': False,
        'webhook_url': ''
    }
}

# Wczytywanie i zapisywanie ustawień
def load_settings(path=SETTINGS_FILE):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings, path=SETTINGS_FILE):
    with open(path, 'w') as f:
        json.dump(settings, f, indent=2)

settings = load_settings()
last_email_time = datetime.min

# Inicjalizacja pliku CSV
def init_csv(path):
    try:
        with open(path, 'x', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'site', 'status', 'elapsed_ms', 'detail'])
    except FileExistsError:
        pass

init_csv(settings['csv_log_file'])

class SiteMonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("Site Monitor")
        master.attributes('-topmost', True)

        menu = tk.Menu(master)
        master.config(menu=menu)
        help_menu = tk.Menu(menu, tearoff=0)
        help_menu.add_command(label="Kontakt", command=self.show_contact)
        menu.add_cascade(label="Pomoc", menu=help_menu)

        btn_frame = tk.Frame(master)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Settings", command=self.open_settings).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Exit", command=master.quit).pack(side='right', padx=5)

        self.frame = tk.Frame(master)
        self.frame.pack(padx=10, pady=10)
        self.indicators = {}
        self.build_indicators()

        Thread(target=self.monitor_loop, daemon=True).start()

    def show_contact(self):
        messagebox.showinfo("Kontakt", "Koriko\nPaweł Suchodolski\ntel:784002624\nemail:biuro@koriko.pl")

    def build_indicators(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.indicators.clear()
        for idx, site in enumerate(settings['sites']):
            row = tk.Frame(self.frame)
            row.grid(row=idx, column=0, sticky="w", pady=2)
            tk.Label(row, text=site, width=40, anchor="w").pack(side="left")
            canvas = tk.Canvas(row, width=20, height=20)
            canvas.pack(side="left", padx=(5,0))
            circle = canvas.create_oval(2,2,18,18, fill="gray")
            self.indicators[site] = (canvas, circle)

    def open_settings(self):
        win = tk.Toplevel(self.master)
        win.title("Settings")
        win.attributes('-topmost', True)

        tk.Label(win, text="Sites (po jednym URL na linijkę):").grid(row=0, column=0, sticky='w')
        txt_sites = tk.Text(win, width=50, height=5)
        txt_sites.grid(row=1, column=0, padx=5, pady=5)
        txt_sites.insert('1.0', "\n".join(settings['sites']))

        tk.Label(win, text="Check interval (s):").grid(row=2, column=0, sticky='w')
        ent_interval = tk.Entry(win)
        ent_interval.grid(row=3, column=0, sticky='w', padx=5)
        ent_interval.insert(0, str(settings['check_interval']))

        tk.Label(win, text="Request timeout (s):").grid(row=4, column=0, sticky='w')
        ent_timeout = tk.Entry(win)
        ent_timeout.grid(row=5, column=0, sticky='w', padx=5)
        ent_timeout.insert(0, str(settings['request_timeout']))

        tk.Label(win, text="CSV log file path:").grid(row=6, column=0, sticky='w')
        ent_csv = tk.Entry(win, width=50)
        ent_csv.grid(row=7, column=0, padx=5)
        ent_csv.insert(0, settings['csv_log_file'])

        email_frame = ttk.Labelframe(win, text="Email Notifications")
        email_frame.grid(row=8, column=0, padx=5, pady=5, sticky='w')
        var_enabled = tk.BooleanVar(value=settings['email_notifications']['enabled'])
        tk.Checkbutton(email_frame, text="Enabled", var=var_enabled).grid(row=0, column=0, sticky='w')
        tk.Label(email_frame, text="Interval (s):").grid(row=1, column=0, sticky='w')
        ent_email_int = tk.Entry(email_frame)
        ent_email_int.grid(row=2, column=0, padx=5, sticky='w')
        ent_email_int.insert(0, str(settings['email_notifications']['interval']))
        var_only = tk.BooleanVar(value=settings['email_notifications']['only_on_danger'])
        tk.Checkbutton(email_frame, text="Only on danger", var=var_only).grid(row=3, column=0, sticky='w')

        labels = ['SMTP server', 'Port', 'User', 'Pass', 'From', 'To (comma-separated)']
        keys = ['smtp_server', 'smtp_port', 'smtp_user', 'smtp_pass', 'from_addr', 'to_addrs']
        entries = {}
        for i, (lbl, key) in enumerate(zip(labels, keys), start=4):
            tk.Label(email_frame, text=lbl+":").grid(row=i, column=0, sticky='w')
            ent = tk.Entry(email_frame, width=50)
            ent.grid(row=i+1, column=0, padx=5, pady=2)
            val = settings['email_notifications'].get(key, '')
            ent.insert(0, ",".join(val) if key=='to_addrs' else str(val))
            entries[key] = ent

        slack_frame = ttk.Labelframe(win, text="Slack Notifications")
        slack_frame.grid(row=14, column=0, padx=5, pady=5, sticky='w')
        var_slack = tk.BooleanVar(value=settings['slack_notifications']['enabled'])
        tk.Checkbutton(slack_frame, text="Enabled", var=var_slack).grid(row=0, column=0, sticky='w')
        tk.Label(slack_frame, text="Webhook URL:").grid(row=1, column=0, sticky='w')
        ent_slack_url = tk.Entry(slack_frame, width=50)
        ent_slack_url.grid(row=2, column=0, padx=5)
        ent_slack_url.insert(0, settings['slack_notifications']['webhook_url'])

        def save():
            settings['sites'] = [s.strip() for s in txt_sites.get('1.0', 'end').splitlines() if s.strip()]
            settings['check_interval'] = int(ent_interval.get())
            settings['request_timeout'] = int(ent_timeout.get())
            settings['csv_log_file'] = ent_csv.get()
            settings['email_notifications']['enabled'] = var_enabled.get()
            settings['email_notifications']['interval'] = int(ent_email_int.get())
            settings['email_notifications']['only_on_danger'] = var_only.get()
            for key, ent in entries.items():
                val = ent.get().strip()
                settings['email_notifications'][key] = [addr.strip() for addr in val.split(',')] if key=='to_addrs' else (int(val) if key=='smtp_port' else val)
            settings['slack_notifications']['enabled'] = var_slack.get()
            settings['slack_notifications']['webhook_url'] = ent_slack_url.get().strip()
            save_settings(settings)
            init_csv(settings['csv_log_file'])
            self.build_indicators()
            win.destroy()

        tk.Button(win, text='Save', command=save).grid(row=20, column=0, pady=10)

    def update_indicator(self, site, color):
        canvas, circle = self.indicators[site]
        canvas.itemconfig(circle, fill=color)

    def notify(self, site, detail):
        messagebox.showwarning("Site Monitor", f"{site}: {detail}")

    def send_email(self, subject, body):
        global last_email_time
        cfg = settings['email_notifications']
        now = datetime.now()
        if not cfg['enabled'] or (now - last_email_time).total_seconds() < cfg['interval']:
            return
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = cfg['from_addr']
        msg['To'] = ", ".join(cfg['to_addrs'])
        try:
            with smtplib.SMTP(cfg['smtp_server'], cfg['smtp_port']) as server:
                server.starttls()
                server.login(cfg['smtp_user'], cfg['smtp_pass'])
                server.sendmail(cfg['from_addr'], cfg['to_addrs'], msg.as_string())
            last_email_time = now
        except Exception as e:
            print(f"Email send failed: {e}")

    def send_slack(self, message):
        cfg = settings['slack_notifications']
        if not cfg['enabled'] or not cfg['webhook_url']:
            return
        try:
            requests.post(cfg['webhook_url'], json={"text": message}, timeout=5)
        except Exception as e:
            print(f"Slack send failed: {e}")

    def log_csv(self, timestamp, site, status, elapsed, detail):
        with open(settings['csv_log_file'], 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, site, status, elapsed, detail])

    def check_site(self, site):
        start = time.time()
        try:
            resp = requests.get(site, timeout=settings['request_timeout'])
            elapsed_ms = int((time.time() - start)*1000)
            return ('green', elapsed_ms, 'OK') if resp.status_code==200 else ('red', elapsed_ms, f'HTTP {resp.status_code}')
        except requests.exceptions.Timeout:
            return ('yellow', settings['request_timeout']*1000, 'TIMEOUT')
        except requests.exceptions.RequestException as e:
            elapsed_ms = int((time.time() - start)*1000)
            return ('red', elapsed_ms, str(e))

    def monitor_loop(self):
        global last_email_time
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            danger = []
            for site in settings['sites']:
                color, elapsed, detail = self.check_site(site)
                self.master.after(0, self.update_indicator, site, color)
                self.log_csv(timestamp, site, color, elapsed, detail)
                if color in ('red','yellow'):
                    danger.append((site, detail))
                    if not settings['email_notifications']['only_on_danger']:
                        self.master.after(0, lambda s=site, d=detail: self.notify(s, d))
            if danger:
                msg = 'Problemy z:\n' + '\n'.join(f"{s}: {d}" for s,d in danger)
                self.send_email('Site Monitor Alert', msg)
                self.send_slack(msg)
                if settings['email_notifications']['only_on_danger']:
                    for s,d in danger:
                        self.master.after(0, lambda s=s,d=d: self.notify(s, d))
            time.sleep(settings['check_interval'])

if __name__ == '__main__':
    root = tk.Tk()
    app = SiteMonitorApp(root)
    root.mainloop()
