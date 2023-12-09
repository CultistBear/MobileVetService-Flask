from flask import Flask, request, render_template, redirect, url_for, session, send_file
from forms import SignUp, SignIn, ProfileForm, AppointmentsForm, EmployeeProfileForm, ReportForm, DownloadForm, PaymentForm, Previousreport
from databseManagement import DB
import os
import shutil
import stripe
from constants import FLASK_SECRET_KEY, PASSWORD_SALT, STRIPE_SECRET_KEY
from werkzeug.utils import secure_filename
from util import upload_user_file, download_user_file, get_filename_from_s3_bucket, download_direct, create_sns_topic, subscribe_to_topic, send_sms_message, delete_sns_topic, subscribe_to_topic_email
import hashlib
from flask_wtf.csrf import CSRFProtect
from datetime import date

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
csrf = CSRFProtect(app)
stripe.api_key = STRIPE_SECRET_KEY

timeDict = {
    "Morning": [900, 1200],
    "Afternoon": [1200,1500],
    "Evening": [1500, 1800]
}

@app.before_request
def make_session_temp():
    if session.get("username", None) == None and request.endpoint not in ["signin", "signup", "static", "logout"]:
        return redirect(url_for("signin"))
    if session.get("username", None) != None and request.endpoint in ["signin", "signup"]:
        return redirect(url_for("home"))
    session.permanent = False

@app.route("/")
@app.route("/signup", methods=["POST", "GET"]) 
def signup():
    db = DB()
    form = SignUp()
    if form.validate_on_submit():
        username = request.form.get("Username")
        name = request.form.get("Name")
        phone = request.form.get("Phone")
        email = request.form.get("Email")
        password = request.form.get("Password")
        confirm_password = request.form.get("Confirm_Password")
        employee = 0
        if password != confirm_password:
            session["error"] = "Passwords do not match"
            return redirect(url_for("signup"))
        elif (len(db.query(r"select * from Users where Username = '%s'" % (username)))!= 0 or len(db.query(r"select * from Employee where Username = '%s'" % (username))) !=0):
            session["error"] = "Username Already Exists"
            return redirect(url_for("signup"))
        elif (len(db.query(r"select * from Users where Email = '%s'" % (email)))!= 0 or len(db.query(r"select * from Employee where Email = '%s'" % (email))) !=0):
            session["error"] = "Email Already Exists"
            return redirect(url_for("signup"))
        password += PASSWORD_SALT
        db.query(r"insert into Users(Username, Name, Phone, Email, Password, Employee, PetName, PetType, PetMedicalHistory) values('%s','%s','%s','%s','%s','%s', 'None', 'None', 'None')"% (username, name, phone, email, hashlib.md5(password.encode()).hexdigest(), employee))
        session["message"] = "Successfully Signed Up"
        return redirect(url_for("signin")) 

    error = session.pop("error", None)
    message = session.pop("message", None)
    return render_template("index.html", error=error, message=message, form=form)


@app.route("/signin", methods=["POST", "GET"])  
def signin():    
    db = DB()
    form = SignIn()
    if form.validate_on_submit():
        emailorusername = request.form.get("UsernameorEmail")
        password = request.form["Password"]
        password += PASSWORD_SALT
        password = hashlib.md5(password.encode()).hexdigest()
        if (len(db.query(r"select * from Users where Username = '%s' and Password = '%s'" % (emailorusername, password))) == 0):
            if (len(db.query(r"select * from Users where Email = '%s' and Password = '%s'"% (emailorusername, password))) == 0):
                if(len(db.query(r"select * from Employee where Username= '%s' and Password = '%s'" %(emailorusername,password)))==0):
                    if(len(db.query(r"select * from Employee where Email= '%s' and Password = '%s'" %(emailorusername,password)))==0):
                        session["error"] = "Invalid Username/Email or Password"
                        return redirect(url_for("signin"))
                    else:
                        session["username"] = db.query(r"select Username from Employee where Email = '%s' and Password = '%s'" %(emailorusername,password))[0]["Username"]
                        session["employee"] = 1
                        return redirect(url_for("home"))
                else:
                    session["username"] = emailorusername
                    session["employee"] = 1
                    return redirect(url_for("home"))
            else:
                session["username"] = db.query(r"select Username from Users where Email = '%s' and Password = '%s'"% (emailorusername, password))[0]["Username"]
                session["employee"] = 0
                return redirect(url_for("home"))
        else:
            session["username"] = emailorusername
            session["employee"] = 0
            return redirect(url_for("home"))
        
    message = session.pop("message", None)
    error = session.pop("error", None)
    return render_template("signin.html", message=message, error=error, form=form)

