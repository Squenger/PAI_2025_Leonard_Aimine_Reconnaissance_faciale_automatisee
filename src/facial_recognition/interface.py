import sys
import os

# --- Correction pour MACOS / ANACONDA ---
if sys.platform == 'darwin':
    try:
        import PyQt6
        plugin_path = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins')
        if os.path.exists(plugin_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    except ImportError:
        pass
# ---------------------------------------

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit,
    QProgressBar, QGroupBox, QStyleFactory, QDoubleSpinBox, QMessageBox,
    QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

# Importation du gestionnaire de reconnaissance
try:
    from .manager import FaceRecognizerManager
except ImportError:
    from manager import FaceRecognizerManager

class ImageViewerWindow(QDialog):
    """
    Fenêtre de visualisation des images traitées avec navigation.
    """
    def __init__(self, processed_images, parent=None):
        """
        :param processed_images: Liste de tuples (filepath, [noms reconnus])
        """
        super().__init__(parent)
        self.processed_images = processed_images
        self.current_index = 0
        
        self.setWindowTitle("Visualisation des Résultats")
        self.resize(1000, 800)
        
        self.init_ui()
        self.load_image()
    
    def init_ui(self):
        """Construit l'interface de visualisation."""
        layout = QVBoxLayout(self)
        
        # Titre avec les personnes reconnues
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #5cd6ca; padding: 10px;"
        )
        layout.addWidget(self.title_label)
        
        # Label pour afficher l'image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #ecf0f1; border: 2px solid #bdc3c7;")
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setScaledContents(False)  # Pour garder le ratio
        layout.addWidget(self.image_label, 1)  # stretch=1 pour prendre l'espace disponible
        
        # Compteur d'images
        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.counter_label.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        layout.addWidget(self.counter_label)
        
        # Boutons de navigation
        nav_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton("⬅ Précédent")
        self.btn_prev.clicked.connect(self.show_previous)
        
        self.btn_next = QPushButton("Suivant ➡")
        self.btn_next.clicked.connect(self.show_next)
        
        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet("background-color: #e74c3c; color: white;")
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_close)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        
        layout.addLayout(nav_layout)
        
        # Appliquer les styles aux boutons de navigation
        self.btn_prev.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
        self.btn_next.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
    
    def load_image(self):
        """Charge et affiche l'image courante."""
        if not self.processed_images:
            self.title_label.setText("Aucune image à afficher")
            return
        
        filepath, recognized_names = self.processed_images[self.current_index]
        
        # Afficher le titre avec les noms reconnus
        if recognized_names and recognized_names[0] != "Inconnu":
            names_str = ", ".join(recognized_names)
            self.title_label.setText(f"Personnes reconnues : {names_str}")
        else:
            self.title_label.setText("Aucune personne reconnue")
        
        # Charger et afficher l'image
        if os.path.exists(filepath):
            pixmap = QPixmap(filepath)
            if pixmap.isNull():
                self.image_label.setText("Impossible de charger l'image")
            else:
                # Redimensionner l'image pour s'adapter au label tout en gardant le ratio
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Fichier introuvable")
        
        # Mettre à jour le compteur
        self.counter_label.setText(
            f"Image {self.current_index + 1} sur {len(self.processed_images)}"
        )
        
        # Activer/désactiver les boutons selon la position
        self.btn_prev.setEnabled(self.current_index > 0)
        self.btn_next.setEnabled(self.current_index < len(self.processed_images) - 1)
    
    def show_previous(self):
        """Affiche l'image précédente."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
    
    def show_next(self):
        """Affiche l'image suivante."""
        if self.current_index < len(self.processed_images) - 1:
            self.current_index += 1
            self.load_image()
    
    def resizeEvent(self, event):
        """Redimensionne l'image quand la fenêtre est redimensionnée."""
        super().resizeEvent(event)
        self.load_image()

