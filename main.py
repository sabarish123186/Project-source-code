# main.py
import os
from flask import Flask, render_template, Response, redirect, request, session, abort, url_for
from camera import VideoCamera
from camera2 import VideoCamera2
from camera3 import VideoCamera3
from camera4 import VideoCamera4
import cv2
import csv
from flask_mail import Mail, Message
from flask import send_file
import numpy as np
import shutil
import datetime
import time
import PIL.Image
from PIL import Image
import imagehash
import mysql.connector
from werkzeug.utils import secure_filename
from ultralytics import YOLO

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  charset="utf8",
  database="class_skipper"

)
app = Flask(__name__)
app.secret_key = 'abcdef'

UPLOAD_FOLDER = 'static/upload'
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
##email
mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "rnd1024.64@gmail.com",
    "MAIL_PASSWORD": "kazxlklvfrvgncse"
}

app.config.update(mail_settings)
mail = Mail(app)
#######


@app.route('/')
def index():
    ff=open("det.txt","w")
    ff.write("1")
    ff.close()

    ff1=open("photo.txt","w")
    ff1.write("1")
    ff1.close()

    ff11=open("img.txt","w")
    ff11.write("1")
    ff11.close()

    ff=open("person.txt","w")
    ff.write("")
    ff.close()

    ff=open("static/sms2.txt","w")
    ff.write("1")
    ff.close()
            
    return render_template('web/index.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg=""
    if request.method=='POST':
        uname=request.form['uname']
        pwd=request.form['pass']
        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM admin WHERE username = %s AND password = %s', (uname, pwd))
        account = cursor.fetchone()
        if account:
            #session['loggedin'] = True
            #session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('admin'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html',msg=msg)

@app.route('/login_hod', methods=['GET', 'POST'])
def login_hod():
    msg=""
    if request.method=='POST':
        uname=request.form['uname']
        pwd=request.form['pass']
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM staff WHERE uname = %s AND pass = %s && stype='HOD'", (uname, pwd))
        account = cursor.fetchone()
        if account:
            #session['loggedin'] = True
            session['username'] = uname
            # Redirect to home page
            return redirect(url_for('hod_home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login_hod.html',msg=msg)

@app.route('/login_staff', methods=['GET', 'POST'])
def login_staff():
    msg=""
    if request.method=='POST':
        uname=request.form['uname']
        pwd=request.form['pass']
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM staff WHERE uname = %s AND pass = %s && stype='Staff'", (uname, pwd))
        account = cursor.fetchone()
        if account:
            #session['loggedin'] = True
            session['username'] = uname
            # Redirect to home page
            return redirect(url_for('staff_home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login_staff.html',msg=msg)

@app.route('/admin',methods=['POST','GET'])
def admin():
    data=[]
    act=request.args.get("act")
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM register")
    data = mycursor.fetchall()

    mycursor.execute("SELECT * FROM department")
    value1 = mycursor.fetchall()

    mycursor.execute("SELECT distinct(year) FROM register")
    value2 = mycursor.fetchall()

    if request.method=='POST':
        dept=request.form['dept']
        year=request.form['year']
        if dept!="" and year!="":
            mycursor.execute("SELECT * FROM register where dept=%s && year=%s",(dept,year))
            data = mycursor.fetchall()
    else:
        mycursor.execute("SELECT * FROM register")
        data = mycursor.fetchall()

    ###
    if act=="del":
        did=request.args.get("did")

        mycursor.execute("delete from register where id=%s",(did,))
        mydb.commit()
        return redirect(url_for('admin')) 
    ###
        
    return render_template('admin.html',data=data,value1=value1,value2=value2)

@app.route('/admin2',methods=['POST','GET'])
def admin2():
    act=request.args.get("act")
    mycursor = mydb.cursor()
    
    mycursor.execute("SELECT * FROM train_data")
    value = mycursor.fetchall()

    ###
    if act=="del":
        did=request.args.get("did")

        mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(did,))
        cn = mycursor.fetchone()[0]
        if cn>0:
            mycursor.execute("SELECT * FROM vt_face where vid=%s",(did,))
            dd = mycursor.fetchall()
            for ds in dd:
                os.remove("static/frame/"+ds[2])
                os.remove("images_db/"+ds[2])

            mycursor.execute("delete from vt_face where vid=%s",(did,))
            mydb.commit()
                
        
        mycursor.execute("delete from train_data where id=%s",(did,))
        mydb.commit()
        return redirect(url_for('admin')) 
    ###
        
    return render_template('admin2.html',value=value)


@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')




@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    #import student
    msg=""
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM department")
    value1 = mycursor.fetchall()
    
    if request.method=='POST':
        name=request.form['name']
        mobile=request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        aadhar=request.form['aadhar']
        regno=request.form['regno']
        dept=request.form['dept']
        year=request.form['year']
        parent_mob=request.form['parent_mob']
        semester=request.form['semester']
        gender=request.form['gender']

        mycursor.execute("SELECT count(*) FROM register where regno=%s",(regno,))
        cnt = mycursor.fetchone()[0]

        if cnt==0:
            mycursor.execute("SELECT max(id)+1 FROM register")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid=1

                
            sql = "INSERT INTO register(id,name,mobile,email,address,aadhar,regno,dept,year,parent_mob,semester,gender) VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s,%s)"
            val = (maxid,name,mobile,email,address,aadhar,regno,dept,year,parent_mob,semester,gender)
            mycursor.execute(sql, val)
            mydb.commit()            
            return redirect(url_for('add_photo',vid=maxid)) 
        else:        
      
            msg='fail'

            
    return render_template('add_student.html',msg=msg,value1=value1)

#
def prepare_data():
    DATASET_PATH = "dataset/"  
    encodings = []
    names = []

    for student in os.listdir(DATASET_PATH):
        for img in os.listdir(os.path.join(DATASET_PATH, student)):
            image = face_recognition.load_image_file(
                os.path.join(DATASET_PATH, student, img)
            )
            face_enc = face_recognition.face_encodings(image)
            if face_enc:
                encodings.append(face_enc[0])
                names.append(student)

    # Save encodings
    with open("face_encodings.pkl", "wb") as f:
        pickle.dump((encodings, names), f)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    vid=request.args.get("vid")
    msg=""
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM department")
    value1 = mycursor.fetchall()

    mycursor.execute("SELECT * FROM register where id=%s",(vid,))
    data = mycursor.fetchone()
    
    if request.method=='POST':
        name=request.form['name']
        mobile=request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        aadhar=request.form['aadhar']
        
        dept=request.form['dept']
        year=request.form['year']
        parent_mob=request.form['parent_mob']
        semester=request.form['semester']
        gender=request.form['gender']
        
        mycursor.execute("update register set name=%s,mobile=%s,email=%s,address=%s,aadhar=%s,dept=%s,year=%s,parent_mob=%s,semester=%s,gender=%s where id=%s",(name,mobile,email,address,aadhar,dept,year,parent_mob,semester,gender,vid))
        mydb.commit()

        return redirect(url_for('admin')) 

            
    return render_template('edit.html',msg=msg,value1=value1,data=data)

@app.route('/add_staff',methods=['POST','GET'])
def add_staff():
    msg=""
    act=""
    mess=""
    email=""
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM department")
    value1 = mycursor.fetchall()

    mycursor.execute("SELECT distinct(year) FROM register")
    value2 = mycursor.fetchall()
    
    if request.method=='POST':
        
        uname=request.form['uname']
        name=request.form['name']       
        mobile=request.form['mobile']
        email=request.form['email']
        location=request.form['location']        
        pass1=request.form['pass']
        stype=request.form['stype']
        dept=request.form['dept']
       
        now = datetime.datetime.now()
        rdate=now.strftime("%d-%m-%Y")
        mycursor = mydb.cursor()

        mycursor.execute("SELECT count(*) FROM staff where uname=%s",(uname, ))
        cnt = mycursor.fetchone()[0]
        if cnt==0:
            mycursor.execute("SELECT max(id)+1 FROM staff")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid=1
            sql = "INSERT INTO staff(id, name, mobile, email, location,  uname, pass,stype,rdate,dept) VALUES (%s, %s, %s, %s, %s, %s, %s,%s,%s,%s)"
            val = (maxid, name, mobile, email, location, uname, pass1,stype,rdate,dept)
            
            
            mycursor.execute(sql, val)
            mydb.commit()

            msg="success"
            mess="Dear "+name+", Staff ID: "+uname+" ("+stype+"), Password: "+pass1
            print(mycursor.rowcount, "record inserted.")
           
        else:
            msg="fail"
            
    return render_template('add_staff.html',msg=msg,act=act,value1=value1,value2=value2,mess=mess,email=email)


@app.route('/add_dept',methods=['POST','GET'])
def add_dept():
    msg=""
    act=""
    mess=""
    email=""
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM department")
    value1 = mycursor.fetchall()

    mycursor.execute("SELECT distinct(year) FROM register")
    value2 = mycursor.fetchall()
    
    if request.method=='POST':
 
        dept=request.form['dept']
       


        mycursor.execute("SELECT count(*) FROM department where department=%s",(dept, ))
        cnt = mycursor.fetchone()[0]
        if cnt==0:
            mycursor.execute("SELECT max(id)+1 FROM department")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid=1
            sql = "INSERT INTO department(id,department) VALUES (%s, %s)"
            val = (maxid, dept)
            
            
            mycursor.execute(sql, val)
            mydb.commit()
            return redirect(url_for('view_dept')) 
           
        else:
            msg="fail"
            
    return render_template('add_dept.html',msg=msg,act=act)

@app.route('/update',methods=['POST','GET'])
def update():
    msg=""
    act=""
    mess=""
    email=""
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM admin where username='admin'")
    data = mycursor.fetchone()

   
    if request.method=='POST':
 
        mobile=request.form['mobile']
        mycursor.execute("update admin set mobile=%s where username='admin'",(mobile,))
        mydb.commit()
        msg="success"
            
    return render_template('update.html',msg=msg,act=act,data=data)

@app.route('/add_table', methods=['GET', 'POST'])
def add_table():
    #import student
    msg=""
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM staff")
    sdat = mycursor.fetchall()

    mycursor.execute("SELECT * FROM department")
    mdat = mycursor.fetchall()
        
    
    if request.method=='POST':
        dept=request.form['dept']
        staff=request.form['staff']
        semester=request.form['semester']
        subject=request.form['subject']
        
        hour1=request.form['t1']
        minute1=request.form['t2']
        hour2=request.form['t3']
        minute2=request.form['t4']
        period=request.form['period']

        mycursor.execute("SELECT count(*) FROM timetable where dept=%s && semester=%s && period=%s",(dept,semester,period))
        cnt = mycursor.fetchone()[0]
        if cnt==0:
            
            mycursor.execute("SELECT max(id)+1 FROM timetable")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid=1
            sql = "INSERT INTO timetable(id,dept,staff,semester,subject,hour1,minute1,hour2,minute2,period) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            val = (maxid, dept,staff,semester,subject,hour1,minute1,hour2,minute2,period)
            mycursor.execute(sql, val)
            mydb.commit()
            
            msg="success"

            
    return render_template('add_table.html',msg=msg,sdat=sdat,mdat=mdat)

@app.route('/edit_table', methods=['GET', 'POST'])
def edit_table():
    tid=request.args.get("tid")
    msg=""
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM staff")
    sdat = mycursor.fetchall()

    mycursor.execute("SELECT * FROM department")
    mdat = mycursor.fetchall()

    mycursor.execute("SELECT * FROM timetable where id=%s",(tid,))
    tdata = mycursor.fetchone()
        
    
    if request.method=='POST':
        dept=request.form['dept']
        staff=request.form['staff']
        semester=request.form['semester']
        subject=request.form['subject']
        
        hour1=request.form['t1']
        minute1=request.form['t2']
        hour2=request.form['t3']
        minute2=request.form['t4']
        period=request.form['period']
        
        mycursor.execute("update timetable set dept=%s,staff=%s,semester=%s,subject=%s,hour1=%s,minute1=%s,hour2=%s,minute2=%s,period=%s where id=%s",(dept,staff,semester,subject,hour1,minute1,hour2,minute2,period,tid))
        mydb.commit()
        msg="success"

            
    return render_template('edit_table.html',msg=msg,sdat=sdat,mdat=mdat,tdata=tdata)

@app.route('/view_dept', methods=['GET', 'POST'])
def view_dept():
    #import student
    msg=""
    act=request.args.get("act")
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM department")
    data = mycursor.fetchall()

    if act=="del":
        did=request.args.get("did")
        mycursor.execute("delete from department where id=%s",(did,))
        mydb.commit()
        msg="ok"

    return render_template('view_dept.html',msg=msg,data=data)

@app.route('/view_staff', methods=['GET', 'POST'])
def view_staff():
    #import student
    msg=""
    act=request.args.get("act")
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM staff")
    data = mycursor.fetchall()

    if act=="del":
        did=request.args.get("did")
        mycursor.execute("delete from staff where id=%s",(did,))
        mydb.commit()
        msg="ok"

    return render_template('view_staff.html',msg=msg,data=data)


@app.route('/view_table', methods=['GET', 'POST'])
def view_table():
    #import student
    msg=""
    act=request.args.get("act")
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM timetable")
    data = mycursor.fetchall()
    if act=="del":
        did=request.args.get("did")
        mycursor.execute("delete from timetable where id=%s",(did,))
        mydb.commit()
        return redirect(url_for('view_table')) 

    return render_template('view_table.html',msg=msg,act=act,data=data)


def getImagesAndLabels(path):

    
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml");

    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
    faceSamples=[]
    ids = []

    for imagePath in imagePaths:

        PIL_img = Image.open(imagePath).convert('L') # convert it to grayscale
        img_numpy = np.array(PIL_img,'uint8')

        id = int(os.path.split(imagePath)[-1].split(".")[1])
        faces = detector.detectMultiScale(img_numpy)

        for (x,y,w,h) in faces:
            faceSamples.append(img_numpy[y:y+h,x:x+w])
            ids.append(id)

    return faceSamples,ids


@app.route('/add_photo',methods=['POST','GET'])
def add_photo():
    vid = request.args.get('vid')
    ff1=open("photo.txt","w")
    ff1.write("2")
    ff1.close()

    #ff2=open("mask.txt","w")
    #ff2.write("face")
    #ff2.close()
    act = request.args.get('act')

    cursor = mydb.cursor()
    
    cursor.execute("SELECT * FROM register where id=%s",(vid,))
    value = cursor.fetchone()
    name=value[1]
    
    ff=open("user.txt","w")
    ff.write(name)
    ff.close()

    ff=open("user1.txt","w")
    ff.write(vid)
    ff.close()
    

    
    
    if request.method=='POST':
        vid=request.form['vid']
        fimg="v"+vid+".jpg"
        

        cursor.execute('delete from vt_face WHERE vid = %s', (vid, ))
        mydb.commit()

        

        ff=open("det.txt","r")
        v=ff.read()
        ff.close()
        vv=int(v)
        v1=vv-1
        vface1="User."+vid+"."+str(v1)+".jpg"
        i=2
        while i<vv:
            
            cursor.execute("SELECT max(id)+1 FROM vt_face")
            maxid = cursor.fetchone()[0]
            if maxid is None:
                maxid=1
            vface="User."+vid+"."+str(i)+".jpg"
            sql = "INSERT INTO vt_face(id, vid, vface) VALUES (%s, %s, %s)"
            val = (maxid, vid, vface)
            print(val)
            cursor.execute(sql,val)
            mydb.commit()
            i+=1

        
            
        cursor.execute('update register set fimg=%s WHERE id = %s', (vface1, vid))
        mydb.commit()
        shutil.copy('static/faces/f1.jpg', 'static/photo/'+vface1)

        
        ##########
        
        ##Training face
        # Path for face image database
        path = 'dataset'

        recognizer = cv2.face.LBPHFaceRecognizer_create()

        # function to get the images and label data
        

        print ("\n [INFO] Training faces. It will take a few seconds. Wait ...")
        faces,ids = getImagesAndLabels(path)
        recognizer.train(faces, np.array(ids))

        # Save the model into trainer/trainer.yml
        recognizer.write('trainer/trainer.yml') # recognizer.save() worked on Mac, but not on Pi

        # Print the numer of faces trained and end program
        print("\n [INFO] {0} faces trained. Exiting Program".format(len(np.unique(ids))))






        #################################################
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM vt_face where vid=%s",(vid, ))
        dt = cursor.fetchall()
        for rs in dt:
            ##Preprocess
            path="static/frame/"+rs[2]
            path2="static/process1/"+rs[2]
            mm2 = PIL.Image.open(path).convert('L')
            rz = mm2.resize((200,200), PIL.Image.ANTIALIAS)
            rz.save(path2)
            
            '''img = cv2.imread(path2) 
            dst = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 15)
            path3="static/process2/"+rs[2]
            cv2.imwrite(path3, dst)'''
            #noice
            img = cv2.imread('static/process1/'+rs[2]) 
            dst = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 15)
            fname2='ns_'+rs[2]
            cv2.imwrite("static/process1/"+fname2, dst)
            ######
            ##bin
            image = cv2.imread('static/process1/'+rs[2])
            original = image.copy()
            kmeans = kmeans_color_quantization(image, clusters=4)

            # Convert to grayscale, Gaussian blur, adaptive threshold
            gray = cv2.cvtColor(kmeans, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (3,3), 0)
            thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,21,2)
            
            # Draw largest enclosing circle onto a mask
            mask = np.zeros(original.shape[:2], dtype=np.uint8)
            cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
            for c in cnts:
                ((x, y), r) = cv2.minEnclosingCircle(c)
                cv2.circle(image, (int(x), int(y)), int(r), (36, 255, 12), 2)
                cv2.circle(mask, (int(x), int(y)), int(r), 255, -1)
                break
            
            # Bitwise-and for result
            result = cv2.bitwise_and(original, original, mask=mask)
            result[mask==0] = (0,0,0)

            
            ###cv2.imshow('thresh', thresh)
            ###cv2.imshow('result', result)
            ###cv2.imshow('mask', mask)
            ###cv2.imshow('kmeans', kmeans)
            ###cv2.imshow('image', image)
            ###cv2.waitKey()

            cv2.imwrite("static/process1/bin_"+rs[2], thresh)
            

            ###RPN - Segment
            img = cv2.imread('static/process1/'+rs[2])
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            ret, thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

            
            kernel = np.ones((3,3),np.uint8)
            opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)

            # sure background area
            sure_bg = cv2.dilate(opening,kernel,iterations=3)

            # Finding sure foreground area
            dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
            ret, sure_fg = cv2.threshold(dist_transform,0.7*dist_transform.max(),255,0)

            # Finding unknown region
            sure_fg = np.uint8(sure_fg)
            segment = cv2.subtract(sure_bg,sure_fg)
            img = Image.fromarray(img)
            segment = Image.fromarray(segment)
            path3="static/process2/fg_"+rs[2]
            segment.save(path3)
            ####
            img = cv2.imread('static/process2/fg_'+rs[2])
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            ret, thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

            
            kernel = np.ones((3,3),np.uint8)
            opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)

            # sure background area
            sure_bg = cv2.dilate(opening,kernel,iterations=3)

            # Finding sure foreground area
            dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
            ret, sure_fg = cv2.threshold(dist_transform,0.7*dist_transform.max(),255,0)

            # Finding unknown region
            sure_fg = np.uint8(sure_fg)
            segment = cv2.subtract(sure_bg,sure_fg)
            img = Image.fromarray(img)
            segment = Image.fromarray(segment)
            path3="static/process2/fg_"+rs[2]
            segment.save(path3)
            '''
            img = cv2.imread(path2)
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            ret, thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

            # noise removal
            kernel = np.ones((3,3),np.uint8)
            opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)

            # sure background area
            sure_bg = cv2.dilate(opening,kernel,iterations=3)

            # Finding sure foreground area
            dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
            ret, sure_fg = cv2.threshold(dist_transform,0.7*dist_transform.max(),255,0)

            # Finding unknown region
            sure_fg = np.uint8(sure_fg)
            segment = cv2.subtract(sure_bg,sure_fg)
            img = Image.fromarray(img)
            segment = Image.fromarray(segment)
            path3="static/process2/"+rs[2]
            segment.save(path3)
            '''
            #####
            image = cv2.imread(path2)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edged = cv2.Canny(gray, 50, 100)
            image = Image.fromarray(image)
            edged = Image.fromarray(edged)
            path4="static/process3/"+rs[2]
            edged.save(path4)
            ##
        ###
        cursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
        cnt = cursor.fetchone()[0]
        
        return redirect(url_for('view_photo',vid=vid,act='success'))
        
    
    cursor.execute("SELECT * FROM register")
    data = cursor.fetchall()
    return render_template('add_photo.html',data=data, vid=vid)

