# Architecture du Projet

Ce document décrit la structure du projet 

## Racine du Projet

- **`pyproject.toml`** : Le fichier de configuration principal. Il définit :
    - Les métadonnées du projet (nom, version, auteur).
    - Les dépendances (pandas, opencv, PyQt6, etc.).
    - Les configurations des outils de développement (Ruff pour le linting, MyPy pour les types, Pytest pour les tests, Coverge, etc.).
    - L'exclusion du package `scripts_without_interface`.

- **`uv.lock`** : Fichier généré par `uv`. Il verrouille les versions exactes de toutes les dépendances pour garantir que tout le monde utilise exactement les mêmes librairies.

- **`README.md`** : La documentation principale pour l'utilisateur. Explique comment installer, lancer et tester le projet.

- **`Lancer_Interface.command`** : Script spécifique pour macOS permettant de lancer l'application en un double-clic (lance `uv run python -m facial_recognition`).

- **`.gitignore`** : Liste les fichiers et dossiers que Git doit ignorer (comme les fichiers temporaires, le dossier virtuel `.venv`, `__pycache__`, etc.).

- **`.editorconfig`** : Définit les styles de codage (indentation, fin de ligne) pour assurer la cohérence entre différents éditeurs de code.

- **`.gitattributes`** : Configure le comportement de Git sur certains fichiers (ex: gestion des fins de ligne LF/CRLF).

- **`.pre-commit-config.yaml`** : Configuration pour l'outil `pre-commit`. Il définit les vérifications automatiques (linting, fin de fichiers, etc.) qui s'exécutent avant chaque commit pour garder le code propre.

- **`LICENSE`** : Le fichier de licence (MIT) définissant les droits d'utilisation du code.

## Dossiers Spéciaux

### `.github/`
Contient les configurations pour GitHub Actions.
- **`workflows/tests.yml`** : Définit le pipeline d'intégration continue (CI). À chaque "push", GitHub installe le projet et lance automatiquement les tests (`pytest`) et les vérifications de (`pre-commit`) pour s'assurer que rien n'est cassé.

### `src/`
Le code source de l'application.
- **`facial_recognition/`** : Le package Python principal.
    - **`__init__.py`** : Marque le dossier comme un package Python.
    - **`__main__.py`** : Point d'entrée pour lancer l'application via `python -m facial_recognition`.
    - **`interface.py`** : Contient le code de l'interface graphique (PyQt6) :
        - `FaceRecoApp` : Fenêtre principale avec 4 boutons d'action (Vérifier Modèles, Apprendre Visages, Lancer le Tri, Voir les Résultats)
        - `ImageViewerWindow` : Fenêtre de visualisation des images traitées avec navigation
        - `WorkerThread` : Gestion des tâches en arrière-plan
    - **`manager.py`** : Logique métier principale :
        - Gestion des modèles ONNX (YuNet, SFace)
        - Chargement et sauvegarde des encodages
        - Traitement et renommage des images
        - Stockage des résultats dans `processed_images` pour visualisation
    - **`py.typed`** : Fichier vide (marker) indiquant que le package fournit des annotations de type (compatible PEP 561).
    - **`extraction/`** : Dossier à ignorer contenant l'extraction des visages à partir d'un trombinoscope.
    - **`models_onnx/`** : Dossier contenant les modèles de reconnaissance faciale (SFace, YuNet).
    - **`scripts_without_interface/`** : Dossier contenant des scripts expérimentaux ou hors interface, ignoré par la configuration du projet et git.
- **`facial_recognition.egg-info/`** : Dossier généré automatiquement contenant les métadonnées du package installé (versions, dépendances...).

### `tests/`
Contient les tests unitaires et d'intégration.
- **`test_facial_recognition.py`** : Le fichier principal contenant tous les tests (vérification du manager, du renommage, de l'entrainement, etc.).

### `docs/`
Configuration pour la documentation (Sphinx).
- **`conf.py`** : Configuration de Sphinx (thème, extensions).
- **`index.md`, `usage.md`, etc.** : Les pages de documentation au format Markdown.
