from databseManagement import DB
from constants import PASSWORD_SALT
import hashlib
db = DB()

def password_generate(passw):
    return hashlib.md5((passw+PASSWORD_SALT).encode()).hexdigest()

try:
    db.query("drop database testdb")
    db.query("create database testdb")
    db.query("use testdb")
    db.query("create table Users(Username varchar(20), Name varchar(105), Phone varchar(10), Email varchar(100), Password varchar(300), employee boolean, PetName varchar(105), PetType varchar(30), PetMedicalHistory varchar(5000))")
    db.query("create table Employee(Username varchar(20), Doctor_Name varchar(20), Phone varchar(10), Email varchar(100), Password varchar(300), Pet_Types varchar(100), Start_time integer(5), End_time integer(5))")
    db.query("create table appointments(Username varchar(20), DoctorUsername varchar(20), Name varchar(20), PetName varchar(20), PetType varchar(30), UserPhone varchar(10), DoctorName varchar(20), DoctorPhone varchar(10), DoctorEmail varchar(100), Email varchar(100), Services varchar(100), Date date, timeslot varchar(20), Fee varchar(10), Paid varchar(1), arn varchar(1024), address varchar(200))")
    db.query("INSERT INTO Employee (Username, Doctor_Name, Phone, Email, Password, Pet_Types, Start_time, End_time) VALUES ('user1', 'Dr. Smith', '1234567890', 'user1@email.com', '%s', 'Dog', 900, 1200), ('user2', 'Dr. Johnson', '9876543210', 'user2@email.com', '%s', 'Cat', 1200, 1500),('user3', 'Dr. Davis', '5555555555', 'user3@email.com', '%s', 'Bird', 1500, 1800),('user4', 'Dr. White', '1112223333', 'user4@email.com', '%s', 'Fish', 900, 1200),('user5', 'Dr. Brown', '9998887777', 'user5@email.com', '%s', 'Reptile', '1200', 1500),('user1', 'Dr. Smith', '1234567890', 'user1@email.com', '%s', 'Cat', 900, 1200), ('user2', 'Dr. Johnson', '9876543210', 'user2@email.com', '%s', 'Bird', 1200, 1500),('user2', 'Dr. Johnson', '9876543210', 'user2@email.com', '%s', 'Dog', 1200, 1500)"%(password_generate('password1'),password_generate('password2'),password_generate('password3'),password_generate('password4'),password_generate('password5'), password_generate('password1'),password_generate('password2'),password_generate('password2')))
except Exception as e:
    print(e)
    pass
