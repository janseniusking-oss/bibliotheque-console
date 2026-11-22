import sqlite3
from datetime import date, timedelta
from pathlib import Path


DB_FILE = Path(__file__).with_name("bibliotheque.db")

LIVRES_DE_DEPART = [
    ("Le Petit Prince", "Antoine de Saint-Exupéry"),
    ("L'Étranger", "Albert Camus"),
    ("Les Misérables", "Victor Hugo"),
    ("Notre-Dame de Paris", "Victor Hugo"),
    ("Le Rouge et le Noir", "Stendhal"),
    ("Madame Bovary", "Gustave Flaubert"),
    ("Germinal", "Émile Zola"),
    ("Au bonheur des dames", "Émile Zola"),
    ("Vingt mille lieues sous les mers", "Jules Verne"),
    ("Le Tour du monde en quatre-vingts jours", "Jules Verne"),
    ("Voyage au centre de la Terre", "Jules Verne"),
    ("Le Comte de Monte-Cristo", "Alexandre Dumas"),
    ("Les Trois Mousquetaires", "Alexandre Dumas"),
    ("Candide", "Voltaire"),
    ("Le Père Goriot", "Honoré de Balzac"),
    ("Cyrano de Bergerac", "Edmond Rostand"),
    ("Le Malade imaginaire", "Molière"),
    ("L'Avare", "Molière"),
    ("Les Fleurs du mal", "Charles Baudelaire"),
    ("Le Horla", "Guy de Maupassant"),
    ("Bel-Ami", "Guy de Maupassant"),
    ("L'Île au trésor", "Robert Louis Stevenson"),
    ("Les Aventures de Tom Sawyer", "Mark Twain"),
    ("Les Aventures de Huckleberry Finn", "Mark Twain"),
    ("Orgueil et Préjugés", "Jane Austen"),
    ("Jane Eyre", "Charlotte Brontë"),
    ("Les Hauts de Hurlevent", "Emily Brontë"),
    ("Frankenstein", "Mary Shelley"),
    ("Dracula", "Bram Stoker"),
    ("Le Portrait de Dorian Gray", "Oscar Wilde"),
    ("Alice au pays des merveilles", "Lewis Carroll"),
    ("Le Livre de la jungle", "Rudyard Kipling"),
    ("Le Vieil Homme et la Mer", "Ernest Hemingway"),
    ("1984", "George Orwell"),
    ("La Ferme des animaux", "George Orwell"),
    ("Le Meilleur des mondes", "Aldous Huxley"),
    ("Fahrenheit 451", "Ray Bradbury"),
    ("Des souris et des hommes", "John Steinbeck"),
    ("Les Raisins de la colère", "John Steinbeck"),
    ("Ne tirez pas sur l'oiseau moqueur", "Harper Lee"),
    ("Le Seigneur des anneaux", "J. R. R. Tolkien"),
    ("Le Hobbit", "J. R. R. Tolkien"),
    ("Dune", "Frank Herbert"),
    ("Fondation", "Isaac Asimov"),
    ("Le Nom de la rose", "Umberto Eco"),
    ("L'Alchimiste", "Paulo Coelho"),
    ("La Peste", "Albert Camus"),
    ("La Métamorphose", "Franz Kafka"),
    ("Crime et Châtiment", "Fiodor Dostoïevski"),
    ("Le Procès", "Franz Kafka"),
]


