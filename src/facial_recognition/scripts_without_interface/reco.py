import cv2
import numpy as np
import os
import urllib.request
import pickle

# --- CONFIGURATION ---
# Mettre à True pour ré-apprendre les visages (si vous avez ajouté des photos dans known_faces)
# Mettre à False pour utiliser la mémoire sauvegardée (démarrage ultra-rapide)
APPRENDRE = True 

KNOWN_DIR = "known_faces"
UNKNOWN_DIR = "unknown_faces/Darklight party"

# Dossier pour stocker la "mémoire" du programme
ENCODING_DIR = "encodings_data"
ENCODING_FILE = "visages_connus.pkl"

# Seuil de reconnaissance (Cosine Similarity)
MATCH_THRESHOLD = 0.4 
MODEL_DIR = "models_onnx"

# --- TÉLÉCHARGEMENT AUTOMATIQUE DES MODÈLES OPENCV ZOO ---
models_files = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx?raw=true",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx?raw=true"
}

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

print("Vérification des modèles ONNX...")
for filename, url in models_files.items():
    filepath = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Téléchargement de {filename}...")
        try:
            urllib.request.urlretrieve(url, filepath)
        except Exception as e:
            print(f"Erreur de téléchargement : {e}")
            exit()
print("Modèles prêts.\n")


# --- INITIALISATION DES RÉSEAUX NEURONAUX ---
detector = cv2.FaceDetectorYN.create(
    model=os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx"),
    config="",
    input_size=(320, 320),
    score_threshold=0.8,
    nms_threshold=0.3,
    top_k=5000
)

recognizer = cv2.FaceRecognizerSF.create(
    model=os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx"),
    config=""
)

def get_face_embedding(image, face_box):
    face_align = recognizer.alignCrop(image, face_box)
    face_feature = recognizer.feature(face_align)
    return face_feature

def process_image(img):
    h, w, _ = img.shape
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    return faces if faces is not None else []

# --- PARTIE 1 : GESTION DE LA MÉMOIRE (APPRENTISSAGE OU CHARGEMENT) ---
known_features = [] 
known_names = []  
full_encoding_path = os.path.join(ENCODING_DIR, ENCODING_FILE)

# Création du dossier de stockage si inexistant
if not os.path.exists(ENCODING_DIR):
    os.makedirs(ENCODING_DIR)

if APPRENDRE:
    print("--- MODE APPRENTISSAGE ACTIVÉ ---")
    print(f"Lecture du dossier {KNOWN_DIR}...")
    
    if not os.path.exists(KNOWN_DIR):
        os.makedirs(KNOWN_DIR)

    for name in os.listdir(KNOWN_DIR):
        dir_path = os.path.join(KNOWN_DIR, name)
        if not os.path.isdir(dir_path):
            continue
            
        print(f"Apprentissage : {name}")
        for filename in os.listdir(dir_path):
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
                
            filepath = os.path.join(dir_path, filename)
            img = cv2.imread(filepath)
            if img is None: continue

            faces = process_image(img)
            
            if len(faces) > 0:
                feature = get_face_embedding(img, faces[0])
                known_features.append(feature)
                known_names.append(name)
    
    # Sauvegarde dans le fichier pickle
    print(f"Sauvegarde des données dans {full_encoding_path}...")
    with open(full_encoding_path, 'wb') as f:
        pickle.dump((known_features, known_names), f)
    print(f"Terminé. {len(known_features)} visages appris et sauvegardés.\n")

else:
    print("--- MODE LECTURE RAPIDE (APPRENTISSAGE DÉSACTIVÉ) ---")
    if os.path.exists(full_encoding_path):
        print(f"Chargement du fichier {full_encoding_path}...")
        with open(full_encoding_path, 'rb') as f:
            known_features, known_names = pickle.load(f)
        print(f"Mémoire chargée ! {len(known_features)} visages connus prêts.\n")
    else:
        print(f"ERREUR : Le fichier {full_encoding_path} n'existe pas.")
        print("Veuillez mettre APPRENDRE = True pour la première exécution.")
        exit()


# --- PARTIE 2 : TRAITEMENT AUTOMATIQUE (BATCH) ---
print(f"--- TRAITEMENT AUTOMATIQUE DE {UNKNOWN_DIR} ---")

if not os.path.exists(UNKNOWN_DIR):
    print(f"Erreur : Le dossier {UNKNOWN_DIR} n'existe pas.")
    exit()

files_to_process = os.listdir(UNKNOWN_DIR)
count_processed = 0
count_renamed = 0

for filename in files_to_process:
    filepath = os.path.join(UNKNOWN_DIR, filename)
    
    if not os.path.exists(filepath): continue
    if not filename.lower().endswith(('.jpg', '.jpeg', '.png')): continue
        
    img = cv2.imread(filepath)
    if img is None: continue
    
    count_processed += 1
    
    faces = process_image(img)
    
    if len(faces) == 0:
        continue

    found_names_in_image = set()

    for face in faces:
        unknown_feat = get_face_embedding(img, face)
        
        best_score = 0.0
        best_name = "Inconnu"
        
        for i, known_feat in enumerate(known_features):
            score = recognizer.match(known_feat, unknown_feat, cv2.FaceRecognizerSF_FR_COSINE)
            
            if score > best_score:
                best_score = score
                if score > MATCH_THRESHOLD:
                    best_name = known_names[i]
        
        if best_name != "Inconnu":
            found_names_in_image.add(best_name)

    # --- LOGIQUE DE RENOMMAGE ---
    if found_names_in_image:
        sorted_names = sorted(list(found_names_in_image))
        new_base_name = "_".join(sorted_names)
        
        _, ext = os.path.splitext(filename)
        new_filename = f"{new_base_name}{ext}"
        new_filepath = os.path.join(UNKNOWN_DIR, new_filename)
        
        counter = 2
        final_new_filename = new_filename
        final_new_filepath = new_filepath
        
        while os.path.exists(final_new_filepath) and final_new_filepath != filepath:
            final_new_filename = f"{new_base_name}_{counter}{ext}"
            final_new_filepath = os.path.join(UNKNOWN_DIR, final_new_filename)
            counter += 1
            
        if filepath != final_new_filepath:
            try:
                os.rename(filepath, final_new_filepath)
                print(f"[RENOMMÉ] {filename} -> {final_new_filename}")
                count_renamed += 1
            except OSError as e:
                print(f"[ERREUR] Impossible de renommer {filename} : {e}")
        else:
            print(f"[DÉJÀ NOMMÉ] {filename}")
    else:
        pass # On ne pollue pas la console si inconnu

print(f"\n--- TERMINÉ ---")
print(f"Images traitées : {count_processed}")
print(f"Images renommées : {count_renamed}")