class WorkerThread(QThread):
    """
    Gère l'exécution des tâches lourdes en arrière-plan pour éviter de figer l'interface.
    """
    progress_signal = pyqtSignal(str)
    """Signal émettant des messages de log (str) vers l'interface utilisateur."""
    
    finished_signal = pyqtSignal()
    """Signal émis lorsque la tâche en arrière-plan est terminée."""

    def __init__(self, task_function, *args, **kwargs):
        super().__init__()
        self.task_function = task_function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # Injecte signal.emit comme fonction de rappel (callback) pour la logique métier,
        # permettant à FaceRecognizerManager de communiquer avec l'interface.
        try:
            self.task_function(*self.args, **self.kwargs, progress_callback=self.progress_signal.emit)
        except Exception as e:
            self.progress_signal.emit(f"[ERREUR CRITIQUE] {str(e)}")
        finally:
            self.finished_signal.emit()

class FaceRecoApp(QMainWindow):
    """
    Fenêtre principale de l'application de reconnaissance faciale.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Leomine - Reconnaissance Faciale Automatisée")
        self.resize(900, 700)
        
        # Initialisation du gestionnaire avec les chemins par défaut
        self.base_dir = os.getcwd()
        self.manager = FaceRecognizerManager(
            model_dir=None,  # Utilise le dossier dans le package par défaut
            encoding_file=os.path.join(self.base_dir, "encodings_data", "visages_connus.pkl")
        )

        self.worker = None 

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Construit et initialise l'interface utilisateur graphique."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- SECTION 1 : CONFIGURATION ---
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()

        # Répertoire des Visages Connus (Source pour l'apprentissage)
        self.path_known = self.create_file_input("Dossier des Visages Connus :", "known_faces")
        config_layout.addLayout(self.path_known['layout'])

        # Répertoire des Visages Inconnus (Cible pour le tri)
        self.path_unknown = self.create_file_input("Dossier à Trier :", "unknown_faces")
        config_layout.addLayout(self.path_unknown['layout'])

        # Seuil de Similarité
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Seuil de Similarité (0.1 - 0.9) :")
        threshold_label.setStyleSheet("color: black;") 
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 0.9)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(0.4)
        self.threshold_spin.setToolTip("Plus bas = Plus strict (Moins de faux positifs). Plus haut = Plus tolérant.")
        
        self.threshold_spin.valueChanged.connect(self.update_threshold)
        
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        config_layout.addLayout(threshold_layout)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # --- SECTION 2 : ACTIONS ---
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()

        self.btn_check_models = QPushButton("1. Vérifier Modèles")
        self.btn_check_models.clicked.connect(self.run_check_models)
        
        self.btn_train = QPushButton("2. Apprendre Visages")
        self.btn_train.clicked.connect(self.run_training)
        
        self.btn_process = QPushButton("3. Lancer le Tri")
        self.btn_process.clicked.connect(self.run_processing)
        
        self.btn_view_results = QPushButton("4. Voir les Résultats")
        self.btn_view_results.clicked.connect(self.show_results)
        self.btn_view_results.setEnabled(False)  # Désactivé par défaut

        # Style spécifique pour les boutons
        self.btn_process.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_view_results.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold;")
        
        actions_layout.addWidget(self.btn_check_models)
        actions_layout.addWidget(self.btn_train)
        actions_layout.addWidget(self.btn_process)
        actions_layout.addWidget(self.btn_view_results)
        
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)

        # --- SECTION 3 : LOGS ET PROGRESSION ---
        log_group = QGroupBox("Journal d'activité")
        log_layout = QVBoxLayout()

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Mode indéterminé par défaut
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        log_layout.addWidget(self.log_area)
        log_layout.addWidget(self.progress_bar)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Message d'initialisation
        self.log_message("Interface prête. Veuillez vérifier les modèles avant de commencer.")

    def create_file_input(self, label_text, default_path):
        """Crée une rangée de widgets pour la sélection de fichiers."""
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("color: black;")
        label.setFixedWidth(180)
        
        line_edit = QLineEdit()
        line_edit.setText(os.path.join(self.base_dir, default_path))
        
        btn = QPushButton("Parcourir...")
        btn.clicked.connect(lambda: self.browse_folder(line_edit))
        
        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(btn)
        
        return {'layout': layout, 'input': line_edit}

    def browse_folder(self, line_edit_widget):
        """Ouvre une boîte de dialogue pour sélectionner un répertoire."""
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier", line_edit_widget.text())
        if folder:
            line_edit_widget.setText(folder)

    def log_message(self, message):
        """Ajoute un message à la zone de texte et fait défiler vers le bas."""
        self.log_area.append(f"> {message}")
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_threshold(self, value):
        """Met à jour le seuil dans le gestionnaire."""
        self.manager.threshold = value
        self.log_message(f"Seuil mis à jour : {value:.2f}")

    def toggle_buttons(self, enable):
        """Active ou désactive les boutons d'action pendant le traitement."""
        self.btn_check_models.setEnabled(enable)
        self.btn_train.setEnabled(enable)
        self.btn_process.setEnabled(enable)
        # Note: btn_view_results reste géré séparément
        
        if not enable:
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    # --- Gestion des Threads ---

    def start_worker(self, func, *args):
        """Démarre un thread de travail (Worker)."""
        if self.worker is not None and self.worker.isRunning():
            self.log_message("Une tâche est déjà en cours...")
            return

        self.toggle_buttons(False)
        self.worker = WorkerThread(func, *args)
        self.worker.progress_signal.connect(self.log_message)
        self.worker.finished_signal.connect(lambda: self.toggle_buttons(True))
        self.worker.start()

    def run_check_models(self):
        self.log_message("--- Démarrage de la vérification des modèles ---")
        self.start_worker(self.manager.check_and_download_models)

    def run_training(self):
        directory = self.path_known['input'].text()
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "Erreur", "Le dossier des visages connus n'existe pas.")
            return
            
        self.log_message(f"--- Démarrage de l'apprentissage sur : {directory} ---")
        self.start_worker(self.manager.train_faces, directory)

    def run_processing(self):
        # S'assurer que les modèles sont chargés
        if self.manager.detector is None:
            loaded = self.manager.load_models()
            if not loaded:
                self.log_message("Erreur : Impossible de charger les modèles.")
                return

        # S'assurer que les encodages (signatures) sont chargés
        if not self.manager.known_features:
            success, count = self.manager.load_encodings()
            if success:
                self.log_message(f"Base de données chargée automatiquement : {count} visages.")
            else:
                self.log_message("ATTENTION : Aucune signature de visage chargée. Veuillez lancer l'apprentissage d'abord.")
                return

        directory = self.path_unknown['input'].text()
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "Erreur", "Le dossier cible n'existe pas.")
            return

        self.log_message(f"--- Démarrage du tri sur : {directory} ---")
        # Créer un worker avec callback pour activer le bouton une fois terminé
        if self.worker is not None and self.worker.isRunning():
            self.log_message("Une tâche est déjà en cours...")
            return

        self.toggle_buttons(False)
        self.worker = WorkerThread(self.manager.process_directory, directory)
        self.worker.progress_signal.connect(self.log_message)
        self.worker.finished_signal.connect(self.on_processing_finished)
        self.worker.start()

    def on_processing_finished(self):
        """Appelé quand le traitement est terminé."""
        self.toggle_buttons(True)
        # Activer le bouton de visualisation si des images ont été traitées
        if self.manager.processed_images:
            self.btn_view_results.setEnabled(True)
            self.log_message(f"{len(self.manager.processed_images)} images disponibles pour visualisation.")
    
    def show_results(self):
        """Affiche la fenêtre de visualisation des résultats."""
        if not self.manager.processed_images:
            QMessageBox.information(
                self,
                "Aucun résultat",
                "Aucune image n'a été traitée. Veuillez d'abord lancer le tri."
            )
            return
        
        viewer = ImageViewerWindow(self.manager.processed_images, self)
        viewer.exec()
    
    def apply_styles(self):
        """Applique les styles CSS globaux."""
        self.setStyleSheet("""
            QMainWindow { background-color: white; color: black; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; margin-top: 10px; padding-top: 15px; background-color: white; color: black; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QPushButton { padding: 8px; border-radius: 4px; background-color: #3498db; color: white; min-width: 100px; }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #bdc3c7; }
            QLineEdit { padding: 5px; border: 1px solid #ccc; border-radius: 3px; }
            QTextEdit { background-color: white; color: black; font-family: 'Consolas', 'Courier New', monospace; }
            QToolTip { color: white; background-color: #333; border: 1px solid #333; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Utilisation du style "Fusion" pour un look moderne et uniforme
    app.setStyle(QStyleFactory.create("Fusion"))
    
    window = FaceRecoApp()
    window.show()
    sys.exit(app.exec())