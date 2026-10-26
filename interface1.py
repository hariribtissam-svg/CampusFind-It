"""
FindIt - interface.py (Membre 2 : Edouarda)
Interface Tkinter connectée à la base SQLite (database/User.py, objects.py, restitutions.py).
Lancer : python main.py   (ou python interface.py pour tester seule)
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from database import User, objects, restitutions
from database.connection import get_connection
from forms import (SIDEBAR_BG, SIDEBAR_HOVER, ACCENT, G1, G2, BG, CARD, TEXT, MUTED, BORDER,
                   COLORS, BADGES, CLAIM_COLORS, FONT, FONT_B, TITLE, CATEGORIES, ICONS,
                   SB_W, TOPBAR_H, mix, LoginWindow, DeclareForm, ask_claim_message)


def to_ui(r):
    """Ligne de la table objects (dict) -> dict utilisé par l'interface.
    Le statut affiché est « Restitué » si l'objet est rendu, sinon le type (Perdu / Trouvé)."""
    return {"id": r["id_object"], "nom": r["name_object"], "cat": r["category"],
            "lieu": r["location"], "date": r["date_declaration"],
            "statut": "Restitué" if r["status"] == "Restitué" else r["type_declaration"],
            "declarant": r["declarant_name"], "user_id": r["user_id"],
            "desc": r["description"] or ""}


class ScrollFrame(tk.Frame):
    """Frame défilable (molette + barre)."""
    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=20)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win, width=e.width))


