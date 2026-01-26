import face_recognition
import os
import cv2



known_dir="known_faces"
unknown_dir= "unknown_faces"
tolerance = 0.6
frame_thikness = 3
front_thinkness = 2
Model = "cnn"

print ("loading known faces")

knwon_faces=[]
known_name=[]

for name in os.listdir(known_dir):
    for filename in os.listdir(f"{known_dir}/{name}"):
        image = face_recognition.load_image_file(f"{known_dir}/{name}/{filename}")

        encoding = face_recognition.face_encodings(image)[0]
        known_name.append(encoding)
        knwon_faces.append(name)
        
print("working on unknown faces")

for filename in os.listdir(unknown_dir):
    print(filename)
    image = face_recognition.load_image_file(f"{unknown_dir}/{filename}")
    locations = face_recognition.face_locations(image,model = Model) 
    encoding= face_recognition.face_encodings(image,locations)
    image = cv2.cvtColor(image,cv2.COLOR_RGB2BGR)
    print(f',{len(encoding)} visages trouvés')
    for face_encoding, face_location in zip(encoding,locations):
        results= face_recognition.compare_faces(knwon_faces,face_encoding,tolerance)
        match = None
        if True in results:
            match = known_name[results.index(True)]
            print(f"visage trouvé : {match}")
            
            top__left = (face_location[3], face_location[0])
            bottom_right = (face_location[1],face_location[2])
            
            color= [0,255,0]
            cv2.rectangle(image,top__left, bottom_right,color, frame_thikness)
            
            top__left = (face_location[3], face_location[2])
            bottom_right = (face_location[1],face_location[2]+22)
            
            cv2.rectangle(image,top__left, bottom_right,color, cv2.FILLED)
            cv2.putText(image,match, (face_location[3]+10, face_location[2]+15),cv2.FONT_HERSHEY_SIMPLEX,0.5, (200,220,200),front_thinkness)
            
    cv2.imshow(filename,image)
    cv2.waitKey(10000)
    #cv2.destroyWindow(filename)