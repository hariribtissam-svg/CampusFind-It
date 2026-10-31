"""
forms.py - Formulaires de l'application FindIt (partie d'Edouarda)

Contient :
- LoginWindow : fenêtre de connexion et d'inscription
- DeclareForm : formulaire pour déclarer un objet perdu ou trouvé
- ClaimDialog : petite fenêtre pour écrire le message d'une demande
"""
import re
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from database import User

CATEGORIES = ["Électronique", "Vêtements", "Clés", "Documents", "Livres", "Sac", "Autre"]
LIEUX = ["Bibliothèque", "Amphi A", "Amphi B", "Cafétéria", "Résidence", "Labo info", "Parking", "Gymnase"]


class LoginWindow(tk.Tk):
    """Fenêtre de connexion / inscription.
    Après sa fermeture, self.user contient l'utilisateur connecté (ou None)."""

    def __init__(self):
        super().__init__()
        self.user = None
        self.title("FindIt - Connexion")
        self.geometry("380x430")

        tk.Label(self, text="FindIt", font=("Arial", 22, "bold")).pack(pady=(15, 0))
        tk.Label(self, text="Objets perdus et trouvés sur le campus").pack()

        # Deux onglets : Connexion et Inscription
        onglets = ttk.Notebook(self)
        onglets.pack(fill="both", expand=True, padx=15, pady=15)
        page_connexion = tk.Frame(onglets)
        page_inscription = tk.Frame(onglets)
        onglets.add(page_connexion, text="Connexion")
        onglets.add(page_inscription, text="Inscription")

        # Onglet connexion
        self.l_email = tk.StringVar()
        self.l_mdp = tk.StringVar()
        self.ajouter_champ(page_connexion, "Email", self.l_email, 0)
        self.ajouter_champ(page_connexion, "Mot de passe", self.l_mdp, 1, cache=True)
        tk.Button(page_connexion, text="Se connecter", command=self.do_login).grid(
            row=2, column=0, columnspan=2, pady=20)

        # Onglet inscription
        self.r_nom = tk.StringVar()
        self.r_email = tk.StringVar()
        self.r_pwd = tk.StringVar()
        self.r_pwd2 = tk.StringVar()
        self.ajouter_champ(page_inscription, "Nom complet", self.r_nom, 0)
        self.ajouter_champ(page_inscription, "Email", self.r_email, 1)
        self.ajouter_champ(page_inscription, "Mot de passe", self.r_pwd, 2, cache=True)
        self.ajouter_champ(page_inscription, "Confirmer", self.r_pwd2, 3, cache=True)
        tk.Button(page_inscription, text="Créer mon compte", command=self.do_register).grid(
            row=4, column=0, columnspan=2, pady=20)

    def ajouter_champ(self, parent, texte, variable, ligne, cache=False):
        """Ajoute un label et une zone de saisie sur une ligne de la grille."""
        tk.Label(parent, text=texte).grid(row=ligne, column=0, sticky="w", padx=10, pady=8)
        entree = tk.Entry(parent, textvariable=variable, width=25, show="*" if cache else "")
        entree.grid(row=ligne, column=1, padx=10, pady=8)

    def do_login(self):
        email = self.l_email.get().strip()
        mdp = self.l_mdp.get()
        if email == "" or mdp == "":
            messagebox.showwarning("Connexion", "Entrez votre email et votre mot de passe.")
            return
        user = User.login(email, mdp)          # fonction de la base (Ibtissam)
        if user is None:
            messagebox.showerror("Connexion", "Email ou mot de passe incorrect.")
            return
        self.user = user
        self.destroy()                         # ferme la fenêtre de connexion

    def do_register(self):
        nom = self.r_nom.get().strip()
        email = self.r_email.get().strip()
        mdp = self.r_pwd.get()
        # Vérifications avant d'appeler la base
        if nom == "" or email == "" or mdp == "":
            messagebox.showwarning("Inscription", "Tous les champs sont obligatoires.")
            return
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            messagebox.showwarning("Inscription", "Adresse email invalide.")
            return
        if len(mdp) < 6:
            messagebox.showwarning("Inscription", "Le mot de passe doit contenir au moins 6 caractères.")
            return
        if mdp != self.r_pwd2.get():
            messagebox.showwarning("Inscription", "Les deux mots de passe sont différents.")
            return
        try:
            User.add_user(nom, email, mdp)     # fonction de la base (Ibtissam)
            self.user = User.login(email, mdp)
        except ValueError as erreur:           # ex : email déjà utilisé
            messagebox.showerror("Inscription", str(erreur))
            return
        except sqlite3.Error as erreur:
            messagebox.showerror("Base de données", str(erreur))
            return
        self.destroy()