@app.route("/profile", methods=["POST", "GET"])
def profile():
    db = DB()
    if(session["employee"]==0):
        form = ProfileForm()
        userData = db.query("select * from Users where Username = '%s'" % (session["username"]))[0]
        petData = db.query("select PetName, PetType, PetMedicalHistory from Users where username = '%s'"%(session['username']))
        user = {
            "Username": userData["Username"],
            "Name": userData["Name"],
            "Phone": userData["Phone"],
            "Email": userData["Email"],
            "PetName": [i["PetName"] for i in petData],
            "PetType": [i["PetType"] for i in petData],
            "PetMedicalHistory": [i["PetMedicalHistory"] for i in petData]
        }
        if form.validate_on_submit():
            username = session["username"]
            name = request.form.get("Name")
            phone = request.form.get("Phone")
            email = request.form.get("Email")

            getPassEmp = db.query("select Password, Employee from Users where Username = '%s'" % (username))[0]
            password = getPassEmp["Password"]
            employee = getPassEmp["Employee"]
            db.query("delete from Users where Username = '%s'" % (username))

            pet_data = {}
            for key, value in request.form.items():
                if key.startswith("PetName") or key.startswith("PetType") or key.startswith("PetMedicalHistory"):
                    pet_number = key[-1] 
                    field_name = key[:-1]  
                    pet_data.setdefault(pet_number, {})[field_name] = value
            insert_str=""

            flag = 1
            if(flag):
                    insert_str+=str(('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'))% (username, name, phone, email, password, employee, "None", "None", "None")+","
                    flag = 0
            for pet_number, pet_info in pet_data.items():
                pet_name = pet_info.get("PetName")
                pet_type = pet_info.get("PetType")
                pet_medical_history = pet_info.get("PetMedicalHistory")
                insert_str+=str(('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'))%(username, name, phone, email, password, employee, pet_name, pet_type, pet_medical_history)+","
            db.query("insert into Users(Username, Name, Phone, Email, Password, Employee, PetName, PetType, PetMedicalHistory) values %s" % (insert_str[:-1]))
            session["message"] = "Successfully Updated Profile"
            return redirect(url_for("profile"))

        message = session.pop("message", None)
        error = session.pop("error", None)
        return render_template("profile.html", message=message, error=error, form=form, user=user)
    else:
        form = EmployeeProfileForm()
        userData = db.query("select * from Employee where Username = '%s'" % (session["username"]))[0]
        petData = db.query("select Pet_Types from Employee where username = '%s'"%(session['username']))
        user = {
            "Username": userData["Username"],
            "Name": userData["Doctor_Name"],
            "Phone": userData["Phone"],
            "Email": userData["Email"],
            "Pet_Types": ", ".join([i["Pet_Types"] for i in petData]),
            "start_time": userData["Start_time"],
            "end_time": userData["End_time"],
        }
        if form.validate_on_submit():
            name = request.form.get("Name")
            phone = request.form.get("Phone")
            db.query("update Employee set Name = '%s', Phone = '%s' where Username = '%s'"%(name, phone, session["username"]))
        return render_template("employeeprofile.html", form=form, user=user)

