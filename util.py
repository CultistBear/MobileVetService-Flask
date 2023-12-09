import stripe
from constants import REPORTS_BUCKET, STRIPE_SECRET_KEY
from aws_keys import botoSession
stripe.api_key = STRIPE_SECRET_KEY

def upload_user_file(file, username, doctor_name, petname, pettype, date, timeslot):
    s3 = botoSession.resource("s3")
    s3.Object(REPORTS_BUCKET, "reports/%s.pdf"%("-".join([username,doctor_name,petname,pettype,date.replace("-",""),timeslot]))).upload_file(file)

def download_user_file(username, doctor_name, petname, pettype, date, timeslot):
    s3 = botoSession.resource("s3")
    filePath = "reports\%s.pdf"%("-".join([username,doctor_name,petname,pettype,date.replace("-",""),timeslot]))
    s3.Object(REPORTS_BUCKET, "reports/%s.pdf"%("-".join([username,doctor_name,petname,pettype,date.replace("-",""),timeslot]))).download_file(filePath)
    return filePath

def download_direct(filepath):
    s3 = botoSession.resource("s3")
    s3.Object(REPORTS_BUCKET, filepath).download_file(filepath)
    return filepath

def get_filename_from_s3_bucket():
    s3 = botoSession.resource("s3")
    bucket = s3.Bucket(REPORTS_BUCKET)
    return bucket.objects.all()

def create_sns_topic(topicname):
    sns = botoSession.client("sns")
    response = sns.create_topic(Name=topicname)
    return response["TopicArn"]

def subscribe_to_topic(*number, topicarn):
    sns = botoSession.client("sns")
    for i in number:
        reponse = sns.subscribe(
            TopicArn=topicarn,
            Protocol="sms",
            Endpoint="+91"+i
        )
def subscribe_to_topic_email(*email, topicarn):
    sns = botoSession.client("sns")
    for i in email:
        reponse = sns.subscribe(
            TopicArn=topicarn,
            Protocol="email",
            Endpoint=i
        )
        
def send_sms_message(message, topicarn):
    sns = botoSession.client("sns")
    sns.publish(
        TopicArn=topicarn,
        Message=message
    )
    
def delete_sns_topic(topicarn):
    sns = botoSession.client("sns")
    sns.delete_topic(
        TopicArn=topicarn
    )