def kmeans_color_quantization(image, clusters=8, rounds=1):
    h, w = image.shape[:2]
    samples = np.zeros([h*w,3], dtype=np.float32)
    count = 0

    for x in range(h):
        for y in range(w):
            samples[count] = image[x][y]
            count += 1

    compactness, labels, centers = cv2.kmeans(samples,
            clusters, 
            None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10000, 0.0001), 
            rounds, 
            cv2.KMEANS_RANDOM_CENTERS)

    centers = np.uint8(centers)
    res = centers[labels.flatten()]
    return res.reshape((image.shape))

@app.route('/view_photo',methods=['POST','GET'])
def view_photo():
    ff1=open("photo.txt","w")
    ff1.write("1")
    ff1.close()
    vid=""
    value=[]
    if request.method=='GET':
        vid = request.args.get('vid')
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM vt_face where vid=%s",(vid, ))
        value = mycursor.fetchall()

    if request.method=='POST':
        print("Training")
        vid=request.form['vid']
        
        #shutil.copy('static/img/11.png', 'static/process4/'+rs[2])
       
        #return redirect(url_for('view_photo1',vid=vid))
        
    return render_template('view_photo.html', result=value,vid=vid)



@app.route('/pro1',methods=['POST','GET'])
def pro1():
    s1=""
    vid = request.args.get('vid')
    act = request.args.get('act')
    value=[]
    
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
    cnt = mycursor.fetchone()[0]

    if act is None:
        act=1
        
    act1=int(act)-1
    act2=int(act)+1
    act3=str(act2)
    
    n=10
    if act1<n:
        s1="1"
        mycursor.execute("SELECT * FROM vt_face where vid=%s limit %s,1",(vid, act1))
        value = mycursor.fetchone()
    else:
        s1="2"

    
    return render_template('pro1.html', value=value,vid=vid, act=act3,s1=s1)

