import json
import boto3
import mailparser
import urllib3
from botocore.exceptions import ClientError
from base64 import b64decode
from datetime import datetime
from os import getenv, listdir, environ

def lambda_handler(event, context):
    parsed_emails = 0
    records = event["Records"]
    s3 = boto3.resource("s3", region_name="us-west-2")
    bucket = s3.Bucket(getenv("Email_Bucket", "tycoon-emails"))
    http = urllib3.PoolManager()
    for record in records:
        notification = record["Sns"]
        message = json.loads(notification["Message"])
        receipt = message["receipt"]
        eml_id = message["mail"]["messageId"]
        print(f"Processing Message with ID: {eml_id}")
        action = receipt["action"]
        email_object = bucket.Object(action["objectKey"])
        try:
            response = email_object.get()
        except ClientError as e:
            print(f"Error Occurred: {e}. Skipping...")
        else:
            body = response["Body"]
            email_data = body.read()
            mail = mailparser.parse_from_bytes(email_data)
            
            locale, domain = mail.to[0][1].split("@")
            
            base_key = domain + "/" + str("/".join(locale.split("+"))) + "/" + mail.date.isoformat()
            obj_base_key = str(base_key + " - " + mail.from_[0][1] + ": " + str(mail.subject).replace("/", "-")).replace("\r", "").replace("\n", "")
            
            bucket.put_object(
                Key=f"{obj_base_key}.eml",
                Body=email_data
            )
            
            print(f"Saved Email File To: {obj_base_key}.eml")
            
            with open("slackmessage.json", "r") as f:
                eml_from = mail.from_[0][1]
                eml_to = mail.to[0][1]
                eml_subject = mail.subject
                
                slack_message = json.loads(f.read())
                slack_message["text"] = f"New email from {eml_from}"
                slack_message["blocks"][0]["text"]["text"] = f"*To:* {eml_to}\n*From:* {eml_from}\n*Subject:* {eml_subject}"
                slack_message["blocks"][1]["elements"][0]["value"] = f"{obj_base_key}.eml"
                slack_message["blocks"][1]["elements"][1]["value"] = f"{obj_base_key}.eml"
                
                json_data = json.dumps(slack_message).encode("utf-8")
                
                http.request(
                    "POST",
                    "https://slack.com/api/chat.postMessage",
                    body=json_data,
                    headers={
                        "Authorization": f"Bearer {environ['Slack_Token']}",
                        "Content-Type": "application/json"
                    }
                )
            
            parsed_emails += 1
            
    return {
        'statusCode': 200,
        'body': json.dumps(f"Successfully parsed {parsed_emails} email(s)")
    }