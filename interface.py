"""
interface.py - Interface graphique de FindIt (partie d'Edouarda)

L'interface ne contient aucune requête SQL : elle appelle les fonctions
de la base de données écrites par Ibtissam (dossier database/).
Lancer : python main.py   (ou python interface.py pour tester seule)
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from database import User, objects, restitutions
from database.connection import get_connection
from forms import LoginWindow, DeclareForm, ask_claim_message

# Couleur du texte selon le statut (objets et demandes)
COULEURS = {"Perdu": "red", "Trouvé": "orange", "Restitué": "green",
            "En attente": "orange", "Acceptée": "green", "Refusée": "red"}


def to_ui(r):
    """Transforme une ligne de la base en dictionnaire simple pour l'interface.
    Le statut affiché est « Restitué » si l'objet est rendu, sinon Perdu ou Trouvé."""
    if r["status"] == "Restitué":
        statut = "Restitué"
    else:
        statut = r["type_declaration"]
    return {"id": r["id_object"], "nom": r["name_object"], "cat": r["category"],
            "lieu": r["location"], "date": r["date_declaration"], "statut": statut,
            "declarant": r["declarant_name"], "user_id": r["user_id"],
            "desc": r["description"] or ""}


def creer_tableau(parent, colonnes, largeurs):
    """Crée un tableau (Treeview) avec une barre de défilement."""
    cadre = tk.Frame(parent)
    tableau = ttk.Treeview(cadre, columns=colonnes, show="headings", selectmode="browse")
    barre = ttk.Scrollbar(cadre, orient="vertical", command=tableau.yview)
    tableau.configure(yscrollcommand=barre.set)
    for nom, largeur in zip(colonnes, largeurs):
        tableau.heading(nom, text=nom)
        tableau.column(nom, width=largeur)
    for statut, couleur in COULEURS.items():
        tableau.tag_configure(statut, foreground=couleur)
    tableau.pack(side="left", fill="both", expand=True)
    barre.pack(side="right", fill="y")
    return cadre, tableau


