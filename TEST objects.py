
import secrets

from database.connection import get_connection

from database.User import (
    create_table as create_users_table,
    add_user,
    get_user_by_email
)

from database.objects import (
    create_table as create_objects_table,
    add_object,
    get_object_by_id,
    get_objects_by_user,
    get_all_objects,
    update_object,
    delete_object
)

from database.restitutions import (
    create_table as create_restitutions_table,
    add_restitution,
    get_all_restitutions,
    get_restitutions_by_user,
    get_restitutions_for_my_objects,
    update_restitution_message,
    update_restitution_status,
    delete_restitution
)


# ==================================================
# TEST 1 : CREATION DES TROIS TABLES
# ==================================================

with get_connection() as connection:
    create_users_table(connection)
    create_objects_table(connection)
    create_restitutions_table(connection)

print("\nTEST 1 : les trois tables sont créées.")


# ==================================================
# FONCTION UTILITAIRE : REUTILISER UN UTILISATEUR
# ==================================================

def get_or_create_user(full_name, email, password):
    utilisateur = get_user_by_email(email)

    if utilisateur is not None:
        return utilisateur["id"]

    return add_user(full_name, email, password)


# ==================================================
# TEST 2 : CREER OU RETROUVER AHMED ET SARA
# ==================================================

owner_id = get_or_create_user(
    "Ahmed Propriétaire",
    "ahmed.owner2@example.com",
    "Ahmed123!"
)

claimant_id = get_or_create_user(
    "Sara Demandeuse",
    "sara.claimant2@example.com",
    "Sara123!"
)

print("\nTEST 2 : utilisateurs Ahmed et Sara")
print("ID propriétaire :", owner_id)
print("ID demandeur :", claimant_id)
print("Utilisateurs différents :", owner_id != claimant_id)


# ==================================================
# TEST 3 : AHMED DECLARE UN OBJET TROUVE
# ==================================================

object_id_test = add_object(
    name_object="Téléphone Samsung",
    description="Téléphone noir avec une coque bleue",
    category="Téléphone",
    type_declaration="Trouvé",
    location="Salle informatique",
    date_declaration="2026-10-26",
    user_id=owner_id
)

print("\nTEST 3 : objet d'Ahmed créé, ID =", object_id_test)


# ==================================================
# TEST 4 : SARA DEMANDE A RECUPERER LE TELEPHONE
# ==================================================

restitution_id_test = add_restitution(
    object_id_test,
    claimant_id,
    "Je pense que ce téléphone m'appartient."
)

print("\nTEST 4 : demande de Sara créée, ID =", restitution_id_test)


# ==================================================
# TEST 5 : CONSULTER LES DEMANDES DE SARA
# ==================================================

demandes_sara = get_restitutions_by_user(claimant_id)

print("\nTEST 5 : demandes de Sara")

for demande in demandes_sara:
    print(
        "ID :", demande["id_restitution"],
        "| Objet :", demande["nom_objet"],
        "| Statut :", demande["statut"]
    )


# ==================================================
# TEST 6 : AHMED CONSULTE LES DEMANDES CONCERNANT SES OBJETS
# ==================================================

demandes_ahmed = get_restitutions_for_my_objects(owner_id)

print("\nTEST 6 : demandes concernant les objets d'Ahmed")

for demande in demandes_ahmed:
    print(
        "ID :", demande["id_restitution"],
        "| Objet :", demande["nom_objet"],
        "| Demandeur :", demande["demandeur"],
        "| Statut :", demande["statut"]
    )


# ==================================================
# TEST 7 : SARA MODIFIE SON MESSAGE
# ==================================================

resultat = update_restitution_message(
    claimant_id,
    restitution_id_test,
    "Je peux fournir une preuve que ce téléphone m'appartient."
)

print("\nTEST 7 : modification du message réussie =", resultat)


# ==================================================
# TEST 8 : AHMED ACCEPTE LA DEMANDE DE SARA
# ==================================================

resultat = update_restitution_status(
    owner_id,
    restitution_id_test,
    "Acceptée"
)

print("\nTEST 8 : acceptation par Ahmed réussie =", resultat)

demandes_sara = get_restitutions_by_user(claimant_id)

for demande in demandes_sara:
    if demande["id_restitution"] == restitution_id_test:
        print("Statut final de la demande :", demande["statut"])

objet = get_object_by_id(object_id_test)

print(
    "Statut final du téléphone :",
    objet["status"] if objet else "Objet introuvable"
)


# ==================================================
# TEST 9 : CREER DEUX UTILISATEURS POUR LES AUTRES TESTS
# ==================================================

suffixe = secrets.token_hex(4)

