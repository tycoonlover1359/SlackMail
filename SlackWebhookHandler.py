import json
import base64
import boto3
import hmac
from os import environ

def lambda_handler(event, context):
    body = event["body"]
    slack_timestamp = event["headers"]["x-slack-request-timestamp"]
    slack_signature = event["headers"]["x-slack-signature"]
    signing_secret = environ["Signing_Secret"]
    
    decoded_body = base64.b64decode(body).decode("utf-8")
    sig_basestring = f"v0:{slack_timestamp}:{decoded_body}"
    calculated_signature = "v0=" + hmac.new(
        signing_secret.encode("utf-8"),
        sig_basestring.encode("utf-8"),
        "SHA256"    
    ).hexdigest()
    
    if hmac.compare_digest(calculated_signature, slack_signature):
        print("Signature Match")
        print("Sending to Action Handler")
        aws_lambda = boto3.client("lambda", region_name="us-west-2")
        try:
            response = aws_lambda.invoke(
                FunctionName="arn:aws:lambda:us-west-2:<ACCOUNT_ID>:function:SlackActionHandler",
                Payload=json.dumps({"unparsed_payload": f"{decoded_body}"}).encode("utf-8"),
                InvocationType="Event"
            )
        except Exception as e:
            print(f"Error Occurred: {e}")
            return {
                "statusCode": 500,
                "body": f"Error Occurred: {e}"
            }
        else:
            return {
                'statusCode': 200,
                'body': "Signature Match"
            }
    else:
        print("Signature Mismatch")
        return {
            "statuCode": 401,
            "body": "Signature Mismatch"
        }