class App(tk.Tk):
    """Fenêtre principale, ouverte une fois l'utilisateur connecté."""

    def __init__(self, user):
        super().__init__()
        self.user = user                      # dictionnaire : id, full_name, email
        self.logout_requested = False
        self.title(f"FindIt - {user['full_name']}")
        self.geometry("1000x620")

        self.items = []                       # objets lus dans la base
        self.claims_sent = []                 # mes demandes
        self.claims_recv = []                 # demandes reçues sur mes annonces
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="Tous")

        # Menu du haut
        menu = tk.Frame(self, bg="#dddddd")
        menu.pack(fill="x")
        for nom in ["Accueil", "Objets", "Déclarer", "Demandes", "Restitutions"]:
            tk.Button(menu, text=nom, width=10,
                      command=lambda n=nom: self.show_page(n)).pack(side="left", padx=3, pady=5)
        tk.Button(menu, text="Déconnexion", command=self.logout).pack(side="right", padx=8)
        tk.Label(menu, text=f"Connecté : {user['full_name']}", bg="#dddddd").pack(side="right", padx=10)

        # Zone où s'affichent les pages
        zone = tk.Frame(self)
        zone.pack(fill="both", expand=True, padx=15, pady=10)
        self.pages = {}
        for nom, construire in [("Accueil", self.page_home), ("Objets", self.page_items),
                                ("Déclarer", self.page_declare), ("Demandes", self.page_claims),
                                ("Restitutions", self.page_returns)]:
            page = tk.Frame(zone)
            construire(page)
            self.pages[nom] = page

        self.show_page("Accueil")

    # ---------- Navigation ----------
    def show_page(self, nom):
        """Affiche une seule page et recharge les données de la base."""
        for page in self.pages.values():
            page.pack_forget()
        self.pages[nom].pack(fill="both", expand=True)
        self.reload()

    def goto_search(self, texte="", statut="Tous"):
        """Va sur la page Objets avec une recherche pré-remplie."""
        self.search_var.set(texte)
        self.filter_var.set(statut)
        self.show_page("Objets")

    def titre(self, parent, texte):
        tk.Label(parent, text=texte, font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 10))

    # ---------- Les 5 pages ----------
    def page_home(self, p):
        self.titre(p, "Campus Lost & Found")
        tk.Label(p, text="Déclarez, recherchez et récupérez vos objets perdus ou trouvés.").pack(anchor="w")

        ligne = tk.Frame(p)
        ligne.pack(anchor="w", pady=12)
        self.home_search = tk.StringVar()
        tk.Entry(ligne, textvariable=self.home_search, width=40).pack(side="left", padx=(0, 8))
        tk.Button(ligne, text="Rechercher",
                  command=lambda: self.goto_search(self.home_search.get().strip())).pack(side="left")

        # Statistiques
        stats = tk.LabelFrame(p, text="Statistiques")
        stats.pack(fill="x", pady=10)
        self.stat_labels = {}
        for cle, texte in [("Total", "Total déclarés"), ("Perdu", "Perdus"),
                           ("Trouvé", "Trouvés"), ("Restitué", "Restitués")]:
            case = tk.Frame(stats)
            case.pack(side="left", expand=True, pady=10)
            self.stat_labels[cle] = tk.Label(case, text="0", font=("Arial", 24, "bold"))
            self.stat_labels[cle].pack()
            tk.Label(case, text=texte).pack()

        # Derniers objets signalés
        tk.Label(p, text="Derniers objets signalés", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 4))
        cadre, self.recent_tree = creer_tableau(
            p, ("Objet", "Catégorie", "Lieu", "Date", "Statut"), (260, 130, 140, 110, 100))
        self.recent_tree.configure(height=6)
        cadre.pack(fill="x")

    def page_items(self, p):
        self.titre(p, "Objets")
        barre = tk.Frame(p)
        barre.pack(fill="x", pady=(0, 10))
        tk.Entry(barre, textvariable=self.search_var, width=30).pack(side="left", padx=(0, 8))
        filtre = ttk.Combobox(barre, textvariable=self.filter_var, state="readonly", width=10,
                              values=["Tous", "Perdu", "Trouvé", "Restitué"])
        filtre.pack(side="left")
        tk.Button(barre, text="Supprimer", command=self.delete_item).pack(side="right")
        tk.Button(barre, text="Faire une demande", command=self.make_claim).pack(side="right", padx=8)
        tk.Button(barre, text="Actualiser", command=self.reload).pack(side="right")

        # La recherche se met à jour à chaque lettre tapée
        self.search_var.trace_add("write", lambda *args: self.refresh())
        filtre.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        cadre, self.items_tree = creer_tableau(
            p, ("Objet", "Catégorie", "Lieu", "Date", "Statut"), (260, 130, 140, 110, 100))
        cadre.pack(fill="both", expand=True)
        self.items_tree.bind("<Double-1>", lambda event: self.show_details())
        tk.Label(p, text="Double-clic sur une ligne pour voir la description.").pack(anchor="w", pady=4)

    def page_declare(self, p):
        self.titre(p, "Déclarer un objet")
        self.declare_form = DeclareForm(p, on_submit=self.save_item)
        self.declare_form.pack(anchor="w")

    def page_claims(self, p):
        self.titre(p, "Demandes de récupération")
        onglets = ttk.Notebook(p)
        onglets.pack(fill="both", expand=True)
        mes_demandes = tk.Frame(onglets)
        recues = tk.Frame(onglets)
        onglets.add(mes_demandes, text="Mes demandes")
        onglets.add(recues, text="Demandes reçues")

        # Onglet 1 : les demandes que j'ai envoyées
        barre = tk.Frame(mes_demandes)
        barre.pack(fill="x", pady=8)
        tk.Button(barre, text="Supprimer ma demande", command=self.delete_claim).pack(side="right")
        cadre, self.sent_tree = creer_tableau(
            mes_demandes, ("Objet", "Message", "Date", "Statut"), (200, 380, 100, 100))
        cadre.pack(fill="both", expand=True)

        # Onglet 2 : les demandes reçues sur mes annonces
        barre = tk.Frame(recues)
        barre.pack(fill="x", pady=8)
        tk.Button(barre, text="Refuser", command=lambda: self.answer_claim("Refusée")).pack(side="right")
        tk.Button(barre, text="Accepter", command=lambda: self.answer_claim("Acceptée")).pack(side="right", padx=8)
        cadre, self.recv_tree = creer_tableau(
            recues, ("Objet", "Demandeur", "Message", "Date", "Statut"), (170, 150, 290, 100, 100))
        cadre.pack(fill="both", expand=True)

    def page_returns(self, p):
        self.titre(p, "Restitutions")
        tk.Label(p, text="Objets déjà rendus à leur propriétaire.").pack(anchor="w", pady=(0, 8))
        cadre, self.returns_tree = creer_tableau(
            p, ("Objet", "Catégorie", "Lieu", "Date", "Statut"), (260, 130, 140, 110, 100))
        cadre.pack(fill="both", expand=True)

    # ---------- Lecture de la base et affichage ----------
    def reload(self):
        """Relit la base de données, puis réaffiche."""
        try:
            self.items = [to_ui(r) for r in objects.get_all_objects()]
            self.claims_sent = restitutions.get_restitutions_by_user(self.user["id"])
            self.claims_recv = restitutions.get_restitutions_for_my_objects(self.user["id"])
        except sqlite3.Error as erreur:
            messagebox.showerror("Base de données", f"Impossible de lire la base :\n{erreur}")
            return
        self.refresh()
        self.fill_claims()

    def fill(self, tableau, liste):
        """Remplit un tableau d'objets. L'identifiant de la ligne (iid) est l'id de la base."""
        tableau.delete(*tableau.get_children())
        for o in liste:
            tableau.insert("", "end", iid=str(o["id"]),
                           values=(o["nom"], o["cat"], o["lieu"], o["date"], o["statut"]),
                           tags=(o["statut"],))

    def refresh(self):
        """Réaffiche à partir de self.items (sans interroger la base)."""
        # Statistiques de l'accueil
        self.stat_labels["Total"].config(text=str(len(self.items)))
        for statut in ["Perdu", "Trouvé", "Restitué"]:
            nombre = len([o for o in self.items if o["statut"] == statut])
            self.stat_labels[statut].config(text=str(nombre))

        # Cinq derniers objets
        recents = sorted(self.items, key=lambda o: o["date"], reverse=True)[:5]
        self.fill(self.recent_tree, recents)

        # Page Objets : filtre par recherche et par statut
        texte = self.search_var.get().lower().strip()
        statut = self.filter_var.get()
        resultat = []
        for o in self.items:
            if statut != "Tous" and o["statut"] != statut:
                continue
            if texte in o["nom"].lower() or texte in o["lieu"].lower() \
                    or texte in o["cat"].lower() or texte in o["desc"].lower():
                resultat.append(o)
        self.fill(self.items_tree, resultat)

        # Page Restitutions
        self.fill(self.returns_tree, [o for o in self.items if o["statut"] == "Restitué"])

    def fill_claims(self):
        """Remplit les deux tableaux de la page Demandes."""
        self.sent_tree.delete(*self.sent_tree.get_children())
        for c in self.claims_sent:
            jour = (c["date_restitution"] or "")[:10]
            self.sent_tree.insert("", "end", iid=str(c["id_restitution"]),
                                  values=(c["nom_objet"], c["message"], jour, c["statut"]),
                                  tags=(c["statut"],))
        self.recv_tree.delete(*self.recv_tree.get_children())
        for c in self.claims_recv:
            jour = (c["date_restitution"] or "")[:10]
            self.recv_tree.insert("", "end", iid=str(c["id_restitution"]),
                                  values=(c["nom_objet"], c["demandeur"], c["message"], jour, c["statut"]),
                                  tags=(c["statut"],))

    # ---------- Actions de l'utilisateur ----------
    def selected(self):
        """Renvoie l'id de l'objet sélectionné dans la liste (ou None)."""
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord un objet dans la liste.")
            return None
        return int(selection[0])

    def item_by_id(self, id_objet):
        for o in self.items:
            if o["id"] == id_objet:
                return o
        return None

    def show_details(self):
        id_objet = self.selected()
        if id_objet is None:
            return
        o = self.item_by_id(id_objet)
        messagebox.showinfo(o["nom"],
                            f"Statut : {o['statut']}\nCatégorie : {o['cat']}\n"
                            f"Lieu : {o['lieu']}\nDate : {o['date']}\n"
                            f"Déclaré par : {o['declarant']}\n\n"
                            f"{o['desc'] or 'Pas de description.'}")

    def save_item(self, data):
        """Appelée par le formulaire : enregistre l'objet dans la base."""
        try:
            objects.add_object(self.user["id"], data["nom"], data["desc"], data["cat"],
                               data["lieu"], data["date"], data["type"])
        except ValueError as erreur:
            messagebox.showwarning("Erreur de saisie", str(erreur))
            return False
        except sqlite3.Error as erreur:
            messagebox.showerror("Base de données", str(erreur))
            return False
        messagebox.showinfo("Succès", "Annonce enregistrée avec succès.")
        self.goto_search()
        return True

    def delete_item(self):
        id_objet = self.selected()
        if id_objet is None:
            return
        o = self.item_by_id(id_objet)
        if o["user_id"] != self.user["id"]:
            messagebox.showwarning("Refusé", "Vous ne pouvez supprimer que vos propres annonces.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer cette annonce (et ses demandes) ?"):
            objects.delete_object(self.user["id"], id_objet)
            self.reload()

    def make_claim(self):
        id_objet = self.selected()
        if id_objet is None:
            return
        o = self.item_by_id(id_objet)
        if o["user_id"] == self.user["id"]:
            messagebox.showwarning("Demande impossible", "Vous ne pouvez pas réclamer votre propre annonce.")
            return
        if o["statut"] != "Trouvé":
            messagebox.showwarning("Demande impossible",
                                   "Seuls les objets « Trouvé » non restitués peuvent être réclamés.")
            return
        message = ask_claim_message(self, o["nom"])
        if message is None:                   # l'utilisateur a annulé
            return
        try:
            restitutions.add_restitution(id_objet, self.user["id"], message)
        except ValueError as erreur:          # ex : demande déjà faite
            messagebox.showwarning("Demande refusée", str(erreur))
            return
        messagebox.showinfo("Succès", "Votre demande a été envoyée. Suivez-la dans « Demandes ».")
        self.reload()

    def selected_claim(self, tableau):
        selection = tableau.selection()
        if not selection:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord une demande dans la liste.")
            return None
        return int(selection[0])

    def answer_claim(self, statut):
        """Accepter ou refuser une demande reçue (statut = 'Acceptée' ou 'Refusée')."""
        id_demande = self.selected_claim(self.recv_tree)
        if id_demande is None:
            return
        if not messagebox.askyesno("Confirmation", "Confirmer votre réponse à cette demande ?"):
            return
        ok = restitutions.update_restitution_status(self.user["id"], id_demande, statut)
        if not ok:
            messagebox.showwarning("Action impossible",
                                   "Cette demande est déjà traitée ou l'objet n'est plus disponible.")
        elif statut == "Acceptée":
            # L'objet est rendu : on refuse les autres demandes en attente sur le même objet
            id_objet = None
            for c in self.claims_recv:
                if c["id_restitution"] == id_demande:
                    id_objet = c["id_object"]
            for c in self.claims_recv:
                if c["id_object"] == id_objet and c["id_restitution"] != id_demande \
                        and c["statut"] == "En attente":
                    restitutions.update_restitution_status(self.user["id"], c["id_restitution"], "Refusée")
            messagebox.showinfo("Succès", "Demande acceptée : l'objet est marqué « Restitué ».")
        else:
            messagebox.showinfo("Succès", "Demande refusée.")
        self.reload()

    def delete_claim(self):
        id_demande = self.selected_claim(self.sent_tree)
        if id_demande is None:
            return
        if messagebox.askyesno("Confirmation", "Supprimer cette demande ?"):
            if not restitutions.delete_restitution(self.user["id"], id_demande):
                messagebox.showwarning("Action impossible",
                                       "Seules les demandes « En attente » peuvent être supprimées.")
            self.reload()

    def logout(self):
        self.logout_requested = True
        self.destroy()


# ---------- Lancement du programme ----------
def init_db():
    """Crée les 3 tables si elles n'existent pas encore."""
    with get_connection() as c:
        User.create_table(c)
        objects.create_table(c)
        restitutions.create_table(c)


def run():
    init_db()
    while True:
        fenetre_connexion = LoginWindow()
        fenetre_connexion.mainloop()
        if fenetre_connexion.user is None:     # fenêtre fermée sans connexion
            break
        app = App(fenetre_connexion.user)
        app.mainloop()
        if not app.logout_requested:           # fenêtre fermée normalement : on quitte
            break


if __name__ == "__main__":
    run()
