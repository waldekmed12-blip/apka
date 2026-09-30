import math
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
import requests
import pyttsx3

# ==========================================
# 1. MODUŁ SYNTEZATORA MOWY (WĄTKOWY)
# ==========================================
class VoiceAssistant:
    def __init__(self):
        self.q = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
        except Exception as e:
            print(f"Błąd inicjalizacji TTS: {e}")
            return

        while self.running:
            try:
                text = self.q.get(timeout=0.5)
                if text:
                    engine.say(text)
                    engine.runAndWait()
                self.q.task_done()
            except queue.Empty:
                continue

    def speak(self, text):
        # Wrzucamy do kolejki tylko jeśli nie ma tam zaległych wiadomości (unikanie opóźnień)
        if self.q.qsize() < 2:
            self.q.put(text)

    def stop(self):
        self.running = False


# ==========================================
# 2. LOGIKA TARYFIKATORA I PUNKTÓW
# ==========================================
def calculate_violation(current_speed, speed_limit, current_total_points=17):
    tolerance = 10  # Ludzki margines tolerancji (+10 km/h)
    excess = current_speed - speed_limit

    if excess <= tolerance:
        return None

    over_speed = excess
    mandat = 0
    punkty = 0

    if over_speed <= 10:
        mandat, punkty = 50, 1
    elif over_speed <= 15:
        mandat, punkty = 100, 2
    elif over_speed <= 20:
        mandat, punkty = 200, 3
    elif over_speed <= 25:
        mandat, punkty = 300, 5
    elif over_speed <= 30:
        mandat, punkty = 400, 7
    elif over_speed <= 40:
        mandat, punkty = 800, 9
    elif over_speed <= 50:
        mandat, punkty = 1000, 11
    elif over_speed <= 60:
        mandat, punkty = 1500, 13
    elif over_speed <= 70:
        mandat, punkty = 2000, 14
    else:
        mandat, punkty = 2500, 15

    new_total_points = current_total_points + punkty
    loss_license = new_total_points >= 24

    return {
        "over_speed": over_speed,
        "mandat": mandat,
        "punkty": punkty,
        "total_points": new_total_points,
        "loss_license": loss_license
    }


