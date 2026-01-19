import cv2
import numpy as np
import os
import urllib.request
import pickle
import shutil

class FaceRecognizerManager:
    def __init__(self, model_dir="models_onnx", encoding_file="visages_connus.pkl", threshold=0.4):
        """
        Initializes the face recognition manager.
        
        :param model_dir: Directory for ONNX models.
        :param encoding_file: Path to the pickle file storing known face encodings.
        :param threshold: Cosine similarity threshold for matching.
        """
        self.model_dir = model_dir
        self.encoding_file = encoding_file
        self.threshold = threshold
        
        self.detector = None
        self.recognizer = None
        
        self.known_features = []
        self.known_names = []
        
        # OpenCV Zoo model URLs
        self.models_files = {
            "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx?raw=true",
            "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx?raw=true"
        }

    def check_and_download_models(self, progress_callback=None):
        """
        Verifies and downloads required ONNX models if missing.
        :param progress_callback: Optional callback for status updates.
        """
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        if progress_callback: progress_callback("Verification des modèles...")

        for filename, url in self.models_files.items():
            filepath = os.path.join(self.model_dir, filename)
            if not os.path.exists(filepath):
                if progress_callback: progress_callback(f"Téléchargement de {filename}...")
                try:
                    urllib.request.urlretrieve(url, filepath)
                except Exception as e:
                    if progress_callback: progress_callback(f"Erreur de téléchargement {filename}: {e}")
                    return False
        
        if progress_callback: progress_callback("Tous les modèles sont prêts.")
        return True

    def load_models(self):
        """Loads face detection (YuNet) and recognition (SFace) models."""
        try:
            self.detector = cv2.FaceDetectorYN.create(
                model=os.path.join(self.model_dir, "face_detection_yunet_2023mar.onnx"),
                config="",
                input_size=(320, 320), # Adjusted dynamically during processing
                score_threshold=0.8,
                nms_threshold=0.3,
                top_k=5000
            )
            
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=os.path.join(self.model_dir, "face_recognition_sface_2021dec.onnx"),
                config=""
            )
            return True
        except Exception as e:
            print(f"Erreur lors du chargement des modèles : {e}")
            return False

    def load_encodings(self):
        """Loads known face encodings from storage."""
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
        Scans the known faces directory and generates encodings.
        """
        if not self.detector or not self.recognizer:
            if not self.load_models():
                return False

        self.known_features = []
        self.known_names = []

        if not os.path.exists(known_dir):
            if progress_callback: progress_callback(f"Dossier {known_dir} non trouvé.")
            return False

        people_dirs = [d for d in os.listdir(known_dir) if os.path.isdir(os.path.join(known_dir, d))]
        total_people = len(people_dirs)

        for idx, name in enumerate(people_dirs):
            dir_path = os.path.join(known_dir, name)
            if progress_callback: progress_callback(f"Entraînement sur: {name} ({idx+1}/{total_people})")
            
            for filename in os.listdir(dir_path):
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                    
                filepath = os.path.join(dir_path, filename)
                img = cv2.imread(filepath)
                if img is None: continue

                # Detect faces
                h, w, _ = img.shape
                self.detector.setInputSize((w, h))
                _, faces = self.detector.detect(img)
                
                if faces is not None and len(faces) > 0:
                    # Align and extract features
                    face_align = self.recognizer.alignCrop(img, faces[0])
                    face_feature = self.recognizer.feature(face_align)
                    
                    self.known_features.append(face_feature)
                    self.known_names.append(name)
        
        # Persist data
        save_dir = os.path.dirname(self.encoding_file)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        with open(self.encoding_file, 'wb') as f:
            pickle.dump((self.known_features, self.known_names), f)
            
        if progress_callback: progress_callback(f"Terminé. {len(self.known_features)} visages sauvegardés.")
        return True

    def process_directory(self, unknown_dir, progress_callback=None):
        """
        Processes images in the target directory, identifying and renaming files.
        """
        if not self.known_features:
            if progress_callback: progress_callback("Erreur: Aucun visage connu chargé. Veuillez entraîner d'abord.")
            return

        if not os.path.exists(unknown_dir):
            if progress_callback: progress_callback(f"Dossier non trouvé: {unknown_dir}")
            return

        files = [f for f in os.listdir(unknown_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        total_files = len(files)
        renamed_count = 0

        for idx, filename in enumerate(files):
            filepath = os.path.join(unknown_dir, filename)
            
            # Progress update
            if progress_callback and idx % 5 == 0: 
                progress_callback(f"Traitement :  {idx+1}/{total_files}...")

            img = cv2.imread(filepath)
            if img is None: continue

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
                
                # Match against known features
                for i, known_feat in enumerate(self.known_features):
                    score = self.recognizer.match(known_feat, unknown_feat, cv2.FaceRecognizerSF_FR_COSINE)
                    
                    if score > best_score:
                        best_score = score
                        if score > self.threshold:
                            best_name = self.known_names[i]
                
                if best_name != "Inconnu":
                    found_names_in_image.add(best_name)

            # Rename file based on findings
            if found_names_in_image:
                new_name = self._rename_file(unknown_dir, filename, found_names_in_image)
                if new_name:
                    renamed_count += 1
                    if progress_callback: progress_callback(f"Renommée: {filename} -> {new_name}")

        if progress_callback: progress_callback(f"Terminé. {renamed_count} images renommées sur {total_files}.")

    def _rename_file(self, directory, filename, found_names):
        """Handles file renaming with duplicate prevention logic."""
        sorted_names = sorted(list(found_names))
        new_base_name = "_".join(sorted_names)
        
        _, ext = os.path.splitext(filename)
        new_filename = f"{new_base_name}{ext}"
        filepath = os.path.join(directory, filename)
        new_filepath = os.path.join(directory, new_filename)
        
        # Resolve collisions (e.g., file_2.jpg)
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

# --- USAGE EXAMPLE (Headless) ---
if __name__ == "__main__":
    BASE_DIR = os.getcwd()
    manager = FaceRecognizerManager(
        model_dir=os.path.join(BASE_DIR, "models_onnx"),
        encoding_file=os.path.join(BASE_DIR, "encodings_data", "visages.pkl"),
        threshold=0.4
    )

    def simple_logger(msg):
        print(f"[LOG] {msg}")

    # 1. Check models
    manager.check_and_download_models(simple_logger)
    
    # 2. Load models
    manager.load_models()

    # 3. Mode selection: Train or Load
    # manager.train_faces("known_faces", simple_logger) 
    manager.load_encodings()

    # 4. Process
    # manager.process_directory("unknown_faces/Darklight party", simple_logger)