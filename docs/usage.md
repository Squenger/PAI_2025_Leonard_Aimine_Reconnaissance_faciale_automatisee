# Usage

L'application peut être lancée via la ligne de commande ou en utilisant l'exécutable généré.

## Interface Graphique (GUI)

Pour lancer l'interface graphique par défaut :

```console
$ uv run python -m facial_recognition
```

Ou en utilisant l'exécutable macOS :

```console
$ ./dist/FacialRecognition.app/Contents/MacOS/FacialRecognition
```

### Workflow de l'application

L'interface graphique propose 4 actions principales :

1. **Vérifier Modèles** : Télécharge les modèles ONNX nécessaires (YuNet pour la détection, SFace pour la reconnaissance)
2. **Apprendre Visages** : Analyse le dossier des visages connus et génère les signatures faciales
3. **Lancer le Tri** : Traite les images inconnues, identifie les personnes et renomme les fichiers
4. **Voir les Résultats** : Ouvre une fenêtre de visualisation permettant de :
   - Afficher les images traitées en grand format
   - Voir les personnes reconnues sur chaque image
   - Naviguer entre les images avec les boutons Précédent/Suivant
   - Suivre sa position avec le compteur d'images

## Référence de la ligne de commande

```{eval-rst}
.. click:: facial_recognition.__main__:main
    :prog: facial-recognition
    :nested: full
```