def initialiser_base(connexion):
    connexion.execute("PRAGMA foreign_keys = ON")
    connexion.executescript(
        """
        CREATE TABLE IF NOT EXISTS livres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            auteur TEXT NOT NULL,
            exemplaires INTEGER NOT NULL CHECK (exemplaires > 0)
        );
        CREATE TABLE IF NOT EXISTS emprunts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            livre_id INTEGER NOT NULL REFERENCES livres(id),
            emprunteur TEXT NOT NULL,
            date_emprunt TEXT NOT NULL,
            date_retour TEXT
        );
        """
    )
    colonnes_emprunts = {
        colonne[1] for colonne in connexion.execute("PRAGMA table_info(emprunts)")
    }
    if "date_retour_prevue" not in colonnes_emprunts:
        connexion.execute("ALTER TABLE emprunts ADD COLUMN date_retour_prevue TEXT")

    with connexion:
        connexion.executemany(
            """
            INSERT INTO livres (titre, auteur, exemplaires)
            SELECT ?, ?, 2
            WHERE NOT EXISTS (
                SELECT 1 FROM livres WHERE titre = ? AND auteur = ?
            )
            """,
            [(titre, auteur, titre, auteur) for titre, auteur in LIVRES_DE_DEPART],
        )


def recuperer_catalogue(connexion):
    return connexion.execute(
        """
        SELECT livres.id, livres.titre, livres.auteur, livres.exemplaires,
               livres.exemplaires - COUNT(
                   CASE WHEN emprunts.date_retour IS NULL THEN 1 END
               ) AS disponibles
        FROM livres
        LEFT JOIN emprunts ON emprunts.livre_id = livres.id
        GROUP BY livres.id
        ORDER BY livres.titre COLLATE NOCASE, livres.titre, livres.id
        """
    ).fetchall()


def afficher_livres(connexion, ids=None):
    catalogue = recuperer_catalogue(connexion)
    affiches = catalogue if ids is None else [
        livre for livre in catalogue if livre["id"] in ids
    ]
    if not affiches:
        print("Aucun livre trouvé.")
        return

    print("\n--- Catalogue ---")
    for code, livre in enumerate(catalogue, 1):
        if ids is not None and livre["id"] not in ids:
            continue
        print(
            f"L{code:04d} | {livre['titre']} — {livre['auteur']} "
            f'| {livre["disponibles"]}/{livre["exemplaires"]} disponible(s)'
        )


def ajouter_livre(connexion):
    titre = input("Titre : ").strip()
    auteur = input("Auteur : ").strip()
    if not titre or not auteur:
        print("Le titre et l'auteur sont obligatoires.")
        return

    try:
        exemplaires = int(input("Nombre d'exemplaires : ").strip())
        if exemplaires < 1:
            raise ValueError
    except ValueError:
        print("Entrez un nombre d'exemplaires supérieur à zéro.")
        return

    with connexion:
        curseur = connexion.execute(
            "INSERT INTO livres (titre, auteur, exemplaires) VALUES (?, ?, ?)",
            (titre, auteur, exemplaires),
        )
    catalogue = recuperer_catalogue(connexion)
    code = next(
        index for index, livre in enumerate(catalogue, 1) if livre["id"] == curseur.lastrowid
    )
    print(f"Livre ajouté avec l'identifiant L{code:04d}.")


def rechercher_livres(connexion):
    terme = input("Titre, auteur ou identifiant à rechercher : ").strip().casefold()
    if not terme:
        print("La recherche ne peut pas être vide.")
        return

    catalogue = recuperer_catalogue(connexion)
    resultats = {
        livre["id"]
        for code, livre in enumerate(catalogue, 1)
        if terme in livre["titre"].casefold()
        or terme in livre["auteur"].casefold()
        or terme in f"L{code:04d}".casefold()
    }
    afficher_livres(connexion, resultats)


