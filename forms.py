from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, validators, FileField, HiddenField
from wtforms.validators import InputRequired, Length, EqualTo, Email
class SignUp(FlaskForm):
    Username = StringField(
        "Username", validators=[InputRequired(), Length(min=5, max=16)]
    )
    Name = StringField("Name", validators=[InputRequired(), Length(max=100)])
    Phone = StringField("Phone", validators=[InputRequired(), Length(min=10, max=10)])
    Email = StringField("Email", validators=[InputRequired(), Email(message="Must be a Valid Email Address"), Length(max=100)])
    Password = PasswordField(
        "Password", validators=[InputRequired(), EqualTo("Confirm_Password", message="Passwords Must Match"), Length(min=8, max=30)]
    )
    Confirm_Password = PasswordField(
        "Confirm Password", validators=[InputRequired(), Length(min=8, max=30)]
    )
    Submit = SubmitField(label=('Submit'))

class SignIn(FlaskForm):
    UsernameorEmail = StringField("UsernameorEmail", validators=[InputRequired(), Length(max=100)])
    Password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=30)])
    Submit = SubmitField(label=('Submit'))

class ProfileForm(FlaskForm):    
    Username = StringField("Username", validators=[Length(max=100)])
    Name = StringField("Name", validators=[InputRequired(), Length(max=100)])
    Email = StringField("Email", validators=[InputRequired(), Email(message="Must be a Valid Email Address"), Length(max=100)])
    Phone = StringField("Phone", validators=[InputRequired(), Length(min=10, max=10)])
    Submit = SubmitField(label=('Save Profile'))

def is_weekend(date):
        return date.weekday() in [5, 6]
    
class AppointmentsForm(FlaskForm):
    def validate_date(self, field):
        if is_weekend(field.data):
            raise validators.ValidationError('Weekends are not allowed')
        
    Name = StringField("Name", validators=[InputRequired(), Length(max=100)])
    PetName = SelectField("Petname", validators=[InputRequired()])
    Phone = StringField("Phone", validators=[InputRequired(), Length(min=10, max=10)])
    Address = StringField("Address", validators=[InputRequired(), Length(max=100)])
    ServicesReq=TextAreaField("ServicesReq",validators=[InputRequired()])
    AppointmentDate = DateField("AppointmentDate", validators=[InputRequired(), validate_date])
    AppointmentTime = SelectField("AppointmentTime", choices=[("Morning", "Morning"), ("Afternoon", "Afternoon"), ("Evening", "Evening")])    
    Submit = SubmitField(label=('Book Appointment'))

class EmployeeProfileForm(FlaskForm):
    Username = StringField("Username", validators=[Length(max=100)])
    Name = StringField("Name", validators=[InputRequired(),Length(max=100)])
    Email = StringField("Email", validators=[Email(message="Must be a Valid Email Address"), Length(max=100)])
    Phone = StringField("Phone", validators=[InputRequired(),Length(min=10, max=10)])
    PetTypes = StringField("PetTypes", validators=[Length(max=100)])
    Time = StringField("Time", validators=[Length(max=5)])
    Submit = SubmitField(label=('Save Profile'))

class ReportForm(FlaskForm):
    file = FileField("report", validators=[InputRequired()])
    index = HiddenField("index")
    fee = StringField("Fee", validators=[InputRequired()])
    Submit = SubmitField(name="button", label=('Upload'))

class DownloadForm(FlaskForm):
    index = HiddenField("index")
    Submit = SubmitField(name="button",label=('Download'))

class PaymentForm(FlaskForm):
    index = HiddenField("index")
    PaymentButton = SubmitField(name="button", label=('Pay'))
    
class Previousreport(FlaskForm):
    index = HiddenField("index")
    Download = SubmitField(name="button")
    Submit = SubmitField(name="button",label=('Previous Reports'))