@app.route('/pro2',methods=['POST','GET'])
def pro2():
    s1=""
    vid = request.args.get('vid')
    act = request.args.get('act')
    value=[]
    
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
    cnt = mycursor.fetchone()[0]

    if act is None or act=='0':
        act=1
        
    act1=int(act)-1
    act2=int(act)+1
    act3=str(act2)
    
    n=10
    if act1<n:
        s1="1"
        mycursor.execute("SELECT * FROM vt_face where vid=%s limit %s,1",(vid, act1))
        value = mycursor.fetchone()
    else:
        s1="2"

    
    return render_template('pro2.html', value=value,vid=vid, act=act3,s1=s1)

@app.route('/pro3',methods=['POST','GET'])
def pro3():
    s1=""
    vid = request.args.get('vid')
    act = request.args.get('act')
    value=[]
    
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
    cnt = mycursor.fetchone()[0]

    if act is None:
        act=1
        
    act1=int(act)-1
    act2=int(act)+1
    act3=str(act2)
    
    n=10
    if act1<n:
        s1="1"
        mycursor.execute("SELECT * FROM vt_face where vid=%s limit %s,1",(vid, act1))
        value = mycursor.fetchone()
    else:
        s1="2"

    
    return render_template('pro3.html', value=value,vid=vid, act=act3,s1=s1)

