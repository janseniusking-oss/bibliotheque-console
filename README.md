# Ma bibliothèque

Application de gestion de bibliothèque en Python, utilisable depuis un terminal.

## Lancer l'application

Python 3 est requis. Dans ce dossier, exécutez :

```powershell
python bibliotheque.py
```

Les données sont enregistrées dans la base SQLite `bibliotheque.db`, créée à côté du programme. Le catalogue est initialisé avec 50 livres (deux exemplaires chacun) au premier lancement.

## Fonctions

- Afficher et rechercher les livres par titre, auteur ou identifiant
- Ajouter des livres et préciser le nombre d'exemplaires
- Enregistrer les emprunts et les retours
- Définir la durée d'un emprunt, avec dates de début et de remise prévue
- Consulter les exemplaires disponibles et les emprunts en cours
