"""
FindIt - forms.py (Membre 2 : Edouarda)
Thème graphique + formulaires Tkinter :
  - LoginWindow  : connexion / inscription
  - DeclareForm  : formulaire de publication d'une annonce
  - ClaimDialog  : fenêtre pour envoyer une demande de récupération
"""
import re
import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk, messagebox

from database import User

# ---------- Palette ----------
SIDEBAR_BG = "#1e293b"
SIDEBAR_HOVER = "#334155"
ACCENT = "#6366f1"
G1, G2 = "#4338ca", "#9333ea"          # dégradé de la bannière
BG = "#f1f5f9"
CARD = "#ffffff"
TEXT = "#0f172a"
MUTED = "#64748b"
BORDER = "#e2e8f0"
COLORS = {"Perdu": "#ef4444", "Trouvé": "#f59e0b", "Restitué": "#10b981"}
BADGES = {"Perdu": ("#fee2e2", "#b91c1c"), "Trouvé": ("#fef3c7", "#b45309"), "Restitué": ("#d1fae5", "#047857")}
CLAIM_COLORS = {"En attente": "#f59e0b", "Acceptée": "#10b981", "Refusée": "#ef4444"}

FONT = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 10, "bold")
TITLE = ("Segoe UI", 20, "bold")

CATEGORIES = ["Électronique", "Vêtements", "Clés", "Documents", "Livres", "Sac", "Autre"]
ICONS = {"Électronique": "📱", "Vêtements": "🧥", "Clés": "🔑", "Documents": "📄",
         "Livres": "📚", "Sac": "🎒", "Autre": "📦"}
LIEUX = ["Bibliothèque", "Amphi A", "Amphi B", "Cafétéria", "Résidence", "Labo info", "Parking", "Gymnase"]

SB_W = 250
TOPBAR_H = 56

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- Utilitaires ----------
def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, t):
    a, b = hex2rgb(c1), hex2rgb(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def flat_button(parent, text, cmd, color=ACCENT):
    """Bouton plat avec effet de survol."""
    b = tk.Label(parent, text=text, bg=color, fg="white", font=FONT_B,
                 padx=18, pady=9, cursor="hand2")
    b.bind("<Button-1>", lambda e: cmd())
    b.bind("<Enter>", lambda e: b.config(bg=mix(color, "#000000", 0.15)))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


def labeled(parent, label, factory, bg=CARD):
    """Label + widget créé par factory(frame). Retourne (frame, widget)."""
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=label, bg=bg, fg=MUTED, font=FONT).pack(anchor="w")
    w = factory(f)
    w.pack(fill="x", ipady=5, pady=(4, 0))
    return f, w


def plain_entry(var, show=None):
    return lambda f: tk.Entry(f, textvariable=var, font=FONT, relief="flat", show=show or "",
                              highlightbackground="#cbd5e1", highlightthickness=1)