@app.route("/contact")
def contact():
    db = DB()
    DocList = db.query("select Username, Doctor_Name, Phone, Email, Start_Time, End_Time from Employee")
    UniqueDocList = []
    for _ in range(len(DocList)):
        if(DocList[_] not in UniqueDocList):
            UniqueDocList.append(DocList[_])
    for _ in range(len(UniqueDocList)):
        DocPets = db.query("select Pet_Types from Employee where Username = '%s'"%(UniqueDocList[_]["Username"]))
        DocPet_Types = ", ".join([i["Pet_Types"] for i in DocPets])
        UniqueDocList[_]["Pet_Types"] = DocPet_Types
    return render_template("contact.html", DocList = UniqueDocList)

@app.route("/appointment")
def appointment():
    if(session["employee"]==0):
        return render_template("appointment.html")
    else:
        return redirect(url_for("yourapp"))

@app.route("/book", methods=["POST", "GET"])
def bookappointments():
    if (session["employee"] == 1): 
        redirect(url_for("yourapp"))
    db = DB()
    mindate = date.today().isoformat()
    form = AppointmentsForm()
    userData = db.query("select Name, Phone, PetName, Email, PetType from Users where Username = '%s'" % (session["username"]))
    form.PetName.choices = [("%s"%i["PetName"], i["PetName"]) for i in userData if i["PetName"] != "None"]
    user={
        "Name": userData[0]["Name"],
        "PetName": [i["PetName"] for i in userData],
        "Phone": userData[0]["Phone"]
    }
    if form.validate_on_submit():
        name = request.form.get("Name")
        petname = request.form.get("PetName")
        phone = request.form.get("Phone")
        services = request.form.get("ServicesReq")
        appointmentdate = request.form.get("AppointmentDate")
        address = request.form.get("Address")
        selected_time = request.form.get("AppointmentTime")
        timeList = timeDict[selected_time]
        # 9 to 12, 12 to 3, 3 to 6
        # 0900-1200 1200-1500 1500-1800
        for i in userData:
            if(i["PetName"] == petname):
                pettype = i["PetType"]
        
        DocList = db.query("select Username, Doctor_Name, Phone, Email, Start_Time, End_Time from Employee where Start_Time <= %d and End_Time >= %d and Pet_Types = '%s'"%(timeList[0], timeList[1], pettype))
        if(len(DocList) == 0):
            session["error"] = "No Doctors Available for Selected Time and Pet Type"
            return redirect(url_for("bookappointments"))
        found = 0
        for Doc in DocList:
            if(len(db.query("select * from appointments where DoctorUsername = '%s' and Date = '%s' and timeslot = '%s'"%(Doc['Username'], appointmentdate, selected_time)))==0):
                found = 1
                arn = create_sns_topic("%s%s%s"%(Doc['Username'], appointmentdate, selected_time))
                db.query("insert into appointments values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '-', '0', '%s', '%s')"%(session["username"], Doc['Username'], name, petname, pettype, phone, Doc['Doctor_Name'], Doc['Phone'], Doc['Email'], userData[0]["Email"], services, appointmentdate, selected_time, arn, address))
                subscribe_to_topic(phone, Doc['Phone'], topicarn=arn)
                subscribe_to_topic_email(userData[0]["Email"], Doc['Email'], topicarn=arn)
                send_sms_message("User %s has booked an appointment with %s on %s at %s"%(name, Doc['Doctor_Name'], appointmentdate, selected_time), arn)
                break
        if(found == 0):
            session["error"] = "No Doctors Available for Selected Time and Pet Type"
            return redirect(url_for("bookappointments"))
        
        session["message"] = "Successfully Booked Appointment"
        return redirect(url_for("bookappointments"))
    
    message = session.pop("message", None)
    error = session.pop("error", None)
    return render_template("bookappointments.html", form=form, user=user, mindate = mindate, message = message, error = error)

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/report", methods=['GET', 'POST'])
def report():
    if(session["employee"]==0):
        return redirect(url_for("yourapp"))
       
    db = DB()
    preform = Previousreport()
    appoint = db.query("select distinct Username, Name, PetName, PetType, Fee from appointments where DoctorUsername = '%s' and Fee = '-'"%(session["username"]))
    
    for i in appoint:
        filenames = []
        for file in get_filename_from_s3_bucket():
            if i["Username"] in file.key and i['PetName'] in file.key and i['PetType'] in file.key and file.key not in filenames:
                filenames.append(file.key)
        i["filenames"] = filenames
    
    ChosenPet = 0
    if preform.validate_on_submit():
        if(request.form['button'] != 'Previous Reports'):
            return send_file(download_direct(request.form['button']), as_attachment=True)
        
        ChosenPet =  request.form.get("Petname")
        return render_template("report.html", form=preform, appoint=appoint, ChosenPet=ChosenPet)  
    
    return render_template("report.html", form=preform, appoint=appoint, ChosenPet=ChosenPet)

