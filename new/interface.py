import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QTabWidget, QFileDialog, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt




class MainWindow(QMainWindow):
    """
    Interface Graphique Principale (QT) - Squelette sans logique métier.
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Interface Reconnaissance Faciale")
        self.setGeometry(100, 100, 900, 700)

        # Widget central
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Création des onglets
        tabs = QTabWidget()
        layout.addWidget(tabs)

        self.tab_enroll = QWidget()
        self.tab_recognize = QWidget()
        
        tabs.addTab(self.tab_enroll, "Apprentissage (Enrôlement)")
        tabs.addTab(self.tab_recognize, "Reconnaissance")

        self.setup_enroll_tab()
        self.setup_recognize_tab()

    def setup_enroll_tab(self):
        """Configuration de l'onglet d'enregistrement."""
        layout = QVBoxLayout()
        
        # Champ Nom
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Entrez le nom de la personne")
        form_layout.addWidget(QLabel("Nom :"))
        form_layout.addWidget(self.name_input)
        layout.addLayout(form_layout)

        # Bouton Charger Image
        btn_load = QPushButton("Choisir une photo")
        btn_load.clicked.connect(self.load_enroll_image)
        layout.addWidget(btn_load)

        # Zone d'affichage de l'image
        self.enroll_img_label = QLabel("Aucune image sélectionnée")
        self.enroll_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enroll_img_label.setStyleSheet("border: 1px dashed gray; min-height: 400px;")
        layout.addWidget(self.enroll_img_label)

        # Bouton Enregistrer
        btn_save = QPushButton("Enregistrer l'encodage")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        btn_save.clicked.connect(self.save_enrollment)
        layout.addWidget(btn_save)

        self.enroll_image_path = None
        self.tab_enroll.setLayout(layout)

    def setup_recognize_tab(self):
        """Configuration de l'onglet de reconnaissance."""
        layout = QVBoxLayout()

        # Bouton Tester Image
        btn_load = QPushButton("Charger une image à analyser")
        btn_load.clicked.connect(self.process_recognition)
        layout.addWidget(btn_load)

        # Zone d'affichage du résultat
        self.recog_img_label = QLabel("En attente d'image...")
        self.recog_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recog_img_label.setStyleSheet("border: 1px solid gray; min-height: 500px;")
        layout.addWidget(self.recog_img_label)

        self.tab_recognize.setLayout(layout)

    # --- Fonctions à implémenter (Callbacks) ---

    def load_enroll_image(self):
        """Ouvre un sélecteur de fichier pour l'onglet Apprentissage."""
        fname, _ = QFileDialog.getOpenFileName(self, 'Ouvrir image', '.', "Image files (*.jpg *.jpeg *.png)")
        if fname:
            self.enroll_image_path = fname
            # Affichage simple pour confirmer la sélection
            pixmap = QPixmap(fname)
            self.enroll_img_label.setPixmap(pixmap.scaled(
                self.enroll_img_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
            print(f"Image chargée pour enrôlement : {fname}")

    def save_enrollment(self):
        """Action du bouton 'Enregistrer l'encodage'."""
        name = self.name_input.text()
        path = self.enroll_image_path
        
        print("--- TODO: Implémenter la logique d'enregistrement ---")
        print(f"Nom: {name}")
        print(f"Chemin image: {path}")
        
        # Exemple de feedback visuel (à adapter)
        if name and path:
            QMessageBox.information(self, "Info", "Fonction d'enregistrement à coder ici.")
        else:
            QMessageBox.warning(self, "Attention", "Nom ou image manquant.")

    def process_recognition(self):
        """Action du bouton 'Charger une image à analyser'."""
        fname, _ = QFileDialog.getOpenFileName(self, 'Ouvrir image à tester', '.', "Image files (*.jpg *.jpeg *.png)")
        if fname:
            print("--- TODO: Implémenter la logique de reconnaissance ---")
            print(f"Image à tester: {fname}")
            
            # Affichage de l'image brute pour l'instant
            pixmap = QPixmap(fname)
            self.recog_img_label.setPixmap(pixmap.scaled(
                self.recog_img_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())