# ======================================================================
#  Connexion / Inscription
# ======================================================================
class LoginWindow(tk.Tk):
    """Fenêtre de connexion et d'inscription.
    Après fermeture, `self.user` vaut le dict {"id", "full_name", "email"}
    de l'utilisateur connecté, ou None si la fenêtre a été fermée sans connexion."""
    W, H = 460, 640

    def __init__(self):
        super().__init__()
        self.user = None
        self.title("FindIt - Connexion")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.W) // 2
        y = max((self.winfo_screenheight() - self.H) // 2 - 20, 0)
        self.geometry(f"{self.W}x{self.H}+{x}+{y}")

        # Bannière dégradée
        banner = tk.Canvas(self, height=130, width=self.W, highlightthickness=0, bd=0)
        banner.pack(fill="x")
        n = 60
        for i in range(n):
            banner.create_rectangle(i * self.W / n, 0, (i + 1) * self.W / n + 1, 130,
                                    fill=mix(G1, G2, i / (n - 1)), outline="")
        banner.create_text(self.W / 2, 42, text="🎓", font=("Segoe UI Emoji", 28))
        banner.create_text(self.W / 2, 85, text="Campus Lost & Found", fill="white",
                           font=("Segoe UI", 17, "bold"))
        banner.create_text(self.W / 2, 110, text="Objets perdus & trouvés sur le campus",
                           fill="#e0e7ff", font=FONT)

        card = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=30, pady=22)

        # Onglets Connexion / Inscription
        tabs = tk.Frame(card, bg=CARD)
        tabs.pack(fill="x")
        self.tabs = {}
        for i, name in enumerate(("Connexion", "Inscription")):
            tabs.columnconfigure(i, weight=1, uniform="tab")
            f = tk.Frame(tabs, bg=CARD, cursor="hand2")
            f.grid(row=0, column=i, sticky="ew")
            lbl = tk.Label(f, text=name, bg=CARD, fg=MUTED, font=FONT_B, pady=12)
            lbl.pack(fill="x")
            ul = tk.Frame(f, bg=BORDER, height=3)
            ul.pack(fill="x")
            for w in (f, lbl):
                w.bind("<Button-1>", lambda e, n=name: self.show_tab(n))
            self.tabs[name] = (lbl, ul)

        self.body = tk.Frame(card, bg=CARD)
        self.body.pack(fill="both", expand=True, padx=26, pady=(14, 0))
        self.msg = tk.Label(card, text="", bg=CARD, fg="#b91c1c", font=FONT,
                            wraplength=360, justify="left")
        self.msg.pack(fill="x", padx=26, pady=(0, 16))

        self.f_login = self._build_login()
        self.f_register = self._build_register()
        self.current = None
        self.bind("<Return>", lambda e: self.submit())
        self.show_tab("Connexion")

    # ---------- Construction ----------
    def _build_login(self):
        f = tk.Frame(self.body, bg=CARD)
        self.l_email, self.l_pwd = tk.StringVar(), tk.StringVar()
        labeled(f, "Email", plain_entry(self.l_email))[0].pack(fill="x", pady=6)
        labeled(f, "Mot de passe", plain_entry(self.l_pwd, show="•"))[0].pack(fill="x", pady=6)
        flat_button(f, "Se connecter", self.do_login).pack(fill="x", pady=(14, 0))
        return f

    def _build_register(self):
        f = tk.Frame(self.body, bg=CARD)
        self.r_nom, self.r_email = tk.StringVar(), tk.StringVar()
        self.r_pwd, self.r_pwd2 = tk.StringVar(), tk.StringVar()
        labeled(f, "Nom complet", plain_entry(self.r_nom))[0].pack(fill="x", pady=4)
        labeled(f, "Email", plain_entry(self.r_email))[0].pack(fill="x", pady=4)
        labeled(f, "Mot de passe (6 caractères min.)", plain_entry(self.r_pwd, show="•"))[0].pack(fill="x", pady=4)
        labeled(f, "Confirmer le mot de passe", plain_entry(self.r_pwd2, show="•"))[0].pack(fill="x", pady=4)
        flat_button(f, "Créer mon compte", self.do_register).pack(fill="x", pady=(12, 0))
        return f

    # ---------- Navigation ----------
    def show_tab(self, name):
        self.current = name
        self.msg.config(text="")
        for n, (lbl, ul) in self.tabs.items():
            lbl.config(fg=ACCENT if n == name else MUTED)
            ul.config(bg=ACCENT if n == name else BORDER)
        self.f_login.pack_forget()
        self.f_register.pack_forget()
        (self.f_login if name == "Connexion" else self.f_register).pack(fill="x")

    def submit(self):
        (self.do_login if self.current == "Connexion" else self.do_register)()

    def error(self, text):
        self.msg.config(text=text, fg="#b91c1c")

    def info(self, text):
        self.msg.config(text=text, fg=MUTED)
        self.update_idletasks()

    # ---------- Actions ----------
    def do_login(self):
        email, pwd = self.l_email.get().strip(), self.l_pwd.get()
        if not email or not pwd:
            return self.error("Entrez votre email et votre mot de passe.")
        self.info("Connexion en cours…")
        try:
            user = User.login(email, pwd)
        except sqlite3.Error as e:
            return self.error(f"Erreur de base de données : {e}")
        if user is None:
            return self.error("Email ou mot de passe incorrect.")
        self.user = user
        self.destroy()

    def do_register(self):
        nom, email = self.r_nom.get().strip(), self.r_email.get().strip()
        pwd, pwd2 = self.r_pwd.get(), self.r_pwd2.get()
        if not nom or not email or not pwd:
            return self.error("Tous les champs sont obligatoires.")
        if not EMAIL_RE.match(email):
            return self.error("Adresse email invalide.")
        if len(pwd) < 6:
            return self.error("Le mot de passe doit contenir au moins 6 caractères.")
        if pwd != pwd2:
            return self.error("Les deux mots de passe ne correspondent pas.")
        self.info("Création du compte…")
        try:
            User.add_user(nom, email, pwd)
            user = User.login(email, pwd)
        except ValueError as e:                 # ex. email déjà utilisé
            return self.error(str(e))
        except sqlite3.Error as e:
            return self.error(f"Erreur de base de données : {e}")
        self.user = user
        self.destroy()


