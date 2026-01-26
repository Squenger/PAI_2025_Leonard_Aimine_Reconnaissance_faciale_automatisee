# Facial Recognition

[![PyPI](https://img.shields.io/pypi/v/facial-recognition.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/facial-recognition.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/facial-recognition)][pypi status]
[![License](https://img.shields.io/pypi/l/facial-recognition)][license]

[![Read the documentation at https://facial-recognition.readthedocs.io/](https://img.shields.io/readthedocs/facial-recognition/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/bosd/facial-recognition/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/bosd/facial-recognition/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Ruff codestyle][ruff badge]][ruff project]

[pypi status]: https://pypi.org/project/facial-recognition/
[read the docs]: https://facial-recognition.readthedocs.io/
[tests]: https://github.com/bosd/facial-recognition/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/bosd/facial-recognition
[pre-commit]: https://github.com/pre-commit/pre-commit
[ruff badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff project]: https://github.com/charliermarsh/ruff

## Features

- **Détection Faciale** : Utilisation du modèle YuNet pour localiser les visages.
- **Reconnaissance Faciale** : Utilisation du modèle SFace pour l'identification.
- **Interface Graphique** : Application PyQt6 pour une utilisation simplifiée.
- **Automatisation** : Renommage automatique des images en fonction des personnes identifiées.

## Requirements

- Python >= 3.9
- OpenCV (avec modules de reconnaissance faciale)
- PyQt6
- NumPy

## Installation

Verify that you have Python 3.9 or higher installed on your system.

```console
$ python --version
```

Install the required dependencies:

```console
$ pip install -r requirements.txt
```

It is not necessary to install models manually, they will be downloaded automatically when you run the application.

## Usage

Launch the application by running:

```console
uv run python -m facial_recognition
```

You can also use the `Lancer_Interface.command` script to launch the application.

(WORK IN PROGRESS)

You can lunch the application in dist folder. It is not working on macos.


# Tests

```console
$ pytest tests/test_my_project.py
```

Initialization: Ensures the manager starts with correct default paths and parameters.

Model Downloader: Mocks the verification and retrieval of ONNX models (using unittest.mock).

Model Loading: Validates the initialization of OpenCV’s YuNet detector and SFace recognizer.

Encoding Management: Tests successful signature loading and handles missing encoding files.

Renaming Logic: Verifies file renaming accuracy and collision handling (e.g., auto-incrementing to _2, _3).

Training (train_faces): Simulates directory scanning, face detection, and feature extraction.

Directory Processing (process_directory): Tests face identification in unknown image folders and automated renaming based on similarity thresholds.



## License

Distributed under the terms of the [MIT license][license],
_Facial Recognition_ is free and open source software.



## Credits

This project was generated from [@cjolowicz]'s [uv hypermodern python cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[uv hypermodern python cookiecutter]: https://github.com/bosd/cookiecutter-uv-hypermodern-python
[file an issue]: https://github.com/bosd/facial-recognition/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/bosd/facial-recognition/blob/main/LICENSE
[contributor guide]: https://github.com/bosd/facial-recognition/blob/main/CONTRIBUTING.md
[command-line reference]: https://facial-recognition.readthedocs.io/en/latest/usage.html
