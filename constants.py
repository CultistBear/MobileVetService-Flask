from aws_keys import botoSession

def get_parameter(param_name):
    client = botoSession.client("ssm")
    response = client.get_parameter(
        Name=param_name, WithDecryption=True 
    )
    return response["Parameter"]["Value"]

DATABASE_NAME = get_parameter("/vet-app/database_name")
RDS_ENDPOINT = get_parameter("/vet-app/rds_endpoint") 
DB_USERNAME = get_parameter("/vet-app/db_host") 
DB_PASSWORD = get_parameter("/vet-app/db_password") 
PASSWORD_SALT = get_parameter("/vet-app/password_salt") 
FLASK_SECRET_KEY = get_parameter("/vet-app/flask_secret_key") 
REPORTS_BUCKET = get_parameter("/vet-app/reports_bucket")
STRIPE_SECRET_KEY = get_parameter("/vet-app/stripe_secret_key")