# ======================================================================
#  Formulaire de publication d'une annonce
# ======================================================================
class DeclareForm(tk.Frame):
    """Formulaire de déclaration. `on_submit(data)` reçoit un dict
    {nom, desc, cat, lieu, date, type} et doit renvoyer True si l'enregistrement
    a réussi (le formulaire est alors réinitialisé)."""

    def __init__(self, parent, on_submit):
        super().__init__(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        self.on_submit = on_submit
        inner = tk.Frame(self, bg=CARD)
        inner.pack(padx=28, pady=24, fill="x")
        inner.columnconfigure((0, 1), weight=1)

        self.v_nom = tk.StringVar()
        self.v_cat = tk.StringVar(value=CATEGORIES[0])
        self.v_type = tk.StringVar(value="Perdu")
        self.v_lieu = tk.StringVar(value=LIEUX[0])
        self.v_date = tk.StringVar(value=date.today().isoformat())

        def combo(var, vals, state="readonly"):
            return lambda f: ttk.Combobox(f, textvariable=var, values=vals, state=state)

        grid = [
            ("Nom de l'objet *", plain_entry(self.v_nom), 0, 0),
            ("Catégorie", combo(self.v_cat, CATEGORIES), 0, 1),
            ("Type d'annonce", combo(self.v_type, ["Perdu", "Trouvé"]), 1, 0),
            ("Lieu (liste ou saisie libre)", combo(self.v_lieu, LIEUX, state="normal"), 1, 1),
            ("Date (AAAA-MM-JJ)", plain_entry(self.v_date), 2, 0),
        ]
        for label, factory, r, c in grid:
            labeled(inner, label, factory)[0].grid(row=r, column=c, sticky="ew", padx=8, pady=8)

        f = tk.Frame(inner, bg=CARD)
        f.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        tk.Label(f, text="Description (signes distinctifs, couleur, marque…)", bg=CARD,
                 fg=MUTED, font=FONT).pack(anchor="w")
        self.t_desc = tk.Text(f, height=4, font=FONT, relief="flat", wrap="word",
                              highlightbackground="#cbd5e1", highlightthickness=1)
        self.t_desc.pack(fill="x", pady=(4, 0))

        btns = tk.Frame(inner, bg=CARD)
        btns.grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0), padx=8)
        flat_button(btns, "Réinitialiser", self.reset, "#94a3b8").pack(side="left", padx=(0, 8))
        flat_button(btns, "Enregistrer", self.submit).pack(side="left")

    def submit(self):
        data = {"nom": self.v_nom.get().strip(),
                "desc": self.t_desc.get("1.0", "end").strip(),
                "cat": self.v_cat.get(), "lieu": self.v_lieu.get().strip(),
                "date": self.v_date.get().strip(), "type": self.v_type.get()}
        if not data["nom"]:
            return messagebox.showwarning("Champ requis", "Le nom de l'objet est obligatoire.")
        if not data["lieu"]:
            return messagebox.showwarning("Champ requis", "Le lieu est obligatoire.")
        try:
            d = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return messagebox.showwarning("Date invalide",
                                          "Utilisez le format AAAA-MM-JJ (exemple : 2026-10-26).")
        if d > date.today():
            return messagebox.showwarning("Date invalide", "La date ne peut pas être dans le futur.")
        if self.on_submit(data):
            self.reset()

    def reset(self):
        self.v_nom.set("")
        self.v_cat.set(CATEGORIES[0])
        self.v_type.set("Perdu")
        self.v_lieu.set(LIEUX[0])
        self.v_date.set(date.today().isoformat())
        self.t_desc.delete("1.0", "end")


# ======================================================================
#  Fenêtre « Faire une demande de récupération »
# ======================================================================
class ClaimDialog(tk.Toplevel):
    """Fenêtre modale. Utiliser ask_claim_message() qui renvoie le message ou None."""

    def __init__(self, parent, object_name):
        super().__init__(parent)
        self.result = None
        self.title("Faire une demande")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        box = tk.Frame(self, bg=CARD)
        box.pack(padx=26, pady=22)
        tk.Label(box, text="Demande de récupération", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(box, text=f"Objet : {object_name}", bg=CARD, fg=MUTED, font=FONT).pack(anchor="w", pady=(2, 12))
        tk.Label(box, text="Message au déclarant (décrivez l'objet pour prouver qu'il est à vous) *",
                 bg=CARD, fg=MUTED, font=FONT).pack(anchor="w")
        self.txt = tk.Text(box, width=52, height=6, font=FONT, relief="flat", wrap="word",
                           highlightbackground="#cbd5e1", highlightthickness=1)
        self.txt.pack(pady=(4, 14))
        row = tk.Frame(box, bg=CARD)
        row.pack(anchor="e")
        flat_button(row, "Annuler", self.destroy, "#94a3b8").pack(side="left", padx=(0, 8))
        flat_button(row, "Envoyer", self.send).pack(side="left")

        self.grab_set()
        self.txt.focus_set()

    def send(self):
        msg = self.txt.get("1.0", "end").strip()
        if not msg:
            return messagebox.showwarning("Champ requis", "Le message ne peut pas être vide.", parent=self)
        self.result = msg
        self.destroy()


def ask_claim_message(parent, object_name):
    dlg = ClaimDialog(parent, object_name)
    dlg.wait_window()
    return dlg.result