@app.route("/logout")
def logout():
    session.pop("username", None)
    session["message"] = "Successfully Logged Out"
    return redirect(url_for("signin"))

@app.route('/payment/success', methods = ['GET','POST'])
def success():
    db = DB()
    db.query("update appointments set Paid = '1' where Username = '%s' and DoctorUsername = '%s' and Date = '%s' and timeslot = '%s'"%(session["appointmentsAll"][session["index"]]["Username"], session["appointmentsAll"][session["index"]]["DoctorUsername"], session["appointmentsAll"][session["index"]]["Date"], session["appointmentsAll"][session["index"]]["timeslot"]))
    send_sms_message("Payment Completed for appointment booked by %s with %s on %s at %s"%(session["appointmentsAll"][session["index"]]["Name"], session["appointmentsAll"][session["index"]]['DoctorName'], str(session["appointmentsAll"][session["index"]]['Date']), session["appointmentsAll"][session["index"]]['timeslot']), session["appointmentsAll"][session["index"]]['arn'])
    delete_sns_topic(session["appointmentsAll"][session["index"]]['arn'])
    session.pop("appointmentsAll", None)
    session.pop("index", None)
    return redirect(url_for("yourapp"))


@app.route('/payment/cancel', methods = ['GET','POST'])
def cancel():
    return render_template('cancel.html')
    
