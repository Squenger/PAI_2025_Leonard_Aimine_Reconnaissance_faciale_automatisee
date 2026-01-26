import fitz  # PyMuPDF
import os
import re

def nettoyer_texte_dossier(texte):
    """Nettoie le texte pour qu'il soit un nom de dossier valide."""
    # Enlève les caractères interdits
    texte = texte.replace("\n", " ").strip()
    return re.sub(r'[<>:"/\\|?*]', '', texte)

def extraire_photos_clean(pdf_path, output_folder):
    # Création du dossier racine
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Dossier racine '{output_folder}' créé.")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Erreur d'ouverture du fichier : {e}")
        return

    print(f"Traitement du fichier : {pdf_path}")
    
    # LISTE NOIRE : Mots à ignorer absolument
    # J'ai ajouté DIP, ING, et d'autres termes techniques courants dans ce type de document
    mots_interdits = {
        "CONTACTER", "L'ÉTUDIANT", "ETUDIANT", "SYNAPSES", 
        "DIP", "ING", "DIPLÔME", "NIVEAU", "PROMO", 
        "1ÈRE", "LÈRE", "ANNÉE", "2027", "2024", "2025"
    }

    compteur_succes = 0

    for i, page in enumerate(doc):
        # 1. Récupération des images
        image_list = page.get_images(full=True)
        images_data = []
        
        for img in image_list:
            xref = img[0]
            rects = page.get_image_rects(xref)
            if not rects: continue
            rect = rects[0]
            images_data.append({'xref': xref, 'rect': rect})

        # Tri vertical des images (haut vers bas)
        images_data.sort(key=lambda x: x['rect'].y0)

        # 2. Récupération des mots
        words = page.get_text("words")
        # Format words: (x0, y0, x1, y1, "mot", ...)

        for img_info in images_data:
            img_rect = img_info['rect']
            img_y_center = (img_rect.y0 + img_rect.y1) / 2
            img_x_max = img_rect.x1 
            
            # Récupérer les mots sur la même ligne, à droite de la photo
            mots_candidats = []
            for w in words:
                w_y_center = (w[1] + w[3]) / 2
                w_x_min = w[0]
                text = w[4]
                
                # Alignement vertical (tolérance +/- 10px) et position à droite
                if abs(w_y_center - img_y_center) < 15 and w_x_min > img_x_max:
                    # FILTRAGE : On vérifie si le mot est dans la liste noire (en majuscule)
                    if text.upper() not in mots_interdits and len(text) > 1:
                        mots_candidats.append({'text': text, 'x': w_x_min})

            # Tri des mots de gauche à droite
            mots_candidats.sort(key=lambda x: x['x'])
            
            # 3. Identification Nom / Prénom
            # On s'attend à trouver : [Parties du Nom] [Parties du Prénom]
            # Le reste (DIP ING) a normalement été filtré par la liste noire.
            
            parties_nom = []
            parties_prenom = []
            
            for item in mots_candidats:
                mot = item['text']
                # Heuristique : Si TOUT MAJUSCULE -> Partie du NOM
                # Sinon -> Partie du Prénom
                if mot.replace("-", "").isupper():
                    parties_nom.append(mot)
                else:
                    parties_prenom.append(mot)

            # Si on a trouvé des éléments, on construit le nom du dossier
            if parties_nom or parties_prenom:
                nom_final = " ".join(parties_nom)
                prenom_final = " ".join(parties_prenom)
                
                # Format demandé : Prénom_Nom
                # Si le prénom est vide, on met juste le nom et inversement
                if prenom_final and nom_final:
                    nom_dossier = f"{prenom_final}_{nom_final}"
                elif nom_final:
                    nom_dossier = nom_final
                else:
                    nom_dossier = prenom_final
            else:
                # Fallback si aucun texte trouvé
                nom_dossier = f"Inconnu_Page{i+1}_{int(img_y_center)}"

            # Nettoyage final du nom de dossier
            nom_dossier = nettoyer_texte_dossier(nom_dossier)

            # 4. Sauvegarde
            chemin_sous_dossier = os.path.join(output_folder, nom_dossier)
            if not os.path.exists(chemin_sous_dossier):
                os.makedirs(chemin_sous_dossier)
            
            # Extraction image
            pix = fitz.Pixmap(doc, img_info['xref'])
            # Conversion RGB si nécessaire
            if pix.n - pix.alpha < 3:
                pix = fitz.Pixmap(doc, img_info['xref'])
            else:
                pix0 = fitz.Pixmap(fitz.csRGB, pix)
                pix = pix0
            
            nom_fichier_img = f"{nom_dossier}.png"
            pix.save(os.path.join(chemin_sous_dossier, nom_fichier_img))
            print(f"  -> Sauvegardé : {nom_dossier}")
            
            pix = None
            compteur_succes += 1

    print(f"\nTerminé ! {compteur_succes} étudiants traités.")

# --- Lancement ---
nom_fichier_pdf = "Promo2026_1A.pdf"
dossier_sortie = "known_faces"

if __name__ == "__main__":
    if os.path.exists(nom_fichier_pdf):
        extraire_photos_clean(nom_fichier_pdf, dossier_sortie)
    else:
        print(f"Fichier introuvable : {nom_fichier_pdf}")