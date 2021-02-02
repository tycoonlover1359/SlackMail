import json
import urllib3
import urllib.parse
import boto3
import os
from uuid import uuid4

def lambda_handler(event, context):
    message = event["unparsed_payload"]
    slack_payload_unparsed = message.replace("payload=", "")
    slack_payload = json.loads(urllib.parse.unquote_plus(slack_payload_unparsed))
    
    response_url = slack_payload["response_url"]
    message_timestamp = slack_payload["message"]["ts"]
    message_channel = slack_payload["channel"]["id"]
    
    s3_client = boto3.client("s3", region_name="us-west-2")
    http = urllib3.PoolManager()
    bucket = os.getenv("Email_Bucket", "tycoon-emails")
    for action in slack_payload["actions"]:
        action_id = action["action_id"]
        eml_key = action["value"]
        eml_title = eml_key.split("/")[-1]
        if action_id == "download_email":
            eml_url = s3_client.generate_presigned_url(
                "get_object",
                {
                    "Bucket": f"{bucket}",
                    "Key": f"{eml_key}"
                },
                1800
            )
            eml_uuid = uuid4()
            response = http.request(
                "POST",
                "https://slack.com/api/files.remote.add",
                fields={
                    "token": f"{os.environ['Slack_Token']}",
                    "external_id": f"{eml_uuid}",
                    "external_url": f"{eml_url}",
                    "title": f"{eml_title}"
                }
            )
            j = json.loads(response.data.decode("utf-8"))
            if j["ok"]:
                response = http.request(
                    "POST",
                    "https://slack.com/api/files.remote.share",
                    fields={
                        "token": f"{os.environ['Slack_Token']}",
                        "external_id": f"{eml_uuid}",
                        "channels": f"{os.environ['Emails_Channel']}"
                    }
                )
        elif action_id == "delete_email":
            s3_client.delete_object(
                Bucket=f"{bucket}",
                Key=f"{eml_key}"
            )
            response = http.request(
                "POST",
                "https://slack.com/api/chat.delete",
                fields={
                    "token": f"{os.environ['Slack_Token']}",
                    "channel": f"{message_channel}",
                    "ts": f"{message_timestamp}"
                }
            )
                
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