def emprunter_livre(connexion):
    livre_id = input("Identifiant du livre (ex. L0001) : ").strip().upper()
    try:
        if not livre_id.startswith("L"):
            raise ValueError
        numero_code = int(livre_id[1:])
    except ValueError:
        print("Identifiant invalide.")
        return

    catalogue = recuperer_catalogue(connexion)
    if not 1 <= numero_code <= len(catalogue):
        print("Livre introuvable.")
        return
    livre = catalogue[numero_code - 1]
    if livre["disponibles"] < 1:
        print("Aucun exemplaire disponible.")
        return

    emprunteur = input("Nom de l'emprunteur : ").strip()
    if not emprunteur:
        print("Le nom de l'emprunteur est obligatoire.")
        return

    try:
        duree = int(input("Durée de l'emprunt en jours : ").strip())
        if duree < 1:
            raise ValueError
    except ValueError:
        print("La durée doit être un nombre de jours supérieur à zéro.")
        return

    date_debut = date.today()
    date_remise = date_debut + timedelta(days=duree)
    with connexion:
        curseur = connexion.execute(
            """
            INSERT INTO emprunts (
                livre_id, emprunteur, date_emprunt, date_retour_prevue
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                livre["id"],
                emprunteur,
                date_debut.isoformat(),
                date_remise.isoformat(),
            ),
        )
    print(
        f'Emprunt enregistré (E{curseur.lastrowid:04d}) : {livre["titre"]}.\n'
        f"Début : {date_debut.strftime('%d/%m/%Y')} | "
        f"Remise prévue : {date_remise.strftime('%d/%m/%Y')} "
        f"({duree} jours)."
    )


def retourner_livre(connexion):
    actifs = connexion.execute(
        """
        SELECT emprunts.id, livres.titre, emprunts.emprunteur,
               emprunts.date_emprunt, emprunts.date_retour_prevue
        FROM emprunts
        JOIN livres ON livres.id = emprunts.livre_id
        WHERE emprunts.date_retour IS NULL
        ORDER BY emprunts.id
        """
    ).fetchall()
    if not actifs:
        print("Aucun emprunt en cours.")
        return

    print("\n--- Emprunts en cours ---")
    for emprunt in actifs:
        remise = emprunt["date_retour_prevue"]
        remise_affichee = (
            date.fromisoformat(remise).strftime("%d/%m/%Y")
            if remise
            else "non renseignée"
        )
        retard = remise and remise < date.today().isoformat()
        print(
            f'E{emprunt["id"]:04d} | {emprunt["titre"]} | {emprunt["emprunteur"]} '
            f'| début : {date.fromisoformat(emprunt["date_emprunt"]).strftime("%d/%m/%Y")} '
            f'| remise prévue : {remise_affichee}'
            f'{" | EN RETARD" if retard else ""}'
        )

    emprunt_id = input("Identifiant de l'emprunt à clôturer : ").strip().upper()
    try:
        numero = int(emprunt_id.removeprefix("E"))
    except ValueError:
        print("Identifiant invalide.")
        return

    with connexion:
        curseur = connexion.execute(
            """
            UPDATE emprunts SET date_retour = ?
            WHERE id = ? AND date_retour IS NULL
            """,
            (date.today().isoformat(), numero),
        )
    if curseur.rowcount == 0:
        print("Emprunt introuvable.")
        return
    print(f'Retour enregistré le {date.today().strftime("%d/%m/%Y")}.')


def menu():
    print(
        "\n=== Ma bibliothèque ===\n"
        "1. Afficher le catalogue\n"
        "2. Rechercher un livre\n"
        "3. Ajouter un livre\n"
        "4. Emprunter un livre\n"
        "5. Enregistrer un retour\n"
        "0. Quitter"
    )


def main():
    try:
        connexion = sqlite3.connect(DB_FILE)
        connexion.row_factory = sqlite3.Row
        initialiser_base(connexion)
    except sqlite3.Error as erreur:
        print(f"Impossible d'ouvrir la base de données : {erreur}")
        return

    actions = {
        "1": lambda: afficher_livres(connexion),
        "2": lambda: rechercher_livres(connexion),
        "3": lambda: ajouter_livre(connexion),
        "4": lambda: emprunter_livre(connexion),
        "5": lambda: retourner_livre(connexion),
    }

    try:
        while True:
            menu()
            choix = input("Votre choix : ").strip()
            if choix == "0":
                print("À bientôt !")
                break
            action = actions.get(choix)
            if action is None:
                print("Choix invalide.")
                continue
            try:
                action()
            except sqlite3.Error as erreur:
                print(f"Erreur de base de données : {erreur}")
    except EOFError:
        print("\nFin de la saisie.")
    finally:
        connexion.close()


if __name__ == "__main__":
    main()
