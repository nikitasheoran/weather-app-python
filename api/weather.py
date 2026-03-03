
#Name: Nikita
#Student Number: c0958762
# Weather Forecasting

import json
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import requests
from io import BytesIO

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

CONFIG_PATH = "config.json"
DEG = "\N{DEGREE SIGN}"

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.resizable(False, False)
        self.configure(bg="#a33efb")
        self.load_config()

        
        self.title(self.config_data.get("window_title", "Weather App"))
        pos = self.config_data.get("position", {})
        if pos:
            x = pos.get("x", 100)
            y = pos.get("y", 100)
            self.geometry(f"+{x}+{y}")

        # Top bar: date and time
        top = tk.Frame(self, bg="#ef2a2a")
        top.pack(fill="x")
        self.date_lbl = tk.Label(top, text="", font=("Forte", 20), bg="#ef2a2a", fg="#efdf2a")
        self.time_lbl = tk.Label(top, text="", font=("Forte", 20), bg="#ef2a2a", fg="#efdf2a")
        self.date_lbl.pack(side="left", padx=20, pady=10)
        self.time_lbl.pack(side="right", padx=20, pady=10)

        # Main area
        body = tk.Frame(self, bg="#a33efb", bd=2, relief="flat")
        body.pack(padx=20, pady=10)

        # City name
        self.city_lbl = tk.Label(body, text="", font=("Algerian", 28), bg="#a33efb", fg="#e8f139")
        self.city_lbl.grid(row=0, column=0, sticky="w", padx=(20, 50), pady=(10, 0), columnspan=2)

        # details
        self.details = {}
        detail_names = [
            ("Feels like", "feels_like", "°C"),
            ("Humidity", "humidity", "%"),
            ("Clouds", "clouds", "%"),
            ("Pressure", "pressure", " hPa"),
            ("Visibility", "visibility_km", " km"),
            ("Wind Speed", "wind_speed", " m/s"),
        ]
        r = 1
        for label, key, unit in detail_names:
            tk.Label(body, text=f"{label}:", font=("Calibri", 15, "bold"), bg="#a33efb", fg="#e8f139").grid(row=r, column=2, sticky="e", padx=10, pady=3)
            val = tk.Label(body, text="-", font=("Calibri", 15, "bold"), bg="#a33efb", fg="#e8f139")
            val.grid(row=r, column=3, sticky="w", padx=(0, 20), pady=3)
            self.details[key] = (val, unit)
            r += 1

        # temperature and icon
        self.icon_lbl = tk.Label(body, bg="#a33efb")
        self.icon_lbl.grid(row=1, column=0, rowspan=3, padx=(20, 10), pady=(10, 10), sticky="w")

        self.temp_c_lbl = tk.Label(body, text="--°C", font=("Forte", 36), bg="#a33efb", fg="#e8f139")
        self.temp_f_lbl = tk.Label(body, text="--°F", font=("Forte", 22), bg="#a33efb", fg="#e8f139")
        self.temp_c_lbl.grid(row=1, column=1, sticky="w", pady=(10, 0))
        self.temp_f_lbl.grid(row=2, column=1, sticky="w")

        # countdown
        bottom = tk.Frame(self, bg="#ef2a2a")
        bottom.pack(fill="x")
        self.countdown_lbl = tk.Label(bottom, text="", font=("Forte", 18), fg="#e8f139", bg="#ef2a2a")
        self.countdown_lbl.pack(pady=8)

        # Internal timers
        self._countdown = 0
        self.icon_img = None  
        self.after(0, self.update_clock)
        self.after(0, self.fetch_weather)

    # ---------- Config ----------
    def load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
        except FileNotFoundError:
            # default config template on first run
            self.config_data = {
                "city": "Sarnia",
                "api_key": "PUT_YOUR_OPENWEATHER_API_KEY_HERE",
                "interval_minutes": 1,
                "units": "metric",
                "window_title": "Nikita Sheoran — CNum 2268861317 — Weather",
                "position": {"x": 100, "y": 100}
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2)
        # Safety
        self.config_data.setdefault("interval_minutes", 5)
        self.config_data.setdefault("units", "metric")

    # *-*-*-*-*-* UI updaters *-*-*-*-*-*
    def update_clock(self):
        now = datetime.now()
        self.date_lbl.config(text=now.strftime("%B %d, %Y"))
        self.time_lbl.config(text=now.strftime("%I:%M:%S %p"))

        # countdown if available
        if self._countdown > 0:
            self._countdown -= 1
        else:
            # trigger refresh
            self.fetch_weather()

        self.countdown_lbl.config(text=f"Next update in {self._countdown} seconds")
        self.after(1000, self.update_clock)

    def set_city(self, name):
        self.city_lbl.config(text=name)

    def set_temps(self, celsius):
        self.temp_c_lbl.config(text=f"{round(celsius)}{DEG}C")
        fahrenheit = celsius * 9/5 + 32
        self.temp_f_lbl.config(text=f"{round(fahrenheit)}{DEG}F")

    def set_icon_from_code(self, icon_code):
        if not icon_code:
            self.icon_lbl.config(image="", text="")
            return
        if not PIL_AVAILABLE:
            self.icon_lbl.config(text=icon_code)  
            return
        try:
            url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            
            self.icon_img = ImageTk.PhotoImage(img)
            self.icon_lbl.config(image=self.icon_img)
        except Exception:
            self.icon_lbl.config(text=icon_code)

    def set_details(self, data):
        # expects dict with keys used in self.details
        for k, (lbl, unit) in self.details.items():
            val = data.get(k, "-")
            if k == "visibility_km" and isinstance(val, (int, float)):
                lbl.config(text=f"{val:.1f}{unit}")
            elif k == "feels_like" and isinstance(val, (int, float)):
                lbl.config(text=f"{round(val)}{DEG}C")
            elif isinstance(val, (int, float)):
                lbl.config(text=f"{val}{unit}")
            else:
                lbl.config(text=str(val))

    # *-*-*-*-*-* Weather fetching *-*-*-*-*-*
    def fetch_weather(self):
        city = self.config_data.get("city", "Sarnia")
        api_key = self.config_data.get("api_key", "").strip()
        units = self.config_data.get("units", "metric")
        interval_minutes = int(self.config_data.get("interval_minutes", 5))

        self.set_city(city)

        if not api_key or "PUT_YOUR_OPENWEATHER_API_KEY_HERE" in api_key:
            self.countdown_lbl.config(text="Please set your OpenWeather API key in config.json.")
            self._countdown = 10  
            return

        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": api_key, "units": units}
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            w = r.json()

            # core values
            temp_c = w["main"]["temp"] if units == "metric" else (w["main"]["temp"] - 273.15 if units == "standard" else (w["main"]["temp"] - 32) * 5/9)
            feels_like = w["main"]["feels_like"] if units == "metric" else (w["main"]["feels_like"] - 273.15 if units == "standard" else (w["main"]["feels_like"] - 32) * 5/9)

            self.set_temps(temp_c)
            icon_code = (w.get("weather") or [{}])[0].get("icon")
            self.set_icon_from_code(icon_code)

            details = {
                "feels_like": feels_like,
                "humidity": w["main"].get("humidity"),
                "clouds": w.get("clouds", {}).get("all"),
                "pressure": w["main"].get("pressure"),
                "visibility_km": (w.get("visibility", 0) or 0) / 1000.0,
                "wind_speed": w.get("wind", {}).get("speed"),
            }
            self.set_details(details)

            # reset countdown
            self._countdown = max(5, interval_minutes * 60)
        except requests.HTTPError as e:
            self.countdown_lbl.config(text=f"HTTP error: {e}")
            self._countdown = 30
        except Exception as e:
            self.countdown_lbl.config(text=f"Error: {e}")
            self._countdown = 30


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
