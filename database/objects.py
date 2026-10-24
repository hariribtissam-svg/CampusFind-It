
from database.connection import get_connection
def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS objects (
            id_object INTEGER PRIMARY KEY AUTOINCREMENT,
            name_object TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            type_declaration TEXT NOT NULL
                CHECK (type_declaration IN ('Perdu', 'Trouvé')),
            location TEXT NOT NULL,
            date_declaration TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Actif'
                CHECK (status IN ('Actif','Restitué')),
            user_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
            ON DELETE RESTRICT
        )
    """)


# 2. Ajouter un objet perdu ou trouvé

def add_object(user_id, name_object, description, category,
               location, date_declaration, type_declaration):

    if type_declaration not in ("Perdu", "Trouvé"):
        raise ValueError("Le type doit être Perdu ou Trouvé.")

    if not name_object.strip():
        raise ValueError("Le nom de l'objet est obligatoire.")

    if not category.strip():
        raise ValueError("La catégorie est obligatoire.")

    if not location.strip():
        raise ValueError("Le lieu est obligatoire.")

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO objects (
                user_id, name_object, description, category,
                location, date_declaration, type_declaration
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, name_object.strip(), description.strip(),
            category.strip(), location.strip(),
            date_declaration, type_declaration
        ))

        return cursor.lastrowid


# 3. Récupérer les objets déclarés par un utilisateur


def get_objects_by_user(user_id):
    with get_connection() as connection:
        cursor = connection.execute("""
            SELECT *
            FROM objects
            WHERE user_id = ?
            ORDER BY id_object DESC
        """, (user_id,))

        return [dict(row) for row in cursor.fetchall()]


# 4. Récupérer tous les objets

def get_all_objects():
    with get_connection() as connection:
        cursor = connection.execute("""
            SELECT
                objects.*,
                users.full_name AS declarant_name
            FROM objects
            JOIN users ON objects.user_id = users.id
            ORDER BY objects.id_object DESC
        """)

        return [dict(row) for row in cursor.fetchall()]


# 5. Récupérer un objet à partir de son identifiant

def get_object_by_id(id_object):
    with get_connection() as connection:
        cursor = connection.execute("""
            SELECT *
            FROM objects
            WHERE id_object = ?
        """, (id_object,))

        row = cursor.fetchone()
        return dict(row) if row else None


# 6. Modifier un objet appartenant à un utilisateur

def update_object(user_id, id_object, name_object, description,
                  category, location, date_declaration,
                  type_declaration):

    if type_declaration not in ("Perdu", "Trouvé"):
        raise ValueError("Le type doit être Perdu ou Trouvé.")

    if not name_object.strip() or not category.strip() or not location.strip():
        raise ValueError("Le nom, la catégorie et le lieu sont obligatoires.")

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE objects
            SET name_object = ?,
                description = ?,
                category = ?,
                location = ?,
                date_declaration = ?,
                type_declaration = ?
            WHERE id_object = ? AND user_id = ?
        """, (
            name_object.strip(), description.strip(), category.strip(),
            location.strip(), date_declaration, type_declaration,
            id_object, user_id
        ))

        return cursor.rowcount > 0


# 7. Supprimer un objet déclaré par un utilisateur

def delete_object(user_id, id_object):
    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM objects
            WHERE id_object = ? AND user_id = ?
        """, (id_object, user_id))

        return cursor.rowcount > 0





