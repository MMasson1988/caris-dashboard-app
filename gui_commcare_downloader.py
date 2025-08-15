# gui_commcare_downloader.py
# -*- coding: utf-8 -*-
import os, sys, threading, queue, logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

MODULE_NAME = "commcare_downloader"
ID_ENV_FILENAME = "id_cc.env"

try:
    downloader = __import__(MODULE_NAME)
except Exception as e:
    raise SystemExit(
        f"Impossible d'importer le module '{MODULE_NAME}'. "
        f"Place ton script comme '{MODULE_NAME}.py' dans ce dossier.\nErreur: {e}"
    )

log_queue = queue.Queue()

class TkQueueHandler(logging.Handler):
    def emit(self, record):
        try: log_queue.put_nowait(record)
        except Exception: pass

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
formatter = logging.Formatter(LOG_FORMAT, datefmt="%H:%M:%S")
root_logger = logging.getLogger(); root_logger.setLevel(logging.INFO)
gui_handler = TkQueueHandler(); gui_handler.setFormatter(formatter); root_logger.addHandler(gui_handler)
for h in list(root_logger.handlers):
    if h is not gui_handler:
        root_logger.removeHandler(h)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CommCare Smart Downloader — GUI")
        self.geometry("980x680"); self.minsize(900, 600)
        self.running_thread = None
        self.keep_env_file = tk.BooleanVar(value=False)
        self.headless_var = tk.BooleanVar(value=bool(getattr(downloader, "HEADLESS", False)))
        self.email_var = tk.StringVar(); self.pass_var = tk.StringVar()
        default_dir = getattr(downloader, "DOWNLOAD_DIR", str(Path.home() / "Downloads"))
        self.dir_var = tk.StringVar(value=default_dir)
        self.base_vars = []
        self._build_ui(); self._load_expected_bases(); self._poll_log_queue()

    def _build_ui(self):
        form = ttk.Frame(self, padding=10); form.pack(fill="x")
        row1 = ttk.Frame(form); row1.pack(fill="x", pady=(0,8))
        ttk.Label(row1, text="Email:", width=12).pack(side="left")
        ttk.Entry(row1, textvariable=self.email_var, width=40).pack(side="left", padx=(0,10))
        ttk.Label(row1, text="Mot de passe:", width=14).pack(side="left")
        pwd = ttk.Entry(row1, textvariable=self.pass_var, width=30, show="•"); pwd.pack(side="left", padx=(0,10))
        ttk.Checkbutton(row1, text="Afficher", command=lambda: pwd.config(show="" if pwd.cget("show")=="•" else "•")).pack(side="left")
        row2 = ttk.Frame(form); row2.pack(fill="x", pady=(0,8))
        ttk.Label(row2, text="Dossier téléchargement:", width=20).pack(side="left")
        ttk.Entry(row2, textvariable=self.dir_var).pack(side="left", fill="x", expand=True, padx=(0,6))
        ttk.Button(row2, text="Parcourir…", command=self._browse_dir).pack(side="left", padx=(0,10))
        ttk.Checkbutton(row2, text="Headless (sans fenêtre Chrome)", variable=self.headless_var).pack(side="left")
        row3 = ttk.Frame(form); row3.pack(fill="x", pady=(0,8))
        ttk.Checkbutton(row3, text="Conserver id_cc.env (ne pas supprimer après)", variable=self.keep_env_file).pack(side="left")
        sel = ttk.LabelFrame(self, text="Exports CommCare à télécharger", padding=10); sel.pack(fill="both", expand=False, padx=10, pady=(0,10))
        canvas = tk.Canvas(sel, height=160); scroll = ttk.Scrollbar(sel, orient="vertical", command=canvas.yview)
        self.list_frame = ttk.Frame(canvas)
        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.list_frame, anchor="nw"); canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        btns = ttk.Frame(self, padding=(10,0,10,10)); btns.pack(fill="x")
        self.run_btn = ttk.Button(btns, text="▶ Lancer", command=self._on_run, width=18); self.run_btn.pack(side="left")
        ttk.Button(btns, text="🧹 Effacer logs", command=self._clear_logs).pack(side="left", padx=6)
        ttk.Button(btns, text="📂 Ouvrir dossier", command=self._open_folder).pack(side="left")
        ttk.Button(btns, text="Quitter", command=self._on_quit).pack(side="right")
        logs_box = ttk.LabelFrame(self, text="Logs", padding=8); logs_box.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.text = tk.Text(logs_box, wrap="word"); self.text.pack(side="left", fill="both", expand=True)
        tscroll = ttk.Scrollbar(logs_box, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=tscroll.set); tscroll.pack(side="right", fill="y")
        self.text.tag_configure("INFO", foreground="#0a5")
        self.text.tag_configure("WARNING", foreground="#c90")
        self.text.tag_configure("ERROR", foreground="#d11")
        self.text.tag_configure("CRITICAL", foreground="#d11", underline=True)
        self.status = ttk.Label(self, text="Prêt.", anchor="w", relief="sunken"); self.status.pack(fill="x", side="bottom")

    def _load_expected_bases(self):
        bases = list(getattr(downloader, "EXPECTED_BASES", [])) or list(getattr(downloader, "EXPORT_URLS", {}).keys())
        bases = sorted(bases, key=str.lower)
        head = ttk.Frame(self.list_frame); head.pack(fill="x")
        self.select_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(head, text="(Tout sélectionner / désélectionner)", variable=self.select_all_var, command=self._toggle_all).pack(side="left")
        ttk.Label(head, text="  —  Exécuter uniquement les éléments cochés").pack(side="left")
        for b in bases:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.list_frame, text=b, variable=var).pack(anchor="w")
            self.base_vars.append((b, var))

    def _toggle_all(self):
        for _, v in self.base_vars: v.set(self.select_all_var.get())

    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get() or str(Path.home()))
        if d: self.dir_var.set(d)

    def _open_folder(self):
        path = self.dir_var.get(); p = Path(path)
        if not p.exists(): messagebox.showerror("Erreur", f"Dossier introuvable: {p}"); return
        try:
            if sys.platform.startswith("win"): os.startfile(str(p))
            elif sys.platform == "darwin": os.system(f"open '{p}'")
            else: os.system(f"xdg-open '{p}'")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier: {e}")

    def _clear_logs(self): self.text.delete("1.0", "end")
    def _append_log(self, text, level="INFO"): self.text.insert("end", text, level); self.text.see("end")

    def _poll_log_queue(self):
        import queue as q
        try:
            while True:
                record = log_queue.get_nowait()
                msg = formatter.format(record) + "\n"
                level = record.levelname if record.levelname in ("INFO","WARNING","ERROR","CRITICAL") else "INFO"
                self._append_log(msg, level); self.status.config(text=f"Dernier message: {record.levelname}")
        except q.Empty: pass
        self.after(120, self._poll_log_queue)

    def _on_run(self):
        if self.running_thread and self.running_thread.is_alive():
            messagebox.showinfo("En cours", "Un téléchargement est déjà en cours."); return
        selected = [b for (b,v) in self.base_vars if v.get()]
        if not selected: messagebox.showwarning("Sélection vide", "Coche au moins un export à exécuter."); return
        dl_dir = self.dir_var.get().strip()
        if not dl_dir: messagebox.showwarning("Dossier manquant", "Choisis un dossier de téléchargement."); return
        Path(dl_dir).mkdir(parents=True, exist_ok=True)
        downloader.DOWNLOAD_DIR = dl_dir; downloader.HEADLESS = bool(self.headless_var.get()); downloader.EXPECTED_BASES = selected
        email = self.email_var.get().strip(); password = self.pass_var.get().strip()
        if not email or not password:
            if not messagebox.askyesno("Sans identifiants","EMAIL/PASSWORD non renseignés.\nLe script essaiera d'utiliser un id_cc.env existant.\nContinuer ?"):
                return
        def write_env():
            if not email or not password: return None
            Path(ID_ENV_FILENAME).write_text(f"EMAIL={email}\nPASSWORD={password}\n", encoding="utf-8"); return Path(ID_ENV_FILENAME)
        env_path = write_env()
        self.run_btn.config(state="disabled"); self.status.config(text="Exécution en cours…"); self._append_log("\n=== LANCEMENT ===\n", "INFO")
        def worker():
            try:
                downloader.main_enhanced()
            except Exception as e:
                logging.getLogger().exception(f"Erreur pendant l'exécution: {e}")
            finally:
                if env_path and not self.keep_env_file.get():
                    try: Path(env_path).unlink(missing_ok=True); logging.getLogger().info("Fichier id_cc.env temporaire supprimé.")
                    except Exception: pass
                self.after(0, lambda: self.run_btn.config(state="normal")); self.after(0, lambda: self.status.config(text="Terminé."))
        self.running_thread = threading.Thread(target=worker, daemon=True); self.running_thread.start()

    def _on_quit(self):
        if self.running_thread and self.running_thread.is_alive():
            if not messagebox.askyesno("Quitter ?", "Un traitement est en cours. Quitter quand même ?"): return
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
