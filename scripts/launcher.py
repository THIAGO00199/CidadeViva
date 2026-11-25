#!/usr/bin/env python3
import subprocess
import threading
import time
import urllib.request
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "scripts" / "start.sh"
LOG = ROOT / "logs" / "launcher.log"
URL = "http://127.0.0.1:5173"

def ready(url):
    try:
        with urllib.request.urlopen(url, timeout=1.2) as response:
            return response.status < 400
    except Exception:
        return False

def open_city():
    commands = [
        ["chromium", "--app=" + URL, "--class=CidadeViva"],
        ["chromium-browser", "--app=" + URL, "--class=CidadeViva"],
        ["google-chrome", "--app=" + URL, "--class=CidadeViva"],
        ["firefox", "--new-window", URL],
        ["xdg-open", URL],
    ]
    for command in commands:
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            status.set("Cidade aberta no navegador.")
            return
        except FileNotFoundError:
            continue
    status.set("Não encontrei um navegador instalado.")

def launch_services():
    start_button.config(state="disabled")
    status.set("Preparando a cidade...")
    def worker():
        if not ready(URL):
            ROOT.joinpath("logs").mkdir(exist_ok=True)
            with open(LOG, "a") as output:
                subprocess.Popen(["bash", str(START)], cwd=ROOT, stdout=output,
                                 stderr=output, start_new_session=True)
        for _ in range(60):
            if ready(URL):
                root.after(0, lambda: status.set("Cidade pronta."))
                root.after(0, open_city)
                root.after(0, lambda: start_button.config(state="normal"))
                return
            time.sleep(1)
        root.after(0, lambda: status.set("A cidade demorou para iniciar. Consulte logs/launcher.log."))
        root.after(0, lambda: start_button.config(state="normal"))
    threading.Thread(target=worker, daemon=True).start()

def close_services():
    subprocess.Popen(["bash", str(ROOT / "scripts" / "stop.sh")], cwd=ROOT)
    status.set("Serviços encerrados.")

root = tk.Tk()
root.title("Cidade Viva")
root.geometry("390x270")
root.resizable(False, False)
root.configure(bg="#111a14")
try:
    root.iconphoto(True, tk.PhotoImage(file=str(ROOT / "frontend" / "public" / "assets" / "icon.png")))
except tk.TclError:
    pass
status = tk.StringVar(value="Sua cidade está aguardando.")
tk.Label(root, text="CIDADE VIVA", bg="#111a14", fg="#e5d4a5",
         font=("DejaVu Sans", 18, "bold")).pack(pady=(25, 5))
tk.Label(root, text="Um mundo pequeno. Vidas inteiras.", bg="#111a14",
         fg="#9eae9e", font=("DejaVu Sans", 9)).pack(pady=(0, 18))
start_button = tk.Button(root, text="INICIAR E ABRIR A CIDADE", command=launch_services,
          bg="#354a35", fg="#f0f3e9", activebackground="#486348",
          relief="flat", font=("DejaVu Sans", 10, "bold"), padx=14, pady=11)
start_button.pack(fill="x", padx=35)
tk.Button(root, text="ABRIR CIDADE (JÁ INICIADA)", command=open_city,
          bg="#253328", fg="#d6dfd2", activebackground="#354a35",
          relief="flat", padx=10, pady=8).pack(fill="x", padx=35, pady=8)
tk.Button(root, text="ENCERRAR SERVIÇOS", command=close_services,
          bg="#2b2921", fg="#d6c99e", activebackground="#413c2b",
          relief="flat", padx=10, pady=7).pack(fill="x", padx=35)
tk.Label(root, textvariable=status, bg="#111a14", fg="#a8b49f",
         font=("DejaVu Sans", 8), wraplength=340).pack(pady=12)
root.mainloop()