test_owner_id = add_user(
    "Propriétaire Test",
    f"owner_{suffixe}@example.com",
    "OwnerTest123!"
)

test_claimant_id = add_user(
    "Demandeur Test",
    f"claimant_{suffixe}@example.com",
    "ClaimantTest123!"
)

print("\nTEST 9 : utilisateurs de test créés.")
print("Propriétaire :", test_owner_id)
print("Demandeur :", test_claimant_id)


# ==================================================
# TEST 10 : AJOUTER UN OBJET
# ==================================================

object_id = add_object(
    name_object="Sac à dos",
    description="Sac noir trouvé dans la bibliothèque",
    category="Sac",
    type_declaration="Trouvé",
    location="Bibliothèque",
    date_declaration="2026-10-26",
    user_id=test_owner_id
)

print("\nTEST 10 : objet ajouté, ID =", object_id)


# ==================================================
# TEST 11 : RETROUVER UN OBJET PAR SON IDENTIFIANT
# ==================================================

objet = get_object_by_id(object_id)

print("\nTEST 11 : objet retrouvé =", objet is not None)

if objet:
    print("Nom :", objet["name_object"])
    print("Type :", objet["type_declaration"])
    print("Statut :", objet["status"])


# ==================================================
# TEST 12 : RECUPERER LES OBJETS DU PROPRIETAIRE
# ==================================================

objets_utilisateur = get_objects_by_user(test_owner_id)

print(
    "\nTEST 12 : nombre d'objets du propriétaire =",
    len(objets_utilisateur)
)


# ==================================================
# TEST 13 : RECUPERER TOUS LES OBJETS
# ==================================================

tous_les_objets = get_all_objects()

print("\nTEST 13 : liste de tous les objets")

for objet in tous_les_objets:
    print(
        objet["name_object"],
        "-",
        objet["type_declaration"],
        "-",
        objet["declarant_name"]
    )


# ==================================================
# TEST 14 : MODIFIER UN OBJET
# ==================================================

resultat = update_object(
    test_owner_id,
    object_id,
    "Sac à dos noir modifié",
    "Sac noir trouvé près de la salle informatique",
    "Sac",
    "Salle informatique",
    "2026-10-26",
    "Trouvé"
)

print("\nTEST 14 : modification de l'objet réussie =", resultat)

objet = get_object_by_id(object_id)

if objet:
    print("Nouveau nom :", objet["name_object"])
    print("Nouveau lieu :", objet["location"])


# ==================================================
# TEST 15 : CREER UNE DEMANDE POUR LE SAC
# ==================================================

restitution_id = add_restitution(
    object_id,
    test_claimant_id,
    "Ce sac m'appartient."
)

print("\nTEST 15 : demande créée, ID =", restitution_id)


# ==================================================
# TEST 16 : CONSULTER TOUTES LES DEMANDES
# ==================================================

demandes = get_all_restitutions()

print("\nTEST 16 : toutes les demandes")

for demande in demandes:
    print(
        "ID :", demande["id_restitution"],
        "| Objet :", demande["nom_objet"],
        "| Demandeur :", demande["demandeur"],
        "| Statut :", demande["statut"]
    )


# ==================================================
# TEST 17 : REFUSER LA DEMANDE DU SAC
# ==================================================

resultat = update_restitution_status(
    test_owner_id,
    restitution_id,
    "Refusée"
)

print("\nTEST 17 : refus de la demande réussi =", resultat)

objet = get_object_by_id(object_id)

print(
    "Statut du sac après le refus :",
    objet["status"] if objet else "Objet introuvable"
)


# ==================================================
# TEST 18 : CREER UN DEUXIEME OBJET POUR TESTER L'ACCEPTATION
# ==================================================

object_id_2 = add_object(
    name_object="Clé USB",
    description="Clé USB trouvée dans une salle",
    category="Informatique",
    type_declaration="Trouvé",
    location="Salle 12",
    date_declaration="2026-10-26",
    user_id=test_owner_id
)

restitution_id_2 = add_restitution(
    object_id_2,
    test_claimant_id,
    "Cette clé USB m'appartient."
)

print("\nTEST 18 : deuxième objet et demande créés.")


# ==================================================
# TEST 19 : ACCEPTER LA DEUXIEME DEMANDE
# ==================================================

resultat = update_restitution_status(
    test_owner_id,
    restitution_id_2,
    "Acceptée"
)

print("\nTEST 19 : acceptation réussie =", resultat)

objet_2 = get_object_by_id(object_id_2)

print(
    "Statut de la clé USB après acceptation :",
    objet_2["status"] if objet_2 else "Objet introuvable"
)