class DeclareForm(tk.Frame):
    """Formulaire de déclaration d'un objet.
    on_submit(data) est une fonction donnée par interface.py : elle enregistre
    l'objet dans la base et renvoie True si tout s'est bien passé."""

    def __init__(self, parent, on_submit):
        super().__init__(parent)
        self.on_submit = on_submit

        self.v_nom = tk.StringVar()
        self.v_cat = tk.StringVar(value=CATEGORIES[0])
        self.v_type = tk.StringVar(value="Perdu")
        self.v_lieu = tk.StringVar(value=LIEUX[0])
        self.v_date = tk.StringVar(value=date.today().isoformat())

        tk.Label(self, text="Nom de l'objet *").grid(row=0, column=0, sticky="w", pady=6)
        tk.Entry(self, textvariable=self.v_nom, width=40).grid(row=0, column=1, sticky="w")

        tk.Label(self, text="Catégorie").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Combobox(self, textvariable=self.v_cat, values=CATEGORIES, state="readonly",
                     width=37).grid(row=1, column=1, sticky="w")

        tk.Label(self, text="Type d'annonce").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Combobox(self, textvariable=self.v_type, values=["Perdu", "Trouvé"], state="readonly",
                     width=37).grid(row=2, column=1, sticky="w")

        tk.Label(self, text="Lieu *").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Combobox(self, textvariable=self.v_lieu, values=LIEUX, width=37).grid(
            row=3, column=1, sticky="w")

        tk.Label(self, text="Date (AAAA-MM-JJ)").grid(row=4, column=0, sticky="w", pady=6)
        tk.Entry(self, textvariable=self.v_date, width=40).grid(row=4, column=1, sticky="w")

        tk.Label(self, text="Description").grid(row=5, column=0, sticky="nw", pady=6)
        self.t_desc = tk.Text(self, width=40, height=5)
        self.t_desc.grid(row=5, column=1, sticky="w")

        boutons = tk.Frame(self)
        boutons.grid(row=6, column=1, sticky="w", pady=15)
        tk.Button(boutons, text="Enregistrer", command=self.submit).pack(side="left", padx=(0, 8))
        tk.Button(boutons, text="Effacer", command=self.reset).pack(side="left")

    def submit(self):
        """Vérifie les champs, puis envoie les données à interface.py."""
        data = {"nom": self.v_nom.get().strip(),
                "desc": self.t_desc.get("1.0", "end").strip(),
                "cat": self.v_cat.get(),
                "lieu": self.v_lieu.get().strip(),
                "date": self.v_date.get().strip(),
                "type": self.v_type.get()}
        if data["nom"] == "":
            messagebox.showwarning("Champ requis", "Le nom de l'objet est obligatoire.")
            return
        if data["lieu"] == "":
            messagebox.showwarning("Champ requis", "Le lieu est obligatoire.")
            return
        try:
            jour = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("Date invalide", "Format attendu : AAAA-MM-JJ (ex : 2026-10-26).")
            return
        if jour > date.today():
            messagebox.showwarning("Date invalide", "La date ne peut pas être dans le futur.")
            return
        if self.on_submit(data):
            self.reset()

    def reset(self):
        """Remet le formulaire à zéro."""
        self.v_nom.set("")
        self.v_cat.set(CATEGORIES[0])
        self.v_type.set("Perdu")
        self.v_lieu.set(LIEUX[0])
        self.v_date.set(date.today().isoformat())
        self.t_desc.delete("1.0", "end")


class ClaimDialog(tk.Toplevel):
    """Petite fenêtre pour écrire le message d'une demande de récupération."""

    def __init__(self, parent, nom_objet):
        super().__init__(parent)
        self.result = None
        self.title("Faire une demande")
        tk.Label(self, text=f"Objet : {nom_objet}", font=("Arial", 11, "bold")).pack(padx=15, pady=(15, 5))
        tk.Label(self, text="Décrivez l'objet pour prouver qu'il est à vous :").pack(padx=15)
        self.txt = tk.Text(self, width=45, height=6)
        self.txt.pack(padx=15, pady=10)
        boutons = tk.Frame(self)
        boutons.pack(pady=(0, 15))
        tk.Button(boutons, text="Envoyer", command=self.send).pack(side="left", padx=5)
        tk.Button(boutons, text="Annuler", command=self.destroy).pack(side="left", padx=5)
        self.grab_set()                        # bloque la fenêtre principale tant qu'elle est ouverte

    def send(self):
        message = self.txt.get("1.0", "end").strip()
        if message == "":
            messagebox.showwarning("Champ requis", "Le message ne peut pas être vide.", parent=self)
            return
        self.result = message
        self.destroy()


def ask_claim_message(parent, nom_objet):
    """Ouvre la fenêtre et renvoie le message écrit (ou None si annulé)."""
    fenetre = ClaimDialog(parent, nom_objet)
    fenetre.wait_window()
    return fenetre.result
