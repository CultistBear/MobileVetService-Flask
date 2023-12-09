import boto3
#get through s3
credentials = open('credentials.txt', 'r').read().splitlines()
cred = {i.split('=')[0]: i.split('=')[1] for i in credentials}

botoSession = boto3.Session(
    aws_access_key_id=cred['AWS_ACCESS_KEY'],
    aws_secret_access_key=cred['AWS_SECRET_KEY'] ,
    aws_session_token=cred['AWS_SESSION_TOKEN'],
    region_name=cred['AWS_REGION'],
)
