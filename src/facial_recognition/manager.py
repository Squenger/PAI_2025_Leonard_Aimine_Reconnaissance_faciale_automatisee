import cv2
import numpy as np
import os
import urllib.request
import pickle
import shutil

class FaceRecognizerManager:
    """
    Gère la détection et la reconnaissance faciale via les modèles ONNX d'OpenCV Zoo.
    Cette classe permet l'entraînement (encodage) et l'identification automatique 
    d'images dans un répertoire donné.
    """

    def __init__(self, model_dir=None, encoding_file="visages_connus.pkl", threshold=0.4):
        """
        Initialise le gestionnaire de reconnaissance faciale.
        
        :param model_dir: Répertoire de stockage des modèles ONNX.
        :param encoding_file: Chemin du fichier pickle stockant les signatures faciales.
        :param threshold: Seuil de similarité cosinus pour la validation d'une correspondance.
        """
        if model_dir is None:
            # Chemin par défaut vers le dossier des modèles dans le package
            model_dir = os.path.join(os.path.dirname(__file__), "models_onnx")
            
        self.model_dir = model_dir
        self.encoding_file = encoding_file
        self.threshold = threshold
        
        self.detector = None
        self.recognizer = None
        
        self.known_features = []
        self.known_names = []
        
        # URLs des modèles provenant d'OpenCV Zoo
        self.models_files = {
            "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx?raw=true",
            "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx?raw=true"
        }

    def check_and_download_models(self, progress_callback=None):
        """
        Vérifie la présence des modèles ONNX et les télécharge si nécessaire.
        
        :param progress_callback: Fonction de rappel optionnelle pour le suivi de l'état.
        :return: bool: True si les modèles sont prêts, False en cas d'erreur.
        """
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        if progress_callback: progress_callback("Vérification des modèles...")

        for filename, url in self.models_files.items():
            filepath = os.path.join(self.model_dir, filename)
            if not os.path.exists(filepath):
                if progress_callback: progress_callback(f"Téléchargement de {filename}...")
                try:
                    urllib.request.urlretrieve(url, filepath)
                except Exception as e:
                    if progress_callback: progress_callback(f"Erreur de téléchargement {filename}: {e}")
                    return False
        
        if progress_callback: progress_callback("Tous les modèles sont opérationnels.")
        return True

    def load_models(self):
        """
        Initialise les instances de détection (YuNet) et de reconnaissance (SFace).
        
        :return: bool: True si le chargement réussit.
        """
        try:
            # Création du détecteur de visages YuNet
            self.detector = cv2.FaceDetectorYN.create(
                model=os.path.join(self.model_dir, "face_detection_yunet_2023mar.onnx"),
                config="",
                input_size=(320, 320), # Ajusté dynamiquement lors du traitement
                score_threshold=0.8,
                nms_threshold=0.3,
                top_k=5000
            )
            
            # Création du reconnaisseur SFace
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=os.path.join(self.model_dir, "face_recognition_sface_2021dec.onnx"),
                config=""
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation des modèles : {e}")
            return False

    def load_encodings(self):
        """
        Charge les signatures faciales connues depuis le fichier de stockage.
        
        :return: (bool, int): Statut du chargement et nombre de visages chargés.
        """
        if os.path.exists(self.encoding_file):
            try:
                with open(self.encoding_file, 'rb') as f:
                    self.known_features, self.known_names = pickle.load(f)
                return True, len(self.known_names)
            except Exception:
                return False, 0
        return False, 0

    def train_faces(self, known_dir, progress_callback=None):
        """
        Parcourt le répertoire des visages connus pour générer les signatures (encodage).
        
        :param known_dir: Répertoire contenant des sous-dossiers nommés par personne.
        :param progress_callback: Fonction de rappel pour le suivi de la progression.
        """
        if not self.detector or not self.recognizer:
            if not self.load_models():
                return False

        self.known_features = []
        self.known_names = []

        if not os.path.exists(known_dir):
            if progress_callback: progress_callback(f"Erreur : Le dossier {known_dir} est introuvable.")
            return False

        people_dirs = [d for d in os.listdir(known_dir) if os.path.isdir(os.path.join(known_dir, d))]
        total_people = len(people_dirs)

        for idx, name in enumerate(people_dirs):
            dir_path = os.path.join(known_dir, name)
            if progress_callback: progress_callback(f"Analyse de : {name} ({idx+1}/{total_people})")
            
            for filename in os.listdir(dir_path):
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                    
                filepath = os.path.join(dir_path, filename)
                img = cv2.imread(filepath)
                if img is None: continue

                # Détection faciale
                h, w, _ = img.shape
                self.detector.setInputSize((w, h))
                _, faces = self.detector.detect(img)
                
                if faces is not None and len(faces) > 0:
                    # Alignement et extraction des caractéristiques (features)
                    face_align = self.recognizer.alignCrop(img, faces[0])
                    face_feature = self.recognizer.feature(face_align)
                    
                    self.known_features.append(face_feature)
                    self.known_names.append(name)
        
        # Persistance des données
        save_dir = os.path.dirname(self.encoding_file)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        with open(self.encoding_file, 'wb') as f:
            pickle.dump((self.known_features, self.known_names), f)
            
        if progress_callback: progress_callback(f"Entraînement terminé. {len(self.known_features)} signatures sauvegardées.")
        return True

    def process_directory(self, unknown_dir, progress_callback=None):
        """
        Traite les images d'un répertoire cible, identifie les personnes et renomme les fichiers.
        
        :param unknown_dir: Répertoire contenant les images à identifier.
        :param progress_callback: Fonction de rappel pour le suivi de la progression.
        """
        if not self.known_features:
            if progress_callback: progress_callback("Erreur : Aucune signature chargée. Lancez l'entraînement d'abord.")
            return

        if not os.path.exists(unknown_dir):
            if progress_callback: progress_callback(f"Dossier introuvable : {unknown_dir}")
            return

        files = [f for f in os.listdir(unknown_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        total_files = len(files)
        renamed_count = 0

        for idx, filename in enumerate(files):
            filepath = os.path.join(unknown_dir, filename)
            
            if progress_callback and idx % 5 == 0: 
                progress_callback(f"Traitement en cours : {idx+1}/{total_files}...")

            img = cv2.imread(filepath)
            if img is None: continue

            # Mise à jour de la taille d'entrée pour le détecteur
            h, w, _ = img.shape
            self.detector.setInputSize((w, h))
            _, faces = self.detector.detect(img)

            if faces is None or len(faces) == 0:
                continue

            found_names_in_image = set()

            for face in faces:
                face_align = self.recognizer.alignCrop(img, face)
                unknown_feat = self.recognizer.feature(face_align)
                
                best_score = 0.0
                best_name = "Inconnu"
                
                # Comparaison avec les signatures connues
                for i, known_feat in enumerate(self.known_features):
                    score = self.recognizer.match(known_feat, unknown_feat, cv2.FaceRecognizerSF_FR_COSINE)
                    
                    if score > best_score:
                        best_score = score
                        if score > self.threshold:
                            best_name = self.known_names[i]
                
                if best_name != "Inconnu":
                    found_names_in_image.add(best_name)

            # Renommage du fichier si des visages sont identifiés
            if found_names_in_image:
                new_name = self._rename_file(unknown_dir, filename, found_names_in_image)
                if new_name:
                    renamed_count += 1
                    if progress_callback: progress_callback(f"Renommé : {filename} -> {new_name}")

        if progress_callback: progress_callback(f"Traitement terminé. {renamed_count} images identifiées sur {total_files}.")

    def _rename_file(self, directory, filename, found_names):
        """
        Gère la logique de renommage des fichiers avec prévention des doublons.
        
        :param directory: Chemin du répertoire.
        :param filename: Nom d'origine du fichier.
        :param found_names: Ensemble des noms identifiés sur l'image.
        :return: str: Nouveau nom du fichier ou None en cas d'erreur.
        """
        sorted_names = sorted(list(found_names))
        new_base_name = "_".join(sorted_names)
        
        _, ext = os.path.splitext(filename)
        new_filename = f"{new_base_name}{ext}"
        filepath = os.path.join(directory, filename)
        new_filepath = os.path.join(directory, new_filename)
        
        # Gestion des collisions (ex: personne_2.jpg)
        counter = 2
        final_new_filename = new_filename
        final_new_filepath = new_filepath
        
        while os.path.exists(final_new_filepath) and final_new_filepath != filepath:
            final_new_filename = f"{new_base_name}_{counter}{ext}"
            final_new_filepath = os.path.join(directory, final_new_filename)
            counter += 1
            
        if filepath != final_new_filepath:
            try:
                os.rename(filepath, final_new_filepath)
                return final_new_filename
            except OSError:
                return None
        return None
