
from database.connection import get_connection
from database.User import (
    create_table,
    add_user,
    get_user_by_email,
    get_user_by_full_name,
    search_users,
    login
)
import secrets


# TEST 1 : créer la table
connection = get_connection()
try:
    create_table(connection)
    connection.commit()
    print("TEST 1 : table users créée avec succès !")
finally:
    connection.close()


# TEST 2 : inscrire un utilisateur de test
email = f"test_{secrets.token_hex(4)}@example.com"
nom = "Sara Test"
mot_de_passe = "CampusFind123!"

user_id = add_user(nom, email, mot_de_passe)
print("TEST 2 : utilisateur ajouté, ID =", user_id)


# TEST 3 : rechercher par e-mail
user = get_user_by_email(email)
print("TEST 3 : utilisateur trouvé =", user is not None)


# TEST 4 : rechercher par nom complet
resultats_nom = get_user_by_full_name(nom)
print("TEST 4 : recherche par nom =", len(resultats_nom), "résultat(s)")


# TEST 5 : rechercher par nom ou e-mail
resultats = search_users("Sara Test")
print("TEST 5 : recherche générale =", len(resultats), "résultat(s)")


# TEST 6 : connexion avec le bon mot de passe
utilisateur_connecte = login(email, mot_de_passe)
print("TEST 6 : connexion correcte =", utilisateur_connecte is not None)


# TEST 7 : connexion avec un mauvais mot de passe
mauvaise_connexion = login(email, "mauvais_mot_de_passe")
print("TEST 7 : mauvais mot de passe refusé =", mauvaise_connexion is None)