@app.route("/yourappointments", methods = ["POST", "GET"])
def yourapp():
    
    try:
        shutil.rmtree("reports")
        os.mkdir("reports")
    except Exception:
        pass
    
    if(session["employee"]==0):
        db = DB()
        form_ind = DownloadForm()
        form_pay = PaymentForm()
        
        appointmentsAll = db.query("select * from appointments where Username = '%s'"%(session["username"]))
        currentDate = str(date.today().isoformat())
        
        if len(appointmentsAll)>0:
            appointmentsAll.sort(key = lambda x: x["Date"])
        
        for appointment in appointmentsAll:
            appointment["MedicalRecord"] = db.query("select PetMedicalHistory from Users where Username = '%s' and PetName = '%s' and PetType = '%s'"%(appointment["Username"], appointment["PetName"], appointment["PetType"]))[0]['PetMedicalHistory']
            appointment["Date"] = appointment["Date"].isoformat()
            
        if form_ind.validate_on_submit() or form_pay.validate_on_submit():
            if(request.form['button'] == 'Download'):
                index = int(request.form.getlist("index")[-1])
                file = download_user_file(appointmentsAll[index]["Username"], appointmentsAll[index]["DoctorName"], appointmentsAll[index]["PetName"], appointmentsAll[index]["PetType"], str(appointmentsAll[index]["Date"]), appointmentsAll[index]["timeslot"])
                return send_file(file, as_attachment=True)
            
            elif(request.form['button'] == 'Pay'):
                session["appointmentsAll"] = appointmentsAll   
                index = int(request.form.get("index"))
                session["index"] = index
                checkout_session = stripe.checkout.Session.create(
                line_items = [
                    {
                        'price_data': {
                            'product_data': {
                                'name': "Appointment on %s at %s with %s "%(appointmentsAll[index]["Date"], appointmentsAll[index]["timeslot"],appointmentsAll[index]["DoctorName"]),
                            },
                            'unit_amount': int(appointmentsAll[index]["Fee"])*100,
                            'currency': 'inr',
                        },
                        'quantity': 1,
                    },
                ],
                payment_method_types=['card'],
                mode='payment',
                success_url=request.host_url + 'payment/success',
                cancel_url=request.host_url + 'payment/cancel',
                )
                return redirect(checkout_session.url) 
            
        return render_template("yourappointments.html", appointmentsAll = appointmentsAll, currentDate = currentDate, timeDict = timeDict, form_ind = form_ind, form_pay = form_pay)
    
    else:
        form = ReportForm()
        form_ind = DownloadForm()
        
        db=DB()
        
        appointmentsAll = db.query("select * from appointments where DoctorUsername = '%s'"%(session["username"]))
        currentDate = str(date.today().isoformat())
        if len(appointmentsAll)>0:
            appointmentsAll.sort(key = lambda x: x["Date"])

        for appointment in appointmentsAll:
            appointment["MedicalRecord"] = db.query("select PetMedicalHistory from Users where Username = '%s' and PetName = '%s' and PetType = '%s'"%(appointment["Username"], appointment["PetName"], appointment["PetType"]))[0]['PetMedicalHistory']
            appointment["Date"] = appointment["Date"].isoformat()
        
        if form.validate_on_submit() or form_ind.validate_on_submit():
            if(request.form['button'] == 'Download'):
                index = int(request.form.getlist("index")[-1])
                file = download_user_file(appointmentsAll[index]["Username"], appointmentsAll[index]["DoctorName"], appointmentsAll[index]["PetName"], appointmentsAll[index]["PetType"], str(appointmentsAll[index]["Date"]), appointmentsAll[index]["timeslot"])
                return send_file(file, as_attachment=True)
            
            elif(request.form['button'] == 'Upload'):
                index = int(request.form.get("index"))
                file = request.files['file']
                file.save("reports/"+secure_filename(file.filename))
                upload_user_file("reports/"+secure_filename(file.filename), appointmentsAll[index]["Username"], appointmentsAll[index]["DoctorName"], appointmentsAll[index]["PetName"], appointmentsAll[index]["PetType"], str(appointmentsAll[index]["Date"]), appointmentsAll[index]["timeslot"])
                send_sms_message("Report Uploaded for appointment booked by %s with %s on %s at %s"%(appointmentsAll[index]["Name"], appointmentsAll[index]['DoctorName'], str(appointmentsAll[index]['Date']), appointmentsAll[index]['timeslot']), appointmentsAll[index]['arn'])
                os.remove("reports/"+secure_filename(file.filename))
                db.query("update appointments set Fee = '%s' where Username = '%s' and DoctorUsername = '%s' and Date = '%s' and timeslot = '%s'"%(request.form.get("fee"), appointmentsAll[index]["Username"], appointmentsAll[index]["DoctorUsername"], appointmentsAll[index]["Date"], appointmentsAll[index]["timeslot"]))
                return redirect(url_for("yourapp"))

        return render_template("employeemyappointments.html", appointmentsAll=appointmentsAll,currentDate=currentDate,timeDict=timeDict, form=form, form_ind=form_ind)


@app.route("/home", methods=["POST", "GET"])
def home():
    return render_template("home.html")

@app.errorhandler(404)  
def not_found(e): 
  return render_template("404.html") 

if __name__ == "__main__":
    app.run(host="0.0.0.0")
