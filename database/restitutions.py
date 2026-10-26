from database.connection import get_connection
def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS restitutions (
            id_restitution INTEGER PRIMARY KEY AUTOINCREMENT,

            id_object INTEGER NOT NULL,
            user_id INTEGER NOT NULL,

            message TEXT NOT NULL,
            date_restitution TEXT DEFAULT CURRENT_TIMESTAMP,

            statut TEXT NOT NULL DEFAULT 'En attente'
                CHECK (
                    statut IN (
                        'En attente',
                        'Acceptée',
                        'Refusée'
                    )
                ),

            FOREIGN KEY (id_object)
                REFERENCES objects(id_object)
                ON DELETE CASCADE,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE RESTRICT,

            UNIQUE (id_object, user_id)
        )
    """)
# 2. Ajouter une demande de restitution
def add_restitution(id_object, user_id, message):

    if not message.strip():
        raise ValueError("Le message ne peut pas etre vide.")

    with get_connection() as connection:

        objet = connection.execute("""
            SELECT type_declaration, status
            FROM objects
            WHERE id_object = ?
        """, (id_object,)).fetchone()

        if objet is None:
            raise ValueError("Objet introuvable.")

        if objet["type_declaration"] != "Trouvé":
            raise ValueError("Seuls les objets trouvés peuvent être réclames.")

        if objet["status"] != "Actif":
            raise ValueError("Cet objet n'est plus disponible.")

              # verifier c'est cette utilisateur a deja demander cette objet
        demande_existante = connection.execute("""
                    SELECT id_restitution
                    FROM restitutions
                    WHERE id_object = ? AND user_id = ?
                """, (id_object, user_id)).fetchone()

        if demande_existante is not None:
                raise ValueError("Vous avez déjà demandé cet objet.")


        cursor = connection.execute("""
            INSERT INTO restitutions (
                id_object, user_id, message
            )
            VALUES (?, ?, ?)
        """, (id_object, user_id, message))

        return cursor.lastrowid
def get_all_restitutions():

    with get_connection() as connection:
        cursor = connection.execute("""
            SELECT
                restitutions.*,
                users.full_name AS demandeur,
                objects.name_object AS nom_objet,
                objects.user_id AS declarant_id
            FROM restitutions
            JOIN users
                ON restitutions.user_id = users.id
            JOIN objects
                ON restitutions.id_object = objects.id_object
            ORDER BY restitutions.id_restitution DESC
        """)

        return [dict(row) for row in cursor.fetchall()]
# 4. Recuperer les demandes d'un utilisateur
def get_restitutions_by_user(user_id):

    with get_connection() as connection:
        cursor = connection.execute("""
            SELECT
                restitutions.*,
                objects.name_object AS nom_objet
            FROM restitutions
            JOIN objects
                ON restitutions.id_object = objects.id_object
            WHERE restitutions.user_id = ?
            ORDER BY restitutions.id_restitution DESC
        """, (user_id,))

        return [dict(row) for row in cursor.fetchall()]


# 5. Recuperer les demandes concernant mes objets declares
def get_restitutions_for_my_objects(owner_id):

    with get_connection() as connection:
        cursor = connection.execute("""
            SELECT
                restitutions.*,
                users.full_name AS demandeur,
                objects.name_object AS nom_objet
            FROM restitutions
            JOIN objects
                ON restitutions.id_object = objects.id_object
            JOIN users
                ON restitutions.user_id = users.id
            WHERE objects.user_id = ?
            ORDER BY restitutions.id_restitution DESC
        """, (owner_id,))

        return [dict(row) for row in cursor.fetchall()]


# 6. Modifier le message de sa propre demande
def update_restitution_message(user_id, id_restitution, message):

    if not message.strip():
        raise ValueError("Le message ne peut pas etre vide.")

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE restitutions
            SET message = ?
            WHERE id_restitution = ?
              AND user_id = ?
              AND statut = 'En attente'
        """, (message, id_restitution, user_id))

        return cursor.rowcount > 0


# 7. Accepter ou refuser une demande concernant mon objet
def update_restitution_status(
        owner_id, id_restitution, nouveau_statut):

    if nouveau_statut not in ("Acceptée", "Refusée"):
        raise ValueError("Statut invalide.")

    with get_connection() as connection:

        demande = connection.execute("""
            SELECT restitutions.id_object
            FROM restitutions
            JOIN objects
                ON restitutions.id_object = objects.id_object
            WHERE restitutions.id_restitution = ?
              AND objects.user_id = ?
              AND restitutions.statut = 'En attente'
        """, (id_restitution, owner_id)).fetchone()

        if demande is None:
            return False

        id_object = demande["id_object"]

        if nouveau_statut == "Acceptée":
            cursor = connection.execute("""
                UPDATE objects
                SET status = 'Restitué'
                WHERE id_object = ?
                  AND status = 'Actif'
                  AND type_declaration = 'Trouvé'
            """, (id_object,))

            if cursor.rowcount == 0:
                return False

        cursor = connection.execute("""
            UPDATE restitutions
            SET statut = ?
            WHERE id_restitution = ?
              AND statut = 'En attente'
        """, (nouveau_statut, id_restitution))

        return cursor.rowcount > 0


# 8. Supprimer sa propre demande en attente
def delete_restitution(user_id, id_restitution):

    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM restitutions
            WHERE id_restitution = ?
              AND user_id = ?
              AND statut = 'En attente'
        """, (id_restitution, user_id))

        return cursor.rowcount > 0