# ==================================================
# TEST 20 : SUPPRIMER UNE DEMANDE ENCORE EN ATTENTE
# ==================================================

object_id_3 = add_object(
    name_object="Cahier bleu",
    description="Cahier trouvé dans le couloir",
    category="Fournitures",
    type_declaration="Trouvé",
    location="Couloir",
    date_declaration="2026-10-26",
    user_id=test_owner_id
)

restitution_id_3 = add_restitution(
    object_id_3,
    test_claimant_id,
    "Ce cahier est à moi."
)

resultat = delete_restitution(
    test_claimant_id,
    restitution_id_3
)

print("\nTEST 20 : suppression de la demande réussie =", resultat)

demandes = get_restitutions_by_user(test_claimant_id)

demande_existe = any(
    demande["id_restitution"] == restitution_id_3
    for demande in demandes
)

print("La demande existe encore :", demande_existe)


# ==================================================
# TEST 21 : SUPPRIMER UN OBJET DE TEST
# ==================================================

# On supprime le sac, qui appartient bien au propriétaire de test.
resultat = delete_object(test_owner_id, object_id)

print("\nTEST 21 : suppression de l'objet réussie =", resultat)

objet_supprime = get_object_by_id(object_id)

print("L'objet existe encore :", objet_supprime is not None)


# ==================================================
# FIN DES TESTS
# ==================================================

print("\n====================================")
print("FIN DE TOUS LES TESTS")
print("====================================")

# TEST 22 : un utilisateur non autorisé essaie d'accepter une demande

print("\nTEST 22 : tentative d'acceptation non autorisée")

resultat = update_restitution_status(
    claimant_id,          # Sara, qui n'est pas propriétaire
    restitution_id_test,  # La demande concernant le téléphone d'Ahmed
    "Acceptée"
)

print("Résultat de la tentative :", resultat)

objet = get_object_by_id(object_id_test)

if objet:
    print("Statut du téléphone :", objet["status"])

# TEST 23 : verifier les droits du proprietaire sur une demande en attente

print("\nTEST 23 : securite du proprietaire")

# Creer un nouvel objet trouve appartenant a Ahmed
object_id_security = add_object(
    name_object="Écouteurs de test",
    description="Écouteurs trouvés dans le laboratoire",
    category="Accessoires",
    type_declaration="Trouvé",
    location="Laboratoire",
    date_declaration="2026-10-26",
    user_id=owner_id
)

# Sara demande la restitution
restitution_id_security = add_restitution(
    object_id_security,
    claimant_id,
    "Ces écouteurs sont à moi."
)

print("Demande créée :", restitution_id_security)

# Verifier le statut avant la tentative
objet = get_object_by_id(object_id_security)
print("Statut initial de l'objet :", objet["status"])

# Sara essaie d'accepter sa propre demande
resultat = update_restitution_status(
    claimant_id,
    restitution_id_security,
    "Acceptée"
)

print("Tentative de Sara :", resultat)

# Vérifier les statuts après la tentative
objet = get_object_by_id(object_id_security)

demandes_sara = get_restitutions_by_user(claimant_id)

for demande in demandes_sara:
    if demande["id_restitution"] == restitution_id_security:
        print("Statut final de la demande :", demande["statut"])

print("Statut final de l'objet :", objet["status"])

# TEST 24 : modification et suppression non autorisees

print("\nTEST 24 : securite des demandes")

# Creer un troisieme utilisateur
suffixe_securite = secrets.token_hex(4)

other_user_id = add_user(
    "Autre Utilisateur",
    f"autre_{suffixe_securite}@example.com",
    "AutreTest123!"
)

print("ID de Sara :", claimant_id)
print("ID de l'autre utilisateur :", other_user_id)

# L'autre utilisateur essaie de modifier la demande de Sara
modification = update_restitution_message(
    other_user_id,
    restitution_id_security,
    "Je modifie une demande qui ne m'appartient pas."
)

print("Modification non autorisee :", modification)

# L'autre utilisateur essaie de supprimer la demande de Sara
suppression = delete_restitution(
    other_user_id,
    restitution_id_security
)

print("Suppression non autorisee :", suppression)

# Verifier que la demande de Sara existe toujours
demandes_sara = get_restitutions_by_user(claimant_id)

demande_existe = any(
    demande["id_restitution"] == restitution_id_security
    for demande in demandes_sara
)

print("La demande de Sara existe toujours :", demande_existe)


# TEST 25 : suppression non autorisee d'un objet

print("\nTEST 25 : securite de suppression des objets")

# Ahmed possede l'objet cree au test 23
print("ID du proprietaire Ahmed :", owner_id)
print("ID de Sara :", claimant_id)

