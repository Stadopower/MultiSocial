import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
import os
import threading
import sys

sys.path.append(os.path.dirname(__file__))

from platforms import bluesky, instagram, pinterest, X

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# ── Colours ───────────────────────────────────────────────────────────────────
BG      = "#0f0f0f"
SURFACE = "#1a1a1a"
CARD    = "#222222"
ACCENT  = "#47B5E7"
FG      = "#f0f0f0"
FG_DIM  = "#666666"
ENTRY   = "#2a2a2a"
BORDER  = "#333333"
SUCCESS = "#00e676"
ERROR   = "#ff1744"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MultiSocial")
        self.root.geometry("620x820")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.image_paths = []
        self.config = self._load_config()

        self._build()

    # ── Config ────────────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "twitter":   {"api_key": "", "api_secret": "", "access_token": "", "access_token_secret": ""},
            "instagram": {"username": "", "password": ""},
            "bluesky":   {"handle": "", "app_password": ""},
            "pinterest": {"access_token": "", "board_id": ""},
        }

    def _save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=ACCENT, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="MULTISOCIAL", font=("Courier", 18, "bold"),
                 bg=ACCENT, fg=BG).pack(side=tk.LEFT, padx=20)
        tk.Button(hdr, text="⚙ Settings", font=("Courier", 10),
                  bg=ACCENT, fg=BG, relief=tk.FLAT, cursor="hand2",
                  command=self._open_settings).pack(side=tk.RIGHT, padx=16)

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ── Post text ──
        self._label(outer, "POST TEXT")
        self.text_box = scrolledtext.ScrolledText(
            outer, height=7, bg=ENTRY, fg=FG,
            font=("Courier", 11), insertbackground=FG,
            wrap=tk.WORD, bd=0, padx=10, pady=8,
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT
        )
        self.text_box.pack(fill=tk.X, pady=(4, 14))
        self.text_box.bind("<KeyRelease>", self._update_char_count)

        self.char_label = tk.Label(outer, text="0 chars", font=("Courier", 9),
                                   bg=BG, fg=FG_DIM, anchor="e")
        self.char_label.pack(fill=tk.X, pady=(0, 14))

        # ── Image ──
        self._label(outer, "IMAGE")
        img_row = tk.Frame(outer, bg=BG)
        img_row.pack(fill=tk.X, pady=(4, 14))

        tk.Button(img_row, text="Browse", font=("Courier", 10, "bold"),
                  bg=CARD, fg=ACCENT, relief=tk.FLAT, cursor="hand2",
                  padx=14, pady=6, command=self._browse).pack(side=tk.LEFT)

        self.img_label = tk.Label(img_row, text="No image selected",
                                  font=("Courier", 10), bg=BG, fg=FG_DIM)
        self.img_label.pack(side=tk.LEFT, padx=12)

        tk.Button(img_row, text="✕", font=("Courier", 10),
                  bg=BG, fg=FG_DIM, relief=tk.FLAT, cursor="hand2",
                  command=self._clear_image).pack(side=tk.RIGHT)
        
        self._label(outer, "PINTEREST TITLE (optional)")
        self.title_entry = tk.Entry(outer, bg=ENTRY, fg=FG, font=("Courier", 11),
                            insertbackground=FG, bd=0,
                            highlightthickness=1, highlightbackground=BORDER,
                            highlightcolor=ACCENT)
        self.title_entry.pack(fill=tk.X, ipady=7, pady=(4, 14))

        # ── Platforms ──
        self._label(outer, "POST TO")
        plat_frame = tk.Frame(outer, bg=BG)
        plat_frame.pack(fill=tk.X, pady=(4, 20))

        self.post_x     = tk.BooleanVar(value=True)
        self.post_ig    = tk.BooleanVar(value=True)
        self.post_bsky  = tk.BooleanVar(value=True)
        self.post_pint  = tk.BooleanVar(value=True)

        for text, var in [
            ("𝕏  Twitter", self.post_x),
            ("📸 Instagram", self.post_ig),
            ("☁  Bluesky", self.post_bsky),
            ("📌 Pinterest", self.post_pint),
        ]:
            tk.Checkbutton(plat_frame, text=text, variable=var,
                           bg=BG, fg=FG, selectcolor=CARD,
                           activebackground=BG, activeforeground=FG,
                           font=("Courier", 11)).pack(side=tk.LEFT, padx=(0, 20))

        # ── Post button ──
        self.post_btn = tk.Button(outer, text="POST NOW",
                                  command=self._on_post,
                                  bg=ACCENT, fg=BG,
                                  font=("Courier", 14, "bold"),
                                  relief=tk.FLAT, cursor="hand2",
                                  pady=12)
        self.post_btn.pack(fill=tk.X)

        # ── Status ──
        self.status = tk.Label(outer, text="", font=("Courier", 10),
                               bg=BG, fg=SUCCESS, justify=tk.LEFT,
                               wraplength=560, anchor="w")
        self.status.pack(fill=tk.X, pady=(14, 0))

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=("Courier", 9, "bold"),
                 bg=BG, fg=FG_DIM).pack(anchor="w")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _update_char_count(self, _=None):
        count = len(self.text_box.get("1.0", tk.END).strip())
        self.char_label.config(text=f"{count} chars",
                               fg=ERROR if count > 280 else FG_DIM)

    def _browse(self):
        paths = list(filedialog.askopenfilenames(
        filetypes=[("Images", "*.jpg *.jpeg *.png"), ("All", "*.*")]
        ))
        if not paths:
            return
        self._open_reorder_window(paths)

    def _open_reorder_window(self, paths):
        win = tk.Toplevel(self.root)
        win.title("Order Images")
        win.geometry("400x500")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, text="DRAG TO REORDER", font=("Courier", 10, "bold"),
                bg=BG, fg=FG_DIM).pack(pady=(16, 8))

        listbox = tk.Listbox(win, bg=ENTRY, fg=FG, font=("Courier", 10),
                            selectbackground=ACCENT, selectforeground=BG,
                            bd=0, highlightthickness=1,
                            highlightbackground=BORDER, activestyle="none")
        listbox.pack(fill=tk.BOTH, expand=True, padx=20)

        for path in paths:
            listbox.insert(tk.END, os.path.basename(path))

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(pady=12)

        def move(direction):
            selected = listbox.curselection()
            if not selected:
                return
            i = selected[0]
            j = i + direction
            if j < 0 or j >= listbox.size():
                return
            # Swap in listbox
            a, b = listbox.get(i), listbox.get(j)
            listbox.delete(i)
            listbox.insert(i, b)
            listbox.delete(j)
            listbox.insert(j, a)
            # Swap in paths list
            paths[i], paths[j] = paths[j], paths[i]
            listbox.select_set(j)

        tk.Button(btn_row, text="▲ Up", command=lambda: move(-1),
                bg=CARD, fg=ACCENT, font=("Courier", 10, "bold"),
                relief=tk.FLAT, cursor="hand2", padx=16, pady=6).pack(side=tk.LEFT, padx=8)

        tk.Button(btn_row, text="▼ Down", command=lambda: move(1),
                bg=CARD, fg=ACCENT, font=("Courier", 10, "bold"),
                relief=tk.FLAT, cursor="hand2", padx=16, pady=6).pack(side=tk.LEFT, padx=8)

        def confirm():
            self.image_paths = paths
            names = ", ".join(os.path.basename(p) for p in paths)
            self.img_label.config(text=names, fg=SUCCESS)
            win.destroy()

        tk.Button(win, text="CONFIRM", command=confirm,
                bg=ACCENT, fg=BG, font=("Courier", 12, "bold"),
                relief=tk.FLAT, cursor="hand2", pady=10).pack(fill=tk.X, padx=20, pady=(0, 16))

    def _clear_image(self):
        self.image_paths = None
        self.img_label.config(text="No image selected", fg=FG_DIM)

    def _on_post(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Empty", "Please write some text first.")
            return
        if not any([self.post_x.get(), self.post_ig.get(),
                    self.post_bsky.get(), self.post_pint.get()]):
            messagebox.showwarning("No Platform", "Select at least one platform.")
            return

        self.post_btn.config(state=tk.DISABLED, text="POSTING…")
        self.status.config(text="")
        threading.Thread(target=self._do_post, args=(text,), daemon=True).start()

    def _do_post(self, text: str):
        results = []
        if self.post_x.get():
            results.append("𝕏  " + X.post(text, self.config["twitter"], self.image_paths))
        if self.post_ig.get():
            results.append("📸 " + instagram.post(text, self.config["instagram"], self.image_paths))
        if self.post_bsky.get():
            results.append("☁  " + bluesky.post(text, self.config["bluesky"], self.image_paths))
        if self.post_pint.get():
            title = self.title_entry.get().strip or None
            results.append("📌 " + pinterest.post(text, self.config["pinterest"], title, self.image_paths))
        self.root.after(0, self._post_done, "\n".join(results))

    def _post_done(self, message: str):
        all_ok = "❌" not in message and "ERROR" not in message
        self.status.config(text=message, fg=SUCCESS if all_ok else ERROR)
        self.post_btn.config(state=tk.NORMAL, text="POST NOW")

    # ── Settings popup ────────────────────────────────────────────────────────

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("500x620")
        win.configure(bg=BG)
        win.grab_set()

        canvas = tk.Canvas(win, bg=BG, bd=0, highlightthickness=0)
        vsb = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sf = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0, 0), window=sf, anchor="nw")
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))

        inner = tk.Frame(sf, bg=BG)
        inner.pack(fill=tk.X, padx=20, pady=20)

        entries = {}

        sections = [
            ("𝕏  TWITTER", "twitter", [
                ("API Key",              "api_key",            False),
                ("API Secret",           "api_secret",         True),
                ("Access Token",         "access_token",       False),
                ("Access Token Secret",  "access_token_secret",True),
            ]),
            ("📸 INSTAGRAM", "instagram", [
                ("Username", "username", False),
                ("Password", "password", True),
            ]),
            ("☁  BLUESKY", "bluesky", [
                ("Handle",       "handle",       False),
                ("App Password", "app_password", True),
            ]),
            ("📌 PINTEREST", "pinterest", [
                ("Access Token", "access_token", True),
                ("Board ID",     "board_id",     False),
            ]),
        ]

        for title, section, fields in sections:
            tk.Label(inner, text=title, font=("Courier", 10, "bold"),
                     bg=BG, fg=ACCENT).pack(anchor="w", pady=(14, 4))

            for label, key, secret in fields:
                row = tk.Frame(inner, bg=BG)
                row.pack(fill=tk.X, pady=2)
                tk.Label(row, text=label, font=("Courier", 9), bg=BG,
                         fg=FG_DIM, width=22, anchor="w").pack(side=tk.LEFT)
                e = tk.Entry(row, bg=ENTRY, fg=FG, font=("Courier", 10),
                             insertbackground=FG, show="•" if secret else "",
                             bd=0, highlightthickness=1,
                             highlightbackground=BORDER, highlightcolor=ACCENT)
                e.insert(0, self.config.get(section, {}).get(key, ""))
                e.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, ipadx=4)
                entries[(section, key)] = e

        def save():
            for (section, key), entry in entries.items():
                self.config[section][key] = entry.get().strip()
            self._save_config()
            win.destroy()

        tk.Button(inner, text="SAVE", command=save,
                  bg=ACCENT, fg=BG, font=("Courier", 12, "bold"),
                  relief=tk.FLAT, cursor="hand2", pady=10).pack(fill=tk.X, pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()