@app.route('/pro4',methods=['POST','GET'])
def pro4():
    s1=""
    vid = request.args.get('vid')
    act = request.args.get('act')
    value=[]
    
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
    cnt = mycursor.fetchone()[0]

    if act is None:
        act=1
        
    act1=int(act)-1
    act2=int(act)+1
    act3=str(act2)
    
    n=10
    if act1<n:
        s1="1"
        mycursor.execute("SELECT * FROM vt_face where vid=%s limit %s,1",(vid, act1))
        value = mycursor.fetchone()
    else:
        s1="2"

    
    return render_template('pro4.html', value=value,vid=vid, act=act3,s1=s1)

@app.route('/pro5',methods=['POST','GET'])
def pro5():
    s1=""
    vid = request.args.get('vid')
    act = request.args.get('act')
    value=[]
    
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
    cnt = mycursor.fetchone()[0]

    if act is None:
        act=1
        
    act1=int(act)-1
    act2=int(act)+1
    act3=str(act2)
    
    n=10
    if act1<n:
        s1="1"
        mycursor.execute("SELECT * FROM vt_face where vid=%s limit %s,1",(vid, act1))
        value = mycursor.fetchone()
    else:
        s1="2"

    
    return render_template('pro5.html', value=value,vid=vid, act=act3,s1=s1)

@app.route('/pro6',methods=['POST','GET'])
def pro6():
    s1=""
    vid = request.args.get('vid')
    act = request.args.get('act')
    value=[]
    
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
    cnt = mycursor.fetchone()[0]

    if act is None:
        act=1
        
    act1=int(act)-1
    act2=int(act)+1
    act3=str(act2)
    
    n=10
    if act1<n:
        s1="1"
        mycursor.execute("SELECT * FROM vt_face where vid=%s limit %s,1",(vid, act1))
        value = mycursor.fetchone()
    else:
        s1="2"

    
    return render_template('pro6.html', value=value,vid=vid, act=act3,s1=s1)

@app.route('/pro7',methods=['POST','GET'])
def pro7():
    s1=""
    vid = request.args.get('vid')
    act = request.args.get('act')
    value=[]
    
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT count(*) FROM vt_face where vid=%s",(vid, ))
    cnt = mycursor.fetchone()[0]

    if act is None:
        act=1
        
    act1=int(act)-1
    act2=int(act)+1
    act3=str(act2)
    
    n=10
    if act1<n:
        s1="1"
        mycursor.execute("SELECT * FROM vt_face where vid=%s limit %s,1",(vid, act1))
        value = mycursor.fetchone()
    else:
        s1="2"

    
    return render_template('pro7.html', value=value,vid=vid, act=act3,s1=s1)