# ==========================================
# 3. KLASA GŁÓWNA APLIKACJI (TKINTER + GPS + OSM)
# ==========================================
class SpeedAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Polski Asystent Prędkości")
        self.root.geometry("400x500")
        self.root.config(bg="#1e1e1e")

        self.is_running = False
        self.voice = VoiceAssistant()

        # Stan pojazdu i pozycji
        self.current_lat = 51.7592  # Domyślnie Łódź
        self.current_lon = 19.4560
        self.current_speed = 0.0
        self.current_limit = 50     # Domyślny limit
        self.last_osm_lat = 0.0
        self.last_osm_lon = 0.0
        
        # Twój stan punktów
        self.user_points = 17
        
        # Kontrola częstotliwości komunikatów głosowych (anty-spam)
        self.last_warning_time = 0

        self.create_widgets()

    def create_widgets(self):
        title_label = tk.Label(self.root, text="ASYSTENT PRĘDKOŚCI", font=("Arial", 16, "bold"), fg="#ffffff", bg="#1e1e1e")
        title_label.pack(pady=15)

        # Status punktów
        self.lbl_points = tk.Label(self.root, text=f"Twoje punkty: {self.user_points} / 24", font=("Arial", 11), fg="#ffcc00", bg="#1e1e1e")
        self.lbl_points.pack(pady=5)

        # Prędkość bieżąca
        self.lbl_speed = tk.Label(self.root, text="0 km/h", font=("Arial", 38, "bold"), fg="#00ffcc", bg="#1e1e1e")
        self.lbl_speed.pack(pady=10)

        # Ograniczenie prędkości
        self.lbl_limit = tk.Label(self.root, text="Limit: -- km/h", font=("Arial", 16), fg="#ffffff", bg="#1e1e1e")
        self.lbl_limit.pack(pady=5)

        # Komunikat o stanie / ostrzeżenia
        self.lbl_status = tk.Label(self.root, text="Status: Zatrzymany", font=("Arial", 11), fg="#aaaaaa", bg="#1e1e1e")
        self.lbl_status.pack(pady=15)

        # Przycisk START / STOP
        self.btn_toggle = tk.Button(self.root, text="URUCHOM ASYSTENTA", font=("Arial", 14, "bold"), bg="#28a745", fg="white", 
                                    activebackground="#218838", activeforeground="white", relief="flat", command=self.toggle_assistant)
        self.btn_toggle.pack(ipadx=20, ipady=10, pady=20)

        # Informacja na dole
        info_text = tk.Info if hasattr(tk, 'Info') else "Margines tolerancji: +10 km/h"
        lbl_info = tk.Label(self.root, text="Zabezpieczenie: Tolerancja 10 km/h\nObsługa Overpass API + Taryfikator 2026", font=("Arial", 9), fg="#666666", bg="#1e1e1e")
        lbl_info.pack(side="bottom", pady=10)

    def toggle_assistant(self):
        if not self.is_running:
            self.is_running = True
            self.btn_toggle.config(text="ZATRZYMAJ", bg="#dc3545")
            self.lbl_status.config(text="Status: Działa w tle...", fg="#00ff00")
            self.voice.speak("Asystent prędkości uruchomiony. Szerokiej drogi.")
            # Uruchomienie wątku pętli głównej
            threading.Thread(target=self.main_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="URUCHOM ASYSTENTA", bg="#28a745")
            self.lbl_status.config(text="Status: Zatrzymany", fg="#aaaaaa")
            self.voice.speak("Asystent zatrzymany.")

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        # Przybliżona odległość w metrach (Haversine lub uproszczona pitagorejska dla krótkich odcinków)
        dx = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
        dy = math.radians(lat2 - lat1)
        return math.sqrt(dx * dx + dy * dy) * 6371000

    def fetch_osm_speed_limit(self, lat, lon):
        # Odpytanie Overpass API o maxspeed w promieniu 25 metrów
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:3];
        way(around:25,{lat},{lon})[maxspeed];
        out tags;
        """
        try:
            response = requests.post(overpass_url, data=query, timeout=3)
            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                if elements:
                    tags = elements[0].get("tags", {})
                    maxspeed_str = tags.get("maxspeed")
                    if maxspeed_str and maxspeed_str.isdigit():
                        return int(maxspeed_str)
        except Exception:
            pass # W razie braku internetu lub błędu serwera zwracamy None
        return None

    def main_loop(self):
        while self.is_running:
            # TODO: Tutaj podepnij realny odczyt z GPS telefonu / modułu USB
            # Na potrzeby testu symulujemy delikatny ruch lub zmienną prędkość
            # self.current_speed = pobierz_z_gps() 
            
            # Sprawdzenie czy ruszyliśmy się o więcej niż 30 metrów, żeby odpytać OSM
            distance_moved = self.calculate_distance(self.last_osm_lat, self.last_osm_lon, self.current_lat, self.current_lon)
            if distance_moved > 30 or self.last_osm_lat == 0.0:
                limit = self.fetch_osm_speed_limit(self.current_lat, self.current_lon)
                if limit:
                    self.current_limit = limit
                else:
                    # Domyślny polski limit ustawowy (np. teren zabudowany)
                    self.current_limit = 50 
                self.last_osm_lat = self.current_lat
                self.last_osm_lon = self.current_lon

            # Analiza przekroczenia prędkości
            violation = calculate_violation(self.current_speed, self.current_limit, self.user_points)
            
            current_time = time.time()
            if violation and (current_time - self.last_warning_time > 8):  # Ostrzegaj maksymalnie raz na 8 sekund
                self.last_warning_time = current_time
                
                # Budowanie komunikatu głosowego
                msg = f"Uwaga! Przekroczenie o {violation['over_speed']} kilometrów na godzinę. Mandat {violation['mandat']} złotych, {violation['punkty']} punkty."
                if violation['loss_license']:
                    msg += " Uwaga! Przekroczyłeś dwadzieścia cztery punkty! Zagrożenie utratą prawa jazdy!"
                
                self.voice.speak(msg)

            # Aktualizacje interfejsu graficznego (bezpiecznie przez root.after)
            self.root.after(0, self.update_gui)
            
            time.sleep(1.0)

    def update_gui(self):
        self.lbl_speed.config(text=f"{int(self.current_speed)} km/h")
        self.lbl_limit.config(text=f"Limit: {self.current_limit} km/h")
        self.lbl_points.config(text=f"Twoje punkty: {self.user_points} / 24")
        
        # Zmiana koloru prędkości w zależności od przekroczenia
        if self.current_speed > (self.current_limit + 10):
            self.lbl_speed.config(fg="#ff4d4d")  # Czerwony - za szybko
        else:
            self.lbl_speed.config(fg="#00ffcc")  # Zielony - bezpiecznie

    def on_closing(self):
        self.is_running = False
        self.voice.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeedAssistantApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
