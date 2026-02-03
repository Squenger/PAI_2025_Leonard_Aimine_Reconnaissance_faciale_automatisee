# Facial Recognition

## Features

- **Détection Faciale** : Utilisation du modèle YuNet pour localiser les visages.
- **Reconnaissance Faciale** : Utilisation du modèle SFace pour l'identification.
- **Interface Graphique** : Application PyQt6 pour une utilisation simplifiée.
- **Automatisation** : Renommage automatique des images en fonction des personnes identifiées.
- **Visualisation des Résultats** : Navigation et affichage des images traitées avec reconnaissance des personnes.

## Requirements

- Python >= 3.9
- OpenCV 
- PyQt6
- NumPy

## Installation

Verify that you have Python 3.9 or higher installed on your system.

```console
$ python --version
```

Install the project dependencies :

```console
$ uv sync
# OR
$ pip install -r requirements.txt
```

It is not necessary to install models manually, they will be downloaded automatically when you run the application.

## Usage

Launch the application by running:

```console
$ uv run facial-recognition
# OR
$ python -m facial_recognition
```

You can also use the `Lancer_Interface.command` script to launch the application on macOS.

### Workflow

1. **Vérifier les Modèles** : Click "1. Vérifier Modèles" to download required models
2. **Apprentissage** : Click "2. Apprendre Visages" to train on known faces
3. **Traitement** : Click "3. Lancer le Tri" to process and rename unknown images
4. **Visualisation** : Click "4. Voir les Résultats" to view processed images with:
   - Large image display
   - Recognized persons shown in the title
   - Navigation between images using Previous/Next buttons
   - Image counter (e.g., "Image 3 of 15")

## Tests

To run the tests, you can use `pytest`:

```console
$ pytest tests/test_facial_recognition.py
```


Tests cover:
- Initialization: Ensures the manager starts with correct default paths and parameters.
- Model Downloader: Mocks the verification and retrieval of ONNX models.
- Model Loading: Validates the initialization of OpenCV’s YuNet detector and SFace recognizer.
- Encoding Management: Tests successful signature loading and handles missing encoding files.
- Renaming Logic: Verifies file renaming accuracy and collision handling.
- Training (train_faces): Simulates directory scanning, face detection, and feature extraction.
- Directory Processing (process_directory): Tests face identification in unknown image folders.

## License

Distributed under the terms of the [MIT license](LICENSE).
