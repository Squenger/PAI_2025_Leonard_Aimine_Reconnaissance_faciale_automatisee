import sys
import os

# --- Correction for MACOS / ANACONDA --- useless on windows and linux
if sys.platform == 'darwin':
    try:
        import PyQt6
        plugin_path = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins')
        os.environ['QT_PLUGIN_PATH'] = plugin_path
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(plugin_path, 'platforms')
        os.environ['QT_MAC_WANTS_LAYER'] = '1' 
    except ImportError:
        pass
# ----------------------------------

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QProgressBar, QFileDialog, QGroupBox, 
                             QDoubleSpinBox, QMessageBox, QStyleFactory)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Import all functions from FaceRecognizerManager (FaceRecognizerManager.py must be in the same directory)
from FaceRecognizerManager import FaceRecognizerManager

class WorkerThread(QThread):
    """
    Handles background execution of long-running tasks to prevent UI freezing.
    """
    progress_signal = pyqtSignal(str)  # Emits log messages to the UI
    finished_signal = pyqtSignal()     # Emits upon task completion

    def __init__(self, task_function, *args, **kwargs):
        super().__init__()
        self.task_function = task_function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # Inject signal.emit as a callback for the logic function
        # allowing face_logic.py to communicate with the UI.
        try:
            self.task_function(*self.args, **self.kwargs, progress_callback=self.progress_signal.emit)
        except Exception as e:
            self.progress_signal.emit(f"[ERREUR CRITIQUE] {str(e)}")
        finally:
            self.finished_signal.emit()

class FaceRecoApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Leomine - Reconnaissance Faciale Automatisée")
        self.resize(900, 700)
        
        # Initialize face recognizer manager with default paths
        self.base_dir = os.getcwd()
        self.manager = FaceRecognizerManager(
            model_dir=os.path.join(self.base_dir, "models_onnx"),
            encoding_file=os.path.join(self.base_dir, "encodings_data", "visages_connus.pkl")
        )

        self.worker = None 

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Builds and initializes the graphical user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- SECTION 1: CONFIGURATION ---
        config_group = QGroupBox("Configuration")
        # config_group.setStyleSheet("color: green;") 
        config_layout = QVBoxLayout()

        # Known Faces Directory (Source for training)
        self.path_known = self.create_file_input("Dossier des Visages Connus :", "known_faces")
        config_layout.addLayout(self.path_known['layout'])
        

        # Unknown Faces Directory (Target for sorting)
        self.path_unknown = self.create_file_input("Dossier à Trier :", "unknown_faces")
        config_layout.addLayout(self.path_unknown['layout'])

        # Similarity Threshold
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Seuil de Similarité (0.1 - 0.9) :")
        threshold_label.setStyleSheet("color: black;") 
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 0.9)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(0.4)
        self.threshold_spin.setToolTip("Plus bas = Plus strict. Plus haut = Plus tolérant.")
        
        self.threshold_spin.valueChanged.connect(self.update_threshold)
        
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        config_layout.addLayout(threshold_layout)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # --- SECTION 2: ACTIONS ---
        actions_group = QGroupBox("Actions")
        # actions_group.setStyleSheet("color: black;") 
        actions_layout = QHBoxLayout()


        self.btn_check_models = QPushButton("1. Vérifier Modèles")
        self.btn_check_models.clicked.connect(self.run_check_models)
        
        self.btn_train = QPushButton("2. Apprendre Visages")
        self.btn_train.clicked.connect(self.run_training)
        
        self.btn_process = QPushButton("3. Lancer le Tri")
        self.btn_process.clicked.connect(self.run_processing)

        # Button styling
        self.btn_process.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        
        actions_layout.addWidget(self.btn_check_models)
        actions_layout.addWidget(self.btn_train)
        actions_layout.addWidget(self.btn_process)
        
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)

        # --- SECTION 3: LOGS AND PROGRESS ---
        log_group = QGroupBox("Journal d'activité")
        log_layout = QVBoxLayout()

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True) # Le style est défini dans apply_styles
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate mode by default
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        log_layout.addWidget(self.log_area)
        log_layout.addWidget(self.progress_bar)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Initialize log
        self.log_message("Interface prête. Veuillez vérifier les modèles avant de commencer.")

    def create_file_input(self, label_text, default_path):
        """Creates a file selection widget row."""
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
        """Opens a dialog to select a directory."""
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier", line_edit_widget.text())
        if folder:
            line_edit_widget.setText(folder)

    def log_message(self, message):
        """Appends a message to the log area and scrolls to bottom."""
        self.log_area.append(f"> {message}")
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_threshold(self, value):
        """Updates the threshold in the manager."""
        self.manager.threshold = value
        self.log_message(f"Seuil mis à jour : {value:.2f}")

    def toggle_buttons(self, enable):
        """Enables or disables action buttons during processing."""
        self.btn_check_models.setEnabled(enable)
        self.btn_train.setEnabled(enable)
        self.btn_process.setEnabled(enable)
        
        if not enable:
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    # --- Thread Management ---

    def start_worker(self, func, *args):
        """Start a worker thread."""
        if self.worker is not None and self.worker.isRunning():
            self.log_message("Une tâche est déjà en cours...")
            return

        self.toggle_buttons(False)
        self.worker = WorkerThread(func, *args)
        self.worker.progress_signal.connect(self.log_message)
        self.worker.finished_signal.connect(lambda: self.toggle_buttons(True))
        self.worker.start()

    def run_check_models(self):
        self.log_message("--- Démarrage vérification modèles ---")
        self.start_worker(self.manager.check_and_download_models)

    def run_training(self):
        directory = self.path_known['input'].text()
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "Erreur", "Le dossier des visages connus n'existe pas.")
            return
            
        self.log_message(f"--- Démarrage apprentissage sur : {directory} ---")
        self.start_worker(self.manager.train_faces, directory)

    def run_processing(self):
        # Ensure models are loaded
        if self.manager.detector is None:
            loaded = self.manager.load_models()
            if not loaded:
                self.log_message("Erreur : Impossible de charger les modèles.")
                return

        # Ensure encodings are loaded
        if not self.manager.known_features:
            success, count = self.manager.load_encodings()
            if success:
                self.log_message(f"Mémoire chargée automatiquement : {count} visages.")
            else:
                self.log_message("ATTENTION : Aucune mémoire de visage chargée. Veuillez faire l'apprentissage d'abord.")
                return

        directory = self.path_unknown['input'].text()
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "Erreur", "Le dossier cible n'existe pas.")
            return

        self.log_message(f"--- Démarrage du tri sur : {directory} ---")
        self.start_worker(self.manager.process_directory, directory)

    def apply_styles(self):
        """Applies global CSS styling."""
        # Les couleurs de texte par défaut seront noires sur fond blanc, sauf pour les boutons et tooltips
        self.setStyleSheet("""
            QMainWindow { background-color: white; color: black; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; margin-top: 10px; padding-top: 15px; background-color: white; color: black; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QPushButton { padding: 8px; border-radius: 4px; background-color: #3498db; color: white; min-width: 100px; }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #bdc3c7; }
            QLineEdit { padding: 5px; border: 1px solid #ccc; border-radius: 3px; }
            QTextEdit { background-color: white; color: black; font-family: Consolas; }
            QToolTip { color: white; background-color: #333; border: 1px solid #333; } /* Garde le tooltip sombre pour une meilleure lisibilité */
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Improved native look
    app.setStyle(QStyleFactory.create("Fusion"))
    
    window = FaceRecoApp()
    window.show()
    sys.exit(app.exec())