
import secrets

from database.connection import get_connection
from database.User import create_table as create_users_table, add_user
from database.objects import (
    create_table as create_objects_table,
    add_object,
    get_object_by_id,
    get_objects_by_user,
    get_all_objects,
    update_object,
    delete_object

)


# TEST 1 : créer les tables
with get_connection() as connection:
    create_users_table(connection)
    create_objects_table(connection)

print("TEST 1 : tables créées avec succès !")


# TEST 2 : créer un utilisateur de test
email_test = f"test_{secrets.token_hex(4)}@example.com"

user_id = add_user(
    "Utilisateur Test",
    email_test,
    "MotDePasseTest123!"
)

print("TEST 2 : utilisateur créé, ID =", user_id)


# TEST 3 : ajouter un objet
object_id = add_object(
    user_id,
    "Téléphone Samsung",
    "Téléphone noir trouvé dans la bibliothèque",
    "Électronique",
    "Bibliothèque de l'école",
    "2026-10-24",
    "Trouvé"
)

print("TEST 3 : objet ajouté, ID =", object_id)


# TEST 4 : retrouver l'objet par son identifiant
objet = get_object_by_id(object_id)

print("TEST 4 : objet retrouvé =", objet is not None)

if objet:
    print("Nom de l'objet :", objet["name_object"])
    print("Type :", objet["type_declaration"])
    print("Statut :", objet["status"])


# TEST 5 : récupérer les objets de l'utilisateur
objets_utilisateur = get_objects_by_user(user_id)

print("TEST 5 : nombre d'objets de l'utilisateur =",
      len(objets_utilisateur))

# TEST 6 : récupérer tous les objets
tous_les_objets = get_all_objects()

print("TEST 6 : tous les objets")
for objet in tous_les_objets:
    print(objet["name_object"], "-", objet["type_declaration"],
          "-", objet["declarant_name"])

# TEST 7 : modifier un objet
resultat = update_object(
    user_id,
    object_id,
    "Téléphone Samsung modifié",
    "Téléphone noir trouvé près de la salle informatique",
    "Électronique",
    "Salle informatique",
    "2026-10-24",
    "Trouvé"
)

print("TEST 7 : modification réussie =", resultat)

objet_modifie = get_object_by_id(object_id)
print("Nouveau nom :", objet_modifie["name_object"])
print("Nouveau lieu :", objet_modifie["location"])

# TEST 8 : supprimer l'objet de test
resultat = delete_object(user_id, object_id)

print("TEST 8 : suppression réussie =", resultat)

objet_supprime = get_object_by_id(object_id)
print("L'objet existe encore :", objet_supprime is not None)