#Live Video Capture
def live_camera(name):
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")

    cursor.execute("""
        SELECT * FROM attendance WHERE name=? AND date=?
    """, (name, date))

    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO attendance VALUES (?,?,?,?,?)
        """, (name, name, date, time, "Present"))
        conn.commit()

    conn.close()


    # Live camera
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, conf=0.5)

        for r in results:
            for box in r.boxes.xyxy:
                x1, y1, x2, y2 = map(int, box)
                face = frame[y1:y2, x1:x2]

                if face.size == 0:
                    continue

                rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                enc = face_recognition.face_encodings(rgb_face)

                name = "Unknown"

                if enc:
                    matches = face_recognition.compare_faces(
                        known_encodings, enc[0], tolerance=0.5
                    )
                    distances = face_recognition.face_distance(
                        known_encodings, enc[0]
                    )

                    if True in matches:
                        idx = np.argmin(distances)
                        name = known_names[idx]
                        mark_attendance(name)

                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, name, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("College Attendance Surveillance", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break


#Face Detection
def face_detect():
    # Load YOLOv8 face detection model
    model = YOLO("yolov8n-face.pt")

    # Open webcam
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run YOLOv8 inference
        results = model(frame, conf=0.5)

        for result in results:
            boxes = result.boxes.xyxy
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2),
                              (0, 255, 0), 2)
                cv2.putText(frame, "Face",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)

        cv2.imshow("YOLOv8 Face Detection", frame)

def face_recognize():
    for student in os.listdir(DATASET_PATH):
        for img in os.listdir(os.path.join(DATASET_PATH, student)):
            image = face_recognition.load_image_file(
                os.path.join(DATASET_PATH, student, img)
            )
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(student)

    with open("face_db.pkl", "wb") as f:
        pickle.dump((known_encodings, known_names), f)
    
@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
    
    cam1=request.args.get("cam1")
    cam2=request.args.get("cam2")
    cam3=request.args.get("cam3")
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM admin")
    value = mycursor.fetchone()

    ff=open("static/sms.txt","w")
    ff.write("1")
    ff.close()

    ff=open("static/cam1.txt","w")
    ff.write("")
    ff.close()
    ff=open("static/cam2.txt","w")
    ff.write("")
    ff.close()
    ff=open("static/cam3.txt","w")
    ff.write("")
    ff.close()

    
    now = datetime.datetime.now()
    rdate=now.strftime("%d-%m-%Y")
        
    mycursor.execute('SELECT count(*) FROM attendance where rdate=%s',(rdate,))
    cnt = mycursor.fetchone()[0]

    if cnt==0:
        
        mycursor.execute('SELECT * FROM register')
        drow = mycursor.fetchall()

        for rw in drow:
            regno=rw[13]
            mycursor.execute("SELECT max(id)+1 FROM attendance")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid=1
            
            sql = "INSERT INTO attendance(id, regno, rdate, attendance, mask_st) VALUES (%s, %s, %s, %s, %s)"
            val = (maxid, regno, rdate, 'Absent', '-')
            print(sql)
            mycursor.execute(sql, val)
            mydb.commit()
            

    return render_template('monitor.html',cam1=cam1,cam2=cam2,cam3=cam3,value=value)

@app.route('/process1', methods=['GET', 'POST'])
def process1():
    s1=""
    uid=""
    unst=""
    ff=open("static/cam1.txt","r")
    cam1=ff.read()
    ff.close()

    if cam1=="":
        s1="1"

        ff=open("static/info.txt","r")
        unst=ff.read()
        ff.close()
    
    else:
        uid=cam1
        s1="2"

    return render_template('process1.html',uid=uid,s1=s1,unst=unst)

@app.route('/process11', methods=['GET', 'POST'])
def process11():
    s1=""
    uid=request.args.get("uid")
    st=""
    staff=""
    sms2=""
    mess2=""
    mobile2=""
    tdata2=[]
    tid=0

    ff=open("static/info.txt","r")
    unst=ff.read()
    ff.close()

    ff=open("static/sms2.txt","r")
    ss2=ff.read()
    ff.close()
        
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM admin where username='admin'")
    adata = mycursor.fetchone()
    camera=adata[2]
    mobile2=str(adata[5])
   
        

    if uid=="":
        st="2"
        mycursor.execute("SELECT max(id)+1 FROM detect_unknown")
        maxid = mycursor.fetchone()[0]
        if maxid is None:
            maxid=1

        fn="d"+str(maxid)+".jpg"
        shutil.copy("static/faces/f1.jpg","static/unknown/"+fn)
        
        sql = "INSERT INTO detect_unknown(id,camera,face_img) VALUES (%s, %s, %s)"
        val = (maxid, camera,fn)
        
        mycursor.execute(sql, val)
        mydb.commit()

        ss1=int(ss2)+1
        if ss1<=2:
            sms2="1"
            mess2="Unknown Person"
            ff=open("static/sms2.txt","w")
            ff.write(str(ss1))
            ff.close()
    else:
        
        mycursor.execute("SELECT * FROM register where id=%s",(uid,))
        value = mycursor.fetchone()
        dept1=value[6]
        regno=value[13]
        semester=value[15]
        period=0

        mycursor.execute("SELECT count(*) FROM timetable where dept=%s && semester=%s",(dept1,semester))
        cnt = mycursor.fetchone()[0]
        if cnt>0:
            mycursor.execute("SELECT * FROM timetable where dept=%s && semester=%s",(dept1,semester))
            tdata1 = mycursor.fetchall()

            for tdata in tdata1:
                dept2=tdata[1]
                mycursor.execute("SELECT * FROM staff where uname=%s",(tdata[2],))
                sdata = mycursor.fetchone()
                staff=sdata[1]
                

                now = datetime.datetime.now()
                rdate=now.strftime("%d-%m-%Y")

                t = time.localtime()
                rtime = time.strftime("%H", t)
                rmin = time.strftime("%M", t)
                rh=int(rtime)
                rm=int(rmin)

                dh=int(tdata[5])
                dm=int(tdata[6])

                dh2=int(tdata[7])
                dm2=int(tdata[8])
                print("##")
                print(dh)
                print(dm)
                print(dh2)
                print(dm2)
                

                print("ctime")
                print(rh)
                print(rm)

                ######check time####
                x=0
                if dh<=rh and rh<=dh2:
                    if dh==dh2:
                        if dm<=rm and rm<=dm2:
                            x+=1
                            period=tdata[9]
                            tid=tdata[0]
                            break

                    elif dh==rh:
                        if dm<rm:
                            x+=1
                            period=tdata[9]
                            tid=tdata[0]
                            break

                    elif dh<rh and rh<dh2:
                        if rm<60:
                            x+=1
                            period=tdata[9]
                            tid=tdata[0]
                            break
                    elif rh==dh2:
                        if rm<=dm2:
                            x+=1
                            period=tdata[9]
                            tid=tdata[0]
                            break

                print("x")
                print(x)

            mycursor.execute("SELECT * FROM timetable where id=%s",(tid,))
            tdata2 = mycursor.fetchone()   
            #############      
            if x>0 and dept1==dept2:
                st="1"
                if period==1:
                    mycursor.execute("update attendance set p1=1 where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()
                elif period==2:
                    mycursor.execute("update attendance set p2=1 where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()
                elif period==3:
                    mycursor.execute("update attendance set p3=1 where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()
                elif period==4:
                    mycursor.execute("update attendance set p4=1 where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()
                elif period==1:
                    mycursor.execute("update attendance set p5=1 where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()

                mycursor.execute("SELECT * FROM attendance where regno=%s && rdate=%s",(regno,rdate))
                adata = mycursor.fetchone()
                att=adata[5]+adata[6]+adata[7]+adata[8]+adata[9]
                if att==5:
                    mycursor.execute("update attendance set attendance='Full Day Present' where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()
                elif att>=3:
                    mycursor.execute("update attendance set attendance='Half Day Present' where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()
                else:
                    mycursor.execute("update attendance set attendance='Absent' where regno=%s && rdate=%s",(regno,rdate))
                    mydb.commit()

                ff=open("static/cam1.txt","w")
                ff.write("")
                ff.close()
            else:
                st="3"
    
    return render_template('process11.html',uid=uid,tdata=tdata,tdata2=tdata2,value=value,st=st,staff=staff,unst=unst,sms2=sms2,mobile2=mobile2,mess2=mess2)

####
@app.route('/process2', methods=['GET', 'POST'])
def process2():
    s1=""
    uid=""
    ff=open("static/cam2.txt","r")
    cam1=ff.read()
    ff.close()

    if cam1=="":
        s1="1"
    else:
        uid=cam1
        s1="2"

    return render_template('process2.html',uid=uid,s1=s1)

@app.route('/process22', methods=['GET', 'POST'])
def process22():
    s1=""
    uid=request.args.get("uid")
    st=""
    staff=""
    sms=""
    mobile=""
    mess=""

    sms2=""
    mess2=""
    mobile2=""

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM admin where username='admin'")
    adata = mycursor.fetchone()
    camera=adata[3]
    mobile2=str(adata[5])
        
    ff=open("static/sms.txt","r")
    ss=ff.read()
    ff.close()

    ff=open("static/sms2.txt","r")
    ss2=ff.read()
    ff.close()

    ff=open("static/info.txt","r")
    unst=ff.read()
    ff.close()

    if unst=="":
        s=1
    else:
        mycursor.execute("SELECT max(id)+1 FROM detect_unknown")
        maxid = mycursor.fetchone()[0]
        if maxid is None:
            maxid=1

        fn="d"+str(maxid)+".jpg"
        shutil.copy("static/faces/f1.jpg","static/unknown/"+fn)
        
        sql = "INSERT INTO detect_unknown(id,camera,face_img) VALUES (%s, %s, %s)"
        val = (maxid, camera,fn)
        
        mycursor.execute(sql, val)
        mydb.commit()

        ss1=int(ss2)+1
        if ss1<=4:
            sms2="1"
            mess2="Unknown Person"
            ff=open("static/sms2.txt","w")
            ff.write(str(ss1))
            ff.close()
    
    if uid=="":
        s=1
    else:

        
        
        mycursor.execute("SELECT * FROM register where id=%s",(uid,))
        value = mycursor.fetchone()
        dept1=value[6]
        regno=value[13]
        name=value[1]
        
        mycursor.execute("SELECT * FROM timetable where id=1")
        tdata = mycursor.fetchone()
        dept2=tdata[1]
        mycursor.execute("SELECT * FROM staff where uname=%s",(tdata[2],))
        sdata = mycursor.fetchone()
        staff=sdata[1]

        mycursor.execute("SELECT * FROM staff where dept=%s && stype='HOD'",(dept2,))
        hdata = mycursor.fetchone()
        mobile=hdata[2]

        now = datetime.datetime.now()
        rdate=now.strftime("%d-%m-%Y")

        t = time.localtime()
        rtime = time.strftime("%H", t)
        rmin = time.strftime("%M", t)
        rh=int(rtime)
        rm=int(rmin)

        dh=int(tdata[5])
        dm=int(tdata[6])

        dh2=int(tdata[7])
        dm2=int(tdata[8])

        print("ctime")
        print(rh)
        print(rm)

        ######check time####
        x=0
        if dh<=rh and rh<=dh2:
            if dh==dh2:
                if dm<=rm and rm<=dm2:
                    x+=1

            elif dh==rh:
                if dm<rm:
                    x+=1

            elif dh<rh and rh<dh2:
                if rm<60:
                    x+=1
            elif rh==dh2:
                if rm<=dm2:
                    x+=1

        print("x")
        print(x)
        #############      
        if x>0 and dept1==dept2:
            st="1"
            
            mycursor.execute("SELECT max(id)+1 FROM detect_class_skipper")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid=1

            fn="d"+str(maxid)+".jpg"
            shutil.copy("static/faces/f1.jpg","static/detect/"+fn)
            
            sql = "INSERT INTO detect_class_skipper(id, regno, name, camera, face_img, dept) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (maxid, regno, name, camera, fn, dept1)
            print(sql)
            mycursor.execute(sql, val)
            mydb.commit()

            mess="Regno: "+regno+", "+name+", Skipt the Class"

            ff=open("static/cam2.txt","w")
            ff.write("")
            ff.close()

            ss1=int(ss)+1
            if ss1<=4:
                sms="1"
                ff=open("static/sms.txt","w")
                ff.write(str(ss1))
                ff.close()
                
    
    return render_template('process22.html',uid=uid,tdata=tdata,value=value,st=st,staff=staff,sms=sms,mobile=mobile,mess=mess,unst=unst,sms2=sms2,mobile2=mobile2,mess2=mess2)

####
@app.route('/process3', methods=['GET', 'POST'])
def process3():
    s1=""
    uid=""
    ff=open("static/cam3.txt","r")
    cam1=ff.read()
    ff.close()

    if cam1=="":
        s1="1"
    else:
        uid=cam1
        s1="2"

    return render_template('process3.html',uid=uid,s1=s1)

@app.route('/process33', methods=['GET', 'POST'])
def process33():
    s1=""
    uid=request.args.get("uid")
    st=""
    staff=""
    sms=""
    mobile=""
    mess=""
    
    
    sms2=""
    mess2=""
    mobile2=""

    mycursor = mydb.cursor()

    ff=open("static/sms.txt","r")
    ss=ff.read()
    ff.close()

    ff=open("static/sms2.txt","r")
    ss2=ff.read()
    ff.close()

    mycursor.execute("SELECT * FROM admin where username='admin'")
    adata = mycursor.fetchone()
    camera=adata[4]
    mobile2=str(adata[5])

    ff=open("static/info.txt","r")
    unst=ff.read()
    ff.close()

    if unst=="":
        s=1
    else:
        mycursor.execute("SELECT max(id)+1 FROM detect_unknown")
        maxid = mycursor.fetchone()[0]
        if maxid is None:
            maxid=1

        fn="d"+str(maxid)+".jpg"
        shutil.copy("static/faces/f1.jpg","static/unknown/"+fn)
        
        sql = "INSERT INTO detect_unknown(id,camera,face_img) VALUES (%s, %s, %s)"
        val = (maxid, camera,fn)
        
        mycursor.execute(sql, val)
        mydb.commit()

        ss1=int(ss2)+1
        if ss1<=4:
            sms2="1"
            mess2="Unknown Person"
            ff=open("static/sms2.txt","w")
            ff.write(str(ss1))
            ff.close()
        
    if uid=="":
        s=1
    else:

        
        
        mycursor.execute("SELECT * FROM register where id=%s",(uid,))
        value = mycursor.fetchone()
        dept1=value[6]
        regno=value[13]
        name=value[1]
        
        mycursor.execute("SELECT * FROM timetable where id=1")
        tdata = mycursor.fetchone()
        dept2=tdata[1]
        mycursor.execute("SELECT * FROM staff where uname=%s",(tdata[2],))
        sdata = mycursor.fetchone()
        staff=sdata[1]

        mycursor.execute("SELECT * FROM staff where dept=%s && stype='HOD'",(dept2,))
        hdata = mycursor.fetchone()
        mobile=hdata[2]

        now = datetime.datetime.now()
        rdate=now.strftime("%d-%m-%Y")

        t = time.localtime()
        rtime = time.strftime("%H", t)
        rmin = time.strftime("%M", t)
        rh=int(rtime)
        rm=int(rmin)

        dh=int(tdata[5])
        dm=int(tdata[6])

        dh2=int(tdata[7])
        dm2=int(tdata[8])

        print("ctime")
        print(rh)
        print(rm)

        ######check time####
        x=0
        if dh<=rh and rh<=dh2:
            if dh==dh2:
                if dm<=rm and rm<=dm2:
                    x+=1

            elif dh==rh:
                if dm<rm:
                    x+=1

            elif dh<rh and rh<dh2:
                if rm<60:
                    x+=1
            elif rh==dh2:
                if rm<=dm2:
                    x+=1

        print("x")
        print(x)
        #############      
        if x>0 and dept1==dept2:
            st="1"
            
            mycursor.execute("SELECT max(id)+1 FROM detect_class_skipper")
            maxid = mycursor.fetchone()[0]
            if maxid is None:
                maxid=1

            fn="d"+str(maxid)+".jpg"
            shutil.copy("static/faces/f1.jpg","static/detect/"+fn)
            
            sql = "INSERT INTO detect_class_skipper(id, regno, name, camera, face_img, dept) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (maxid, regno, name, camera, fn, dept1)
            print(sql)
            mycursor.execute(sql, val)
            mydb.commit()

            mess="Regno: "+regno+", "+name+", Skipt the Class"

            ff=open("static/cam3.txt","w")
            ff.write("")
            ff.close()

            ss1=int(ss)+1
            if ss1<=4:
                sms="1"
                ff=open("static/sms.txt","w")
                ff.write(str(ss1))
                ff.close()
                
    
    return render_template('process33.html',uid=uid,tdata=tdata,value=value,st=st,staff=staff,sms=sms,mobile=mobile,mess=mess,unst=unst,sms2=sms2,mobile2=mobile2,mess2=mess2)

@app.route('/hod_home',methods=['POST','GET'])
def hod_home():
    msg=""
    uname=""
    act=request.args.get("act")
    data2=[]
    st=""

    if 'username' in session:
        uname = session['username']

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM register")
    data = mycursor.fetchall()

    mycursor.execute("SELECT * FROM department")
    value1 = mycursor.fetchall()

    mycursor.execute("SELECT distinct(year) FROM register")
    value2 = mycursor.fetchall()

    tdays=0
    mycursor.execute("SELECT distinct(rdate) FROM attendance")
    d2 = mycursor.fetchall()
    for d22 in d2:
        tdays+=1

    if request.method=='POST':
        st="1"
        dept=request.form['dept']
        year=request.form['year']
        if dept!="" and year!="":
            mycursor.execute("SELECT * FROM register where dept=%s && year=%s",(dept,year))
            dat = mycursor.fetchall()
            for ds in dat:
                dt=[]
                dt.append(ds[0])
                dt.append(ds[1])
                dt.append(ds[2])
                dt.append(ds[3])
                dt.append(ds[4])
                dt.append(ds[5])
                dt.append(ds[6])
                dt.append(ds[7])
                dt.append(ds[8])
                dt.append(ds[9])
                dt.append(ds[10])
                dt.append(ds[11])
                dt.append(ds[12])
                dt.append(ds[13])
                dt.append(ds[14])
                dt.append(ds[15])

                n1=0
                n2=0
                n3=0
                mycursor.execute("SELECT * FROM attendance where regno=%s",(ds[13],))
                dd = mycursor.fetchall()
                for d1 in dd:
                    if d1[3]=="Full Day Present":
                        n1+=1
                    elif d1[3]=="Half Day Present":
                        n2+=1
                    else:
                        n3+=1


                n22=n2/2
                pr=n1+n22

                per=(pr/tdays)*100
                per1=round(per,2)
                
                dt.append(per1)
                data2.append(dt)
                        
                
            
    
        
    return render_template('hod_home.html',data=data,data2=data2,value1=value1,value2=value2,st=st)

@app.route('/hod_table',methods=['POST','GET'])
def hod_table():
    msg=""
    uname=""
    act=request.args.get("act")
    data=[]

    if 'username' in session:
        uname = session['username']

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM timetable")
    data = mycursor.fetchall()



        
    return render_template('hod_table.html',data=data)

@app.route('/hod_attendance',methods=['POST','GET'])
def hod_attendance():
    msg=""
    uname=""
    st=""
    act=request.args.get("act")
    data=[]
    p1=""
    p2=""
    mob1=""
    mob2=""
    mess1=""
    mess2=""

    if 'username' in session:
        uname = session['username']
    
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM staff where uname=%s",(uname,))
    data1 = cursor.fetchone()
    email=data1[3]
    
    if request.method=='POST':
        
        rd=request.form['rdate']
        rdd=rd.split('-')
        rdate=rdd[2]+"-"+rdd[1]+"-"+rdd[0]
        cursor.execute('SELECT count(*) FROM attendance where rdate=%s',(rdate,))
        cnt = cursor.fetchone()[0]

        cursor.execute("SELECT a.id as SNo,a.regno as RegNo,r.name as Name,a.p1 as Period1,a.p2 as Period2,a.p3 as Period3,a.p4 as Period4,a.p5 as Period5,a.attendance as Status FROM attendance a,register r where r.regno=a.regno")
        result = cursor.fetchall()
        with open('data.csv','w') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
            #writer.writerow(col[0] for col in cursor.description)
            #for row in result:
            #    writer.writerow(row)
            writer.writerow("S.No")
            writer.writerow("RegNo")
            writer.writerow("Name")
            writer.writerow("Period1")
            writer.writerow("Period2")
            writer.writerow("Period3")
            writer.writerow("Period4")
            writer.writerow("Period5")
            writer.writerow("Attendance Status")
        
        with open('data.csv') as input, open('data.csv', 'w', newline='') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(col[0] for col in cursor.description)
            for row in result:
                if row or any(row) or any(field.strip() for field in row):                    
                    writer.writerow(row)

        
        if cnt>0:
            act="1"
            cursor.execute('SELECT * FROM attendance a,register r where a.rdate=%s && a.regno=r.regno',(rdate,))
            data = cursor.fetchall()

     
            ##########absent to parent 
            i=0
            
            for dat1 in data:
                
                if dat1[3]=="Absent" and dat1[2]==rdate:
                    i+=1
                    reg=dat1[1]
                    if i==1:
                        p1=reg
                        cursor.execute("SELECT * FROM register where regno=%s",(p1,))
                        d1 = cursor.fetchone()
                        
                        mob1=d1[14]
                        mess1=d1[1]+", RegNo: "+p1+", Absent"
                        print(mess1)
                    if i==2:
                        p2=reg
                        cursor.execute("SELECT * FROM register where regno=%s",(p2,))
                        d1 = cursor.fetchone()
                        
                        mob2=d1[14]
                        mess2=d1[1]+", RegNo: "+p2+", Absent"
                        print(mess2)
            

    if act=="send":
        mess="Attendance Report"
        with app.app_context():
            msg = Message(subject="Report", sender=app.config.get("MAIL_USERNAME"),recipients=[email], body=mess)
            with app.open_resource("data.csv") as fp:  
                msg.attach("data.csv", "text/csv", fp.read())
            mail.send(msg)
        st="1"

        

    return render_template('hod_attendance.html',msg=msg,act=act,data=data,st=st,mob1=mob1,mob2=mob2,mess1=mess1,mess2=mess2)

@app.route('/hod_report',methods=['POST','GET'])
def hod_report():
    msg=""
    uname=""
    act=request.args.get("act")
    data=[]

    if 'username' in session:
        uname = session['username']

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM staff where uname=%s",(uname,))
    data1 = mycursor.fetchone()
    dept=data1[9]

    mycursor.execute("SELECT * FROM detect_class_skipper where dept=%s order by id desc",(dept,))
    data = mycursor.fetchall()



        
    return render_template('hod_report.html',data=data)


@app.route('/staff_home',methods=['POST','GET'])
def staff_home():
    msg=""
    uname=""
    act=request.args.get("act")
    data=[]

    if 'username' in session:
        uname = session['username']

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM register")
    data = mycursor.fetchall()

    mycursor.execute("SELECT * FROM department")
    value1 = mycursor.fetchall()

    mycursor.execute("SELECT distinct(year) FROM register")
    value2 = mycursor.fetchall()

    if request.method=='POST':
        dept=request.form['dept']
        year=request.form['year']
        if dept!="" and year!="":
            mycursor.execute("SELECT * FROM register where dept=%s && year=%s",(dept,year))
            data = mycursor.fetchall()
    else:
        mycursor.execute("SELECT * FROM register")
        data = mycursor.fetchall()
        
    return render_template('staff_home.html',data=data,value1=value1,value2=value2)

@app.route('/staff_table',methods=['POST','GET'])
def staff_table():
    msg=""
    uname=""
    act=request.args.get("act")
    data=[]

    if 'username' in session:
        uname = session['username']

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM timetable")
    data = mycursor.fetchall()
        
    return render_template('staff_table.html',data=data)

@app.route('/staff_attendance',methods=['POST','GET'])
def staff_attendance():
    msg=""
    uname=""
    act=request.args.get("act")
    data=[]

    if 'username' in session:
        uname = session['username']

    cursor = mydb.cursor()



    if request.method=='POST':
        
        rd=request.form['rdate']
        rdd=rd.split('-')
        rdate=rdd[2]+"-"+rdd[1]+"-"+rdd[0]
        cursor.execute('SELECT count(*) FROM attendance where rdate=%s',(rdate,))
        cnt = cursor.fetchone()[0]

        if cnt>0:
            act="1"
            cursor.execute('SELECT * FROM attendance a,register r where a.rdate=%s && a.regno=r.regno',(rdate,))
            data = cursor.fetchall()
        
    return render_template('staff_attendance.html',data=data)

@app.route('/staff_report',methods=['POST','GET'])
def staff_report():
    msg=""
    uname=""
    act=request.args.get("act")
    data=[]

    if 'username' in session:
        uname = session['username']

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM staff where uname=%s",(uname,))
    data1 = mycursor.fetchone()
    dept=data1[9]

    mycursor.execute("SELECT * FROM detect_class_skipper where dept=%s order by id desc",(dept,))
    data = mycursor.fetchall()



        
    return render_template('staff_report.html',data=data)

@app.route('/view_unknown',methods=['POST','GET'])
def view_unknown():
    msg=""
    uname=""
    act=request.args.get("act")
    data=[]

    if 'username' in session:
        uname = session['username']

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM detect_unknown order by id desc")
    data = mycursor.fetchall()



        
    return render_template('view_unknown.html',data=data)


@app.route('/down', methods=['GET', 'POST'])
def down():
    #fn = request.args.get('fname')
    path="data.csv"
    return send_file(path, as_attachment=True)

@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    #session.pop('username', None)
    return redirect(url_for('index'))


#######
def gen4(camera):
    while True:
        frame = camera.get_frame()
    

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
@app.route('/video_feed4')
def video_feed4():

    return Response(gen4(VideoCamera4()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
#######
def gen3(camera):
    while True:
        frame = camera.get_frame()
    

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
@app.route('/video_feed3')
def video_feed3():

    return Response(gen3(VideoCamera3()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#######
def gen2(camera):
    while True:
        frame = camera.get_frame()
    

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
@app.route('/video_feed2')
def video_feed2():

    return Response(gen2(VideoCamera2()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
##########
def gen(camera):

    while True:
        frame = camera.get_frame()
    

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    
@app.route('/video_feed')
def video_feed():
    
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#########
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