class App(tk.Tk):
    current = None

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.logout_requested = False
        self.title(f"FindIt - {user['full_name']}")
        self.geometry("1150x700")
        self.minsize(900, 580)
        self.configure(bg=BG)

        self.items = []
        self.claims_sent, self.claims_recv = [], []

        self.sb_x, self.sb_target, self.sliding = -SB_W, -SB_W, False
        self.setup_style()
        self.build_topbar()

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)

        self.build_sidebar()   # placé par-dessus le contenu (tiroir)

        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="Tous")

        self.pages = {}
        self.home = ScrollFrame(self.content)
        self.page_home(self.home.inner)
        self.pages["Accueil"] = self.home
        for name, builder in [("Objets", self.page_items), ("Déclarer", self.page_declare),
                              ("Demandes", self.page_claims), ("Restitutions", self.page_returns)]:
            frame = tk.Frame(self.content, bg=BG)
            builder(frame)
            self.pages[name] = frame

        # Événements globaux
        self.bind_all("<MouseWheel>", self.on_wheel)
        self.bind_all("<Button-4>", self.on_wheel)
        self.bind_all("<Button-5>", self.on_wheel)
        self.bind_all("<Button-1>", self.on_global_click, add="+")
        self.bind("<Escape>", lambda e: self.set_sidebar(False))

        self.show_page("Accueil")

    # ---------- Style ----------
    def setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=34, borderwidth=0, font=FONT)
        s.configure("Treeview.Heading", background=BORDER, foreground=TEXT,
                    font=FONT_B, relief="flat", padding=8)
        s.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])
        s.configure("TCombobox", padding=6)

    # ---------- Barre du haut ----------
    def build_topbar(self):
        top = tk.Frame(self, bg=CARD, height=TOPBAR_H)
        top.pack(side="top", fill="x")
        top.pack_propagate(False)
        tk.Frame(self, bg=BORDER, height=1).pack(side="top", fill="x")

        self.menu_btn = tk.Label(top, text="☰", bg=CARD, fg=TEXT, font=("Segoe UI", 18),
                                 padx=18, cursor="hand2")
        self.menu_btn.pack(side="left", fill="y")
        self.menu_btn.bind("<Button-1>", lambda e: self.set_sidebar(self.sb_target != 0))
        self.menu_btn.bind("<Enter>", lambda e: self.menu_btn.config(bg=BG))
        self.menu_btn.bind("<Leave>", lambda e: self.menu_btn.config(bg=CARD))

        tk.Label(top, text="🎓  Campus Lost & Found", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=(4, 0))

        tk.Label(top, text=f"👤 {self.user['full_name']}", bg=CARD, fg=MUTED,
                 font=FONT_B).pack(side="right", padx=(0, 18))
        links = tk.Frame(top, bg=CARD)
        links.pack(side="right", padx=16)
        self.top_links = {}
        for name in ["Accueil", "Objets", "Déclarer", "Demandes", "Restitutions"]:
            f = tk.Frame(links, bg=CARD, cursor="hand2")
            f.pack(side="left", padx=2)
            lbl = tk.Label(f, text=name, bg=CARD, fg=MUTED, font=FONT_B, padx=14, pady=14)
            lbl.pack()
            ul = tk.Frame(f, bg=CARD, height=3)
            ul.pack(fill="x")
            self.top_links[name] = (lbl, ul)
            for w in (f, lbl):
                w.bind("<Button-1>", lambda e, n=name: self.show_page(n))
                w.bind("<Enter>", lambda e, l=lbl, n=name: l.config(fg=TEXT) if self.current != n else None)
                w.bind("<Leave>", lambda e, l=lbl, n=name: l.config(fg=MUTED) if self.current != n else None)

    # ---------- Barre latérale (tiroir) ----------
    def build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG)
        self.sidebar.place(x=-SB_W, y=TOPBAR_H + 1, width=SB_W, relheight=1, height=-(TOPBAR_H + 1))

        tk.Label(self.sidebar, text="Menu", bg=SIDEBAR_BG, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=22, pady=(26, 0))
        tk.Label(self.sidebar, text="Objets perdus & trouvés", bg=SIDEBAR_BG, fg="#94a3b8",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=22, pady=(0, 22))

        self.nav = {}
        for icon, name in [("🏠", "Accueil"), ("📦", "Objets"), ("➕", "Déclarer"), ("📨", "Demandes"), ("✅", "Restitutions")]:
            self.nav[name] = self.nav_button(icon, name, lambda n=name: self.show_page(n))

        tk.Frame(self.sidebar, bg=SIDEBAR_HOVER, height=1).pack(fill="x", padx=22, pady=14)
        self.nav_button("❓", "Aide", lambda: messagebox.showinfo(
            "Aide", "Déclarez un objet via « Déclarer », puis suivez-le dans « Objets ».\n"
                    "Pour un objet trouvé, utilisez « Faire une demande » ; suivez vos demandes dans « Demandes »."))
        self.nav_button("ℹ️", "À propos", lambda: messagebox.showinfo(
            "À propos", "Campus Lost & Found v2.0\nProjet universitaire - Tkinter"))

        self.nav_button("🚪", "Déconnexion", self.logout)

        tk.Label(self.sidebar, text="v2.0 • Université", bg=SIDEBAR_BG, fg="#64748b",
                 font=("Segoe UI", 8)).pack(side="bottom", pady=16)

    def nav_button(self, icon, name, cmd):
        row = tk.Frame(self.sidebar, bg=SIDEBAR_BG, cursor="hand2")
        row.pack(fill="x", pady=2)
        bar = tk.Frame(row, bg=SIDEBAR_BG, width=4)
        bar.pack(side="left", fill="y")
        lbl = tk.Label(row, text=f"  {icon}   {name}", bg=SIDEBAR_BG, fg="#cbd5e1",
                       font=("Segoe UI", 11), anchor="w", padx=14, pady=12)
        lbl.pack(side="left", fill="x", expand=True)

        def enter(_):
            if self.current != name:
                row.config(bg=SIDEBAR_HOVER); lbl.config(bg=SIDEBAR_HOVER)

        def leave(_):
            if self.current != name:
                row.config(bg=SIDEBAR_BG); lbl.config(bg=SIDEBAR_BG)

        def click(_):
            self.set_sidebar(False)
            cmd()

        for w in (row, lbl, bar):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", click)
        return row, bar, lbl

    def set_sidebar(self, open_):
        self.sb_target = 0 if open_ else -SB_W
        if open_:
            self.sidebar.lift()
        if not self.sliding:
            self.sliding = True
            self._slide()

    def _slide(self):
        diff = self.sb_target - self.sb_x
        if abs(diff) < 2:
            self.sb_x = self.sb_target
            self.sidebar.place_configure(x=int(self.sb_x))
            self.sliding = False
            return
        self.sb_x += diff * 0.3
        self.sidebar.place_configure(x=int(self.sb_x))
        self.after(12, self._slide)

    def on_global_click(self, e):
        if self.sb_target != 0:
            return
        w, s = str(e.widget), str(self.sidebar)
        if w == s or w.startswith(s + ".") or w == str(self.menu_btn):
            return
        self.set_sidebar(False)

    def on_wheel(self, e):
        if self.current != "Accueil":
            return
        if e.num == 4:
            d = -1
        elif e.num == 5:
            d = 1
        else:
            d = -1 if e.delta > 0 else 1
        self.home.canvas.yview_scroll(d * 2, "units")

    # ---------- Navigation ----------
    def show_page(self, name):
        self.current = name
        for n, (row, bar, lbl) in self.nav.items():
            active = n == name
            bg = SIDEBAR_HOVER if active else SIDEBAR_BG
            row.config(bg=bg); lbl.config(bg=bg, fg="white" if active else "#cbd5e1")
            bar.config(bg=ACCENT if active else bg)
        for n, (lbl, ul) in self.top_links.items():
            lbl.config(fg=ACCENT if n == name else MUTED)
            ul.config(bg=ACCENT if n == name else CARD)
        for p in self.pages.values():
            p.pack_forget()
        if name == "Accueil":
            self.pages[name].pack(fill="both", expand=True)
        else:
            self.pages[name].pack(fill="both", expand=True, padx=32, pady=26)
        self.reload()

    # ---------- Helpers ----------
    def header(self, parent, title, subtitle):
        tk.Label(parent, text=title, bg=BG, fg=TEXT, font=TITLE).pack(anchor="w")
        tk.Label(parent, text=subtitle, bg=BG, fg=MUTED, font=FONT).pack(anchor="w", pady=(0, 18))

    def make_tree(self, parent):
        cols, widths = ("Objet", "Catégorie", "Lieu", "Date", "Statut"), (260, 130, 140, 110, 100)
        wrap = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        for c, w in zip(cols, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w")
        for st, col in COLORS.items():
            tree.tag_configure(st, foreground=col)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return wrap, tree

    def fill(self, tree, items):
        tree.delete(*tree.get_children())
        for it in items:
            tree.insert("", "end", iid=str(it["id"]),
                        values=(it["nom"], it["cat"], it["lieu"], it["date"], it["statut"]),
                        tags=(it["statut"],))

    def button(self, parent, text, cmd, color=ACCENT):
        b = tk.Label(parent, text=text, bg=color, fg="white", font=FONT_B,
                     padx=18, pady=9, cursor="hand2")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>", lambda e: b.config(bg=mix(color, "#000000", 0.15)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    @staticmethod
    def bind_click(widget, cmd):
        widget.bind("<Button-1>", cmd)
        for ch in widget.winfo_children():
            App.bind_click(ch, cmd)

    def goto_search(self, text="", status="Tous"):
        self.search_var.set(text)
        self.filter_var.set(status)
        self.show_page("Objets")

    # ---------- PAGE D'ACCUEIL ----------
    def section_title(self, parent, title, sub):
        tk.Label(parent, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(38, 0))
        tk.Label(parent, text=sub, bg=BG, fg=MUTED, font=FONT).pack(anchor="w", pady=(2, 14))

    def page_home(self, p):
        # --- Bannière dégradée ---
        self.hero = tk.Canvas(p, height=310, highlightthickness=0, bd=0)
        self.hero.pack(fill="x")
        self.hero_var = tk.StringVar()
        self.hero_box = tk.Frame(self.hero, bg="white")
        tk.Label(self.hero_box, text=" 🔍", bg="white", font=("Segoe UI", 12)).pack(side="left")
        e = tk.Entry(self.hero_box, textvariable=self.hero_var, font=("Segoe UI", 11),
                     relief="flat", bd=0, bg="white", fg=TEXT, insertbackground=TEXT)
        e.pack(side="left", fill="both", expand=True, ipady=10, padx=6)
        e.bind("<Return>", lambda ev: self.hero_search())
        self.hero.bind("<Configure>", self.draw_hero)

        body = tk.Frame(p, bg=BG)
        body.pack(fill="x", padx=48)

        # --- Statistiques ---
        self.section_title(body, "En un coup d'œil", "L'état actuel des objets sur le campus")
        stats = tk.Frame(body, bg=BG)
        stats.pack(fill="x")
        self.stat_labels = {}
        for i, (key, label, color, icon) in enumerate([
                ("Total", "Total déclarés", ACCENT, "📋"), ("Perdu", "Perdus", COLORS["Perdu"], "😟"),
                ("Trouvé", "Trouvés", COLORS["Trouvé"], "🔎"), ("Restitué", "Restitués", COLORS["Restitué"], "🎉")]):
            stats.columnconfigure(i, weight=1, uniform="st")
            card = tk.Frame(stats, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            tk.Frame(card, bg=color, height=4).pack(fill="x")
            tk.Label(card, text=f"{icon}  {label}", bg=CARD, fg=MUTED, font=FONT).pack(anchor="w", padx=16, pady=(12, 0))
            v = tk.Label(card, text="0", bg=CARD, fg=TEXT, font=("Segoe UI", 30, "bold"))
            v.pack(anchor="w", padx=16, pady=(0, 12))
            self.stat_labels[key] = v

        # --- Comment ça marche ---
        self.section_title(body, "Comment ça marche ?", "Retrouvez vos affaires en trois étapes simples")
        steps = tk.Frame(body, bg=BG)
        steps.pack(fill="x")
        for i, (icon, t, d) in enumerate([
                ("📝", "Déclarez", "Signalez un objet perdu ou trouvé en quelques secondes avec le formulaire."),
                ("🔍", "Recherchez", "Parcourez la liste, filtrez par statut et trouvez la correspondance."),
                ("🤝", "Récupérez", "Rendez-vous au bureau des objets trouvés pour récupérer votre bien.")]):
            steps.columnconfigure(i, weight=1, uniform="sp")
            card = tk.Frame(steps, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            head = tk.Frame(card, bg=CARD)
            head.pack(fill="x", padx=20, pady=(20, 6))
            tk.Label(head, text=icon, bg=CARD, font=("Segoe UI Emoji", 26)).pack(side="left")
            tk.Label(head, text=str(i + 1), bg=ACCENT, fg="white", font=FONT_B, width=3).pack(side="right")
            tk.Label(card, text=t, bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20)
            tk.Label(card, text=d, bg=CARD, fg=MUTED, font=FONT, wraplength=250, justify="left").pack(
                anchor="w", padx=20, pady=(4, 22))

        # --- Objets récents ---
        self.section_title(body, "Récemment signalés", "Les dernières déclarations — cliquez pour voir la liste complète")
        self.recent_grid = tk.Frame(body, bg=BG)
        self.recent_grid.pack(fill="x")
        for c in range(3):
            self.recent_grid.columnconfigure(c, weight=1, uniform="rc")

        # --- Catégories ---
        self.section_title(body, "Parcourir par catégorie", "Accédez directement aux objets d'un type donné")
        chips = tk.Frame(body, bg=BG)
        chips.pack(fill="x")
        for cat in CATEGORIES:
            chip = tk.Label(chips, text=f"{ICONS[cat]}  {cat}", bg=CARD, fg=TEXT, font=FONT_B, padx=18, pady=10,
                            cursor="hand2", highlightbackground=BORDER, highlightthickness=1)
            chip.pack(side="left", padx=(0, 8), pady=4)
            chip.bind("<Button-1>", lambda e, c=cat: self.goto_search(c))
            chip.bind("<Enter>", lambda e, w=chip: w.config(bg=ACCENT, fg="white"))
            chip.bind("<Leave>", lambda e, w=chip: w.config(bg=CARD, fg=TEXT))

        # --- Pied de page ---
        foot = tk.Frame(p, bg=SIDEBAR_BG)
        foot.pack(fill="x", pady=(48, 0))
        fin = tk.Frame(foot, bg=SIDEBAR_BG)
        fin.pack(fill="x", padx=48, pady=30)
        for i, (t, lines) in enumerate([
                ("🎓 Campus Lost & Found", ["Le service qui vous aide à retrouver", "vos affaires sur le campus."]),
                ("📍 Bureau des objets trouvés", ["Bâtiment administratif, RDC", "Lun – Ven : 8h30 – 17h00"]),
                ("✉️ Contact", ["objets.trouves@univ.ma", "Tél : 05 22 00 00 00"])]):
            fin.columnconfigure(i, weight=1, uniform="ft")
            col = tk.Frame(fin, bg=SIDEBAR_BG)
            col.grid(row=0, column=i, sticky="nw")
            tk.Label(col, text=t, bg=SIDEBAR_BG, fg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            for ln in lines:
                tk.Label(col, text=ln, bg=SIDEBAR_BG, fg="#94a3b8", font=FONT).pack(anchor="w")
        tk.Label(foot, text="© 2026 Université • Tous droits réservés", bg=SIDEBAR_BG, fg="#64748b",
                 font=("Segoe UI", 8)).pack(pady=(0, 14))

    # --- Dessin de la bannière ---
    def rrect(self, c, x1, y1, x2, y2, r=14, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return c.create_polygon(pts, smooth=True, **kw)

    def canvas_button(self, c, x, y, w, h, text, cmd, fill, fg, outline=None):
        tag = f"btn{x}_{y}"
        kw = {"outline": outline, "width": 2} if outline else {"outline": ""}
        self.rrect(c, x, y, x + w, y + h, 18, fill=fill, tags=tag, **kw)
        c.create_text(x + w / 2, y + h / 2, text=text, fill=fg, font=("Segoe UI", 10, "bold"), tags=tag)
        c.tag_bind(tag, "<Button-1>", lambda e: cmd())
        c.tag_bind(tag, "<Enter>", lambda e: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))

    def draw_hero(self, _=None):
        c = self.hero
        w, h = c.winfo_width(), 310
        if w < 10:
            return
        c.delete("all")
        n = 90
        sw = w / n
        for i in range(n):
            c.create_rectangle(i * sw, 0, (i + 1) * sw + 1, h, fill=mix(G1, G2, i / (n - 1)), outline="")
        for cx, cy, r in [(w - 80, 30, 150), (w - 330, 300, 110), (w - 20, 290, 80), (w * 0.52, -40, 90)]:
            t = min(max(cx / w, 0), 1)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=mix(mix(G1, G2, t), "#ffffff", 0.10), outline="")
        if w > 780:
            c.create_oval(w - 300, 60, w - 100, 260, fill=mix(mix(G1, G2, 0.9), "#ffffff", 0.18), outline="")
            c.create_text(w - 200, 160, text="🎒", font=("Segoe UI Emoji", 80))
        x0 = 56
        c.create_text(x0, 28, text="PORTAIL ÉTUDIANT", anchor="w", fill="#c7d2fe", font=("Segoe UI", 9, "bold"))
        c.create_text(x0, 90, text="Perdu quelque chose\nsur le campus ?", anchor="w", fill="white",
                      font=("Segoe UI", 28, "bold"))
        c.create_text(x0, 160, text="Déclarez, recherchez et récupérez vos objets facilement.",
                      anchor="w", fill="#e0e7ff", font=("Segoe UI", 12))
        c.create_window(x0, 200, window=self.hero_box, anchor="nw", width=min(430, w - 2 * x0), height=44)
        self.canvas_button(c, x0, 258, 170, 36, "➕  Déclarer un objet", lambda: self.show_page("Déclarer"),
                           "white", ACCENT)
        self.canvas_button(c, x0 + 182, 258, 150, 36, "Voir les objets", lambda: self.goto_search(),
                           G2, "white", outline="#c7d2fe")

    def hero_search(self):
        self.goto_search(self.hero_var.get().strip())

    def refresh_home_cards(self):
        for w in self.recent_grid.winfo_children():
            w.destroy()
        latest = sorted(self.items, key=lambda i: i["date"], reverse=True)[:6]
        for k, it in enumerate(latest):
            r, c = divmod(k, 3)
            card = tk.Frame(self.recent_grid, bg=CARD, highlightbackground=BORDER,
                            highlightthickness=1, cursor="hand2")
            card.grid(row=r, column=c, sticky="nsew", padx=(0 if c == 0 else 10, 0), pady=(0, 10))
            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x", padx=16, pady=(14, 6))
            tk.Label(top, text=ICONS.get(it["cat"], "📦"), bg=CARD, font=("Segoe UI Emoji", 22)).pack(side="left")
            bg, fg = BADGES[it["statut"]]
            tk.Label(top, text=it["statut"], bg=bg, fg=fg, font=("Segoe UI", 9, "bold"),
                     padx=10, pady=2).pack(side="right")
            tk.Label(card, text=it["nom"], bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold"),
                     anchor="w").pack(fill="x", padx=16)
            tk.Label(card, text=f"📍 {it['lieu']}   •   {it['date']}", bg=CARD, fg=MUTED, font=("Segoe UI", 9),
                     anchor="w").pack(fill="x", padx=16, pady=(2, 14))
            self.bind_click(card, lambda e, n=it["nom"]: self.goto_search(n))

    # ---------- Autres pages ----------
    def page_items(self, p):
        self.header(p, "Objets", "Rechercher, filtrer et gérer les objets déclarés")
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        tk.Entry(bar, textvariable=self.search_var, font=FONT, relief="flat",
                 highlightbackground="#cbd5e1", highlightthickness=1, width=32).pack(
            side="left", ipady=7, padx=(0, 10))
        cb = ttk.Combobox(bar, textvariable=self.filter_var, state="readonly", width=12,
                          values=["Tous", "Perdu", "Trouvé", "Restitué"])
        cb.pack(side="left")
        self.search_var.trace_add("write", lambda *_: self.refresh())
        cb.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        self.button(bar, "Supprimer", self.delete_item, "#ef4444").pack(side="right")
        self.button(bar, "Faire une demande", self.make_claim, COLORS["Restitué"]).pack(side="right", padx=8)
        self.button(bar, "Actualiser", self.reload, "#94a3b8").pack(side="right")

        wrap, self.items_tree = self.make_tree(p)
        wrap.pack(fill="both", expand=True)
        self.items_tree.bind("<Double-1>", lambda e: self.show_details())
        tk.Label(p, text="Double-clic sur une ligne pour voir la description.", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 0))

    def page_declare(self, p):
        self.header(p, "Déclarer un objet", "Enregistrer un objet perdu ou trouvé")
        self.declare_form = DeclareForm(p, on_submit=self.save_item)
        self.declare_form.pack(anchor="nw", fill="x")

    def page_returns(self, p):
        self.header(p, "Restitutions", "Objets rendus à leur propriétaire")
        wrap, self.returns_tree = self.make_tree(p)
        wrap.pack(fill="both", expand=True)

    # ---------- Page Demandes ----------
    def make_table(self, parent, cols, widths):
        wrap = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        for c, w in zip(cols, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w")
        for st, col in CLAIM_COLORS.items():
            tree.tag_configure(st, foreground=col)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return wrap, tree

    def page_claims(self, p):
        self.header(p, "Demandes de récupération", "Suivez vos demandes et répondez à celles reçues sur vos annonces")
        nb = ttk.Notebook(p)
        nb.pack(fill="both", expand=True)
        mine, recv = tk.Frame(nb, bg=BG), tk.Frame(nb, bg=BG)
        nb.add(mine, text="  Mes demandes  ")
        nb.add(recv, text="  Demandes reçues  ")

        bar = tk.Frame(mine, bg=BG)
        bar.pack(fill="x", pady=10)
        self.button(bar, "Supprimer ma demande", self.delete_claim, "#ef4444").pack(side="right")
        wrap, self.sent_tree = self.make_table(mine, ("Objet", "Message", "Date", "Statut"), (200, 380, 100, 100))
        wrap.pack(fill="both", expand=True)

        bar = tk.Frame(recv, bg=BG)
        bar.pack(fill="x", pady=10)
        self.button(bar, "Refuser", lambda: self.answer_claim("Refusée"), "#ef4444").pack(side="right")
        self.button(bar, "Accepter", lambda: self.answer_claim("Acceptée"), COLORS["Restitué"]).pack(side="right", padx=8)
        wrap, self.recv_tree = self.make_table(recv, ("Objet", "Demandeur", "Message", "Date", "Statut"),
                                               (170, 150, 290, 100, 100))
        wrap.pack(fill="both", expand=True)

    def fill_claims(self):
        for tree, rows, with_user in ((self.sent_tree, self.claims_sent, False),
                                      (self.recv_tree, self.claims_recv, True)):
            tree.delete(*tree.get_children())
            for c in rows:
                day = (c["date_restitution"] or "")[:10]
                vals = ((c["nom_objet"], c["demandeur"], c["message"], day, c["statut"]) if with_user
                        else (c["nom_objet"], c["message"], day, c["statut"]))
                tree.insert("", "end", iid=str(c["id_restitution"]), values=vals, tags=(c["statut"],))

    # ---------- Données ----------
    def reload(self):
        """Relit la base (objets + demandes) puis rafraîchit l'affichage."""
        try:
            self.items = [to_ui(r) for r in objects.get_all_objects()]
            self.claims_sent = restitutions.get_restitutions_by_user(self.user["id"])
            self.claims_recv = restitutions.get_restitutions_for_my_objects(self.user["id"])
        except sqlite3.Error as e:
            messagebox.showerror("Base de données", f"Impossible de lire la base :\n{e}")
            return
        self.refresh()
        self.fill_claims()

    def refresh(self):
        """Réaffiche à partir de self.items (filtre recherche + statut), sans requête SQL."""
        counts = {"Total": len(self.items)}
        for st in COLORS:
            counts[st] = sum(1 for i in self.items if i["statut"] == st)
        for k, lbl in self.stat_labels.items():
            lbl.config(text=str(counts[k]))
        self.refresh_home_cards()

        q, f = self.search_var.get().lower().strip(), self.filter_var.get()
        filtered = [i for i in self.items
                    if (f == "Tous" or i["statut"] == f)
                    and (q in i["nom"].lower() or q in i["lieu"].lower() or q in i["cat"].lower()
                         or q in i["desc"].lower())]
        self.fill(self.items_tree, filtered)
        self.fill(self.returns_tree, [i for i in self.items if i["statut"] == "Restitué"])

    # ---------- Actions ----------
    def selected(self):
        """Identifiant (id_object) de la ligne sélectionnée, ou None."""
        sel = self.items_tree.selection()
        if not sel:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord un objet dans la liste.")
            return None
        return int(sel[0])

    def item_by_id(self, id_):
        return next((i for i in self.items if i["id"] == id_), None)

    def show_details(self):
        id_ = self.selected()
        it = self.item_by_id(id_) if id_ is not None else None
        if it:
            messagebox.showinfo(it["nom"], f"Statut : {it['statut']}\nCatégorie : {it['cat']}\n"
                                           f"Lieu : {it['lieu']}\nDate : {it['date']}\n"
                                           f"Déclaré par : {it['declarant']}\n\n"
                                           f"{it['desc'] or 'Pas de description.'}")

    def make_claim(self):
        id_ = self.selected()
        it = self.item_by_id(id_) if id_ is not None else None
        if it is None:
            return
        if it["user_id"] == self.user["id"]:
            return messagebox.showwarning("Demande impossible", "Vous ne pouvez pas réclamer votre propre annonce.")
        if it["statut"] != "Trouvé":
            return messagebox.showwarning("Demande impossible",
                                          "Seuls les objets « Trouvé » non encore restitués peuvent être réclamés.")
        msg = ask_claim_message(self, it["nom"])
        if not msg:
            return
        try:
            restitutions.add_restitution(id_, self.user["id"], msg)
        except ValueError as e:                       # doublon, objet indisponible…
            return messagebox.showwarning("Demande refusée", str(e))
        except sqlite3.Error as e:
            return messagebox.showerror("Base de données", str(e))
        messagebox.showinfo("Succès", "Votre demande a été envoyée. Suivez-la dans « Demandes ».")
        self.reload()

    def delete_item(self):
        id_ = self.selected()
        it = self.item_by_id(id_) if id_ is not None else None
        if it is None:
            return
        if it["user_id"] != self.user["id"]:
            return messagebox.showwarning("Refusé", "Vous ne pouvez supprimer que vos propres annonces.")
        if messagebox.askyesno("Confirmation", "Supprimer cette annonce (et ses demandes) ?"):
            try:
                objects.delete_object(self.user["id"], id_)
            except sqlite3.Error as e:
                return messagebox.showerror("Base de données", str(e))
            self.reload()

    def save_item(self, data):
        """Appelé par DeclareForm. Renvoie True si l'annonce est enregistrée."""
        try:
            objects.add_object(self.user["id"], data["nom"], data["desc"], data["cat"],
                               data["lieu"], data["date"], data["type"])
        except ValueError as e:
            messagebox.showwarning("Erreur de saisie", str(e))
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Base de données", str(e))
            return False
        messagebox.showinfo("Succès", "Annonce enregistrée avec succès.")
        self.goto_search()
        return True

    def selected_claim(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord une demande dans la liste.")
            return None
        return int(sel[0])

    def answer_claim(self, statut):
        id_ = self.selected_claim(self.recv_tree)
        if id_ is None:
            return
        verbe = "accepter" if statut == "Acceptée" else "refuser"
        if not messagebox.askyesno("Confirmation", f"Voulez-vous {verbe} cette demande ?"):
            return
        try:
            ok = restitutions.update_restitution_status(self.user["id"], id_, statut)
        except (ValueError, sqlite3.Error) as e:
            return messagebox.showerror("Erreur", str(e))
        if ok:
            if statut == "Acceptée":
                # l'objet est rendu : on refuse automatiquement les autres demandes en attente
                id_obj = next(c["id_object"] for c in self.claims_recv if c["id_restitution"] == id_)
                for c in self.claims_recv:
                    if c["id_object"] == id_obj and c["id_restitution"] != id_ and c["statut"] == "En attente":
                        restitutions.update_restitution_status(self.user["id"], c["id_restitution"], "Refusée")
            messagebox.showinfo("Succès", "Demande acceptée : l'objet est marqué « Restitué »."
                                if statut == "Acceptée" else "Demande refusée.")
        else:
            messagebox.showwarning("Action impossible", "Cette demande est déjà traitée "
                                                         "ou l'objet n'est plus disponible.")
        self.reload()

    def delete_claim(self):
        id_ = self.selected_claim(self.sent_tree)
        if id_ is None:
            return
        if messagebox.askyesno("Confirmation", "Supprimer cette demande ?"):
            if not restitutions.delete_restitution(self.user["id"], id_):
                messagebox.showwarning("Action impossible", "Seules vos demandes « En attente » peuvent être supprimées.")
            self.reload()

    def logout(self):
        self.logout_requested = True
        self.destroy()


# ---------- Lancement ----------
def init_db():
    """Crée les tables si elles n'existent pas (à appeler une fois au démarrage)."""
    with get_connection() as c:
        User.create_table(c)
        objects.create_table(c)
        restitutions.create_table(c)


def run():
    init_db()
    while True:
        login = LoginWindow()
        login.mainloop()
        if login.user is None:          # fenêtre fermée sans connexion
            break
        app = App(login.user)
        app.mainloop()
        if not app.logout_requested:    # fermeture normale -> on quitte
            break


if __name__ == "__main__":
    run()
