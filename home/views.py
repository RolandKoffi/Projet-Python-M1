from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from scipy.spatial import distance
from imutils import face_utils
from home.simple_facerec import SimpleFacerec
import imutils
import dlib
import cv2
import datetime
import os, shutil
import mimetypes
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML


# Create your views here.
@login_required(login_url="/login/")
def index(request):
    
    dossierDormeurs = os.listdir("static/img/")
    liste_img = []
    
    for i in dossierDormeurs:
        liste_img.append(i[:-4])


    context = {'listeDormeurs': liste_img}

    return render(request,'index.html', context)


def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

@login_required(login_url="/login/")
def activer_camera(request):
    sfr = SimpleFacerec()
    sfr.load_encoding_images("static/images/")

    thresh = 0.25
    frame_check = 20
    detect = dlib.get_frontal_face_detector()
    predict = dlib.shape_predictor("home/shape_predictor_68_face_landmarks.dat")  

    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
    cap = cv2.VideoCapture(0)
    flag = 0

    while True:
        ret, frame = cap.read()
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        subjects = detect(gray, 0)


        #Reconaissance
        face_locations, face_names = sfr.detect_known_faces(frame)
        for face_loc, name in zip(face_locations, face_names):
            y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

            cv2.putText(frame, name,(x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 150), 1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 100), 4)


        for subject in subjects:
            shape = predict(gray, subject)
            shape = face_utils.shape_to_np(shape) 
            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            if ear < thresh:
                flag += 1
                #print(flag)

                if flag >= frame_check:
                    
                    if os.path.exists('templates/opencv_file/Dormeurs.txt'):
                        text_file = open('templates/opencv_file/Dormeurs.txt','r')
                        
                    else:
                        text_file = open('templates/opencv_file/Dormeurs.txt', 'x')
                        
                    text_file = open('templates/opencv_file/Dormeurs.txt', 'r')
                    for i in face_names :
                        if i not in text_file.readlines():
                            img_name = "static/img/"+str(i)+".png"
                            cv2.imwrite(img_name, frame)
                            text_file = open('templates/opencv_file/Dormeurs.txt', "a")
                            texte = i
                            text_file.write(str(texte+"\n"))
                            text_file.close()
            else:
                flag = 0
    
        cv2.imshow("Camera dormeurs", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
    
    cap.release()
    cv2.destroyAllWindows()
        
    return redirect("index")


@login_required(login_url="/login/")
def liste_dormeurs(request):
    
    fichier = open('templates/opencv_file/Dormeurs.txt', "r")
    
    dateDuJour = datetime.date.today()
    
    liste_temp = []
    liste = []
    
    for i in fichier.readlines():
        if i not in liste_temp:
            val = i[:-1]
            liste_temp.append(val)
            for j in liste_temp:
                if j not in liste:
                    liste.append(j)
    
    
    html_string = render_to_string('liste_pdf.html', {'liste_dormeurs': liste, 'dateDuJour': dateDuJour})
    
    html = HTML(string=html_string)
    html.write_pdf(target='static/pdf/liste.pdf');
    
    fs = FileSystemStorage('static/pdf')
    with fs.open('liste.pdf') as pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="liste.pdf"'
    
    fichier_pdf = '/static/pdf/liste.pdf'
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = BASE_DIR + fichier_pdf
    path = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filepath)
    response1 = HttpResponse(path, content_type=mime_type)
    response1['Content-Disposition'] = "attachment; filename=%s" % 'liste'
    
    
    return response1




@login_required(login_url="/login/")
def session(request):
    
    if os.path.exists("templates/opencv_file/Dormeurs.txt") and os.path.exists("static/pdf/liste.pdf"):
        os.remove("templates/opencv_file/Dormeurs.txt")
        os.remove("static/pdf/liste.pdf")
    
    folder = 'static/img/'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            pass
    
    return redirect("index")