# Verifier que l'objet existe avant la tentative
objet_avant = get_object_by_id(object_id_security)

print("Objet existe avant :", objet_avant is not None)

# Sara essaie de supprimer l'objet d'Ahmed
resultat = delete_object(
    claimant_id,
    object_id_security
)

print("Suppression par Sara :", resultat)

# Verifier que l'objet existe encore
objet_apres = get_object_by_id(object_id_security)

print("Objet existe apres :", objet_apres is not None)

# TEST 26 : demander un objet deja restitue

print("\nTEST 26 : demande d'un objet deja restitue")

# object_id_test correspond au telephone accepte au test 8
objet = get_object_by_id(object_id_test)

print("Statut actuel de l'objet :", objet["status"])

# Essayer de creer une nouvelle demande
try:
    nouvelle_demande = add_restitution(
        object_id_test,
        claimant_id,
        "Je souhaite demander cet objet une nouvelle fois."
    )

    print("Nouvelle demande creee :", nouvelle_demande)

except Exception as erreur:
    print("Demande refusee :", type(erreur).__name__, "-", erreur)

# Verifier de nouveau le statut de l'objet
objet = get_object_by_id(object_id_test)

print("Statut final de l'objet :", objet["status"])

# TEST 27 : demander un objet declare Perdu

print("\nTEST 27 : demande d'un objet perdu")

# Creer un objet declare Perdu
object_id_lost = add_object(
    name_object="Portefeuille perdu",
    description="Portefeuille marron perdu dans le campus",
    category="Accessoires",
    type_declaration="Perdu",
    location="Cour de l'ecole",
    date_declaration="2026-10-26",
    user_id=owner_id
)

print("Objet perdu cree, ID :", object_id_lost)

# Sara essaie de demander la restitution de cet objet
try:
    nouvelle_demande = add_restitution(
        object_id_lost,
        claimant_id,
        "Je souhaite recuperer cet objet."
    )

    print("Nouvelle demande creee :", nouvelle_demande)

except Exception as erreur:
    print(
        "Demande refusee :",
        type(erreur).__name__,
        "-",
        erreur
    )

# Verifier que l'objet existe toujours
objet = get_object_by_id(object_id_lost)

if objet:
    print("Type de declaration :", objet["type_declaration"])
    print("Statut de l'objet :", objet["status"])

# TEST 28 : verifier l'unicite des emails

print("\nTEST 28 : email deja utilise")

email_test = "ahmed.test.unique@example.com"

try:
    add_user(
        "Ahmed Test",
        email_test,
        "motdepasse123"
    )
    print("Premier utilisateur cree.")

    add_user(
        "Ahmed Test 2",
        email_test,
        "motdepasse456"
    )
    print("ERREUR : le doublon a ete accepte.")

except Exception as erreur:
    print(
        "Deuxieme utilisateur refuse :",
        type(erreur).__name__,
        "-",
        erreur
    )

user = get_user_by_email(email_test)
print("Un utilisateur avec cet email existe :", user is not None)

# TEST 29 : deux demandes pour le meme objet par la meme personne

print("\nTEST 29 : demandes en double")

# Creer un nouvel objet trouve par Ahmed
object_id_duplicate = add_object(
    name_object="Calculatrice de test",
    description="Calculatrice noire trouvee dans une salle",
    category="Fournitures",
    type_declaration="Trouvé",
    location="Salle 3",
    date_declaration="2026-10-26",
    user_id=owner_id
)

print("Objet cree, ID :", object_id_duplicate)

# Premiere demande de Sara
try:
    demande1 = add_restitution(
        object_id_duplicate,
        claimant_id,
        "Je pense que cette calculatrice est la mienne."
    )
    print("Premiere demande creee :", demande1)

except Exception as erreur:
    print("Erreur premiere demande :", type(erreur).__name__, "-", erreur)

# Deuxieme demande pour le meme objet par Sara
try:
    demande2 = add_restitution(
        object_id_duplicate,
        claimant_id,
        "Je voudrais aussi reclamer cette calculatrice."
    )
    print("ATTENTION : deuxieme demande creee :", demande2)

except Exception as erreur:
    print(
        "Deuxieme demande refusee :",
        type(erreur).__name__,
        "-",
        erreur
    )
print("\nTEST 30 : message vide")


print("\nTEST 30 : message vide")

try:
    add_restitution(object_id_test, claimant_id, "   ")
except ValueError as e:
    print("Demande refusee :", e)

print("\nTEST 31 : objet inexistant")

try:
    add_restitution(-1, 22, "C'est mon objet.")
except ValueError as e:
    print("Demande refusee :", e)

