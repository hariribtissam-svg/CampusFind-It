
from database.connection import get_connection

connection = get_connection()

print("Connexion réussie !")

resultat = connection.execute("PRAGMA foreign_keys").fetchone()
print("Clés étrangères activées :", resultat[0])

connection.close()
print("Connexion fermée.")
