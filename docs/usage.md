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

## Référence de la ligne de commande

```{eval-rst}
.. click:: facial_recognition.__main__:main
    :prog: facial-recognition
    :nested: full
```
