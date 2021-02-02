# SlackMail
SlackMail is a system based around Amazon Simple Email Service (SES) to allow for serverless custom emails. It is intended as a way of allowing a personal domain to be used to "create" email addresses that can be used for organization and potentially spam protection and/or tracking. The user is notified of incoming email addresses via a Slack channel, with options to download and delete the email. Sending emails (replying or otherwise) are currently unsupported.

# Status
SlackMail is marked as `Active-ish`, meaning that it is actively used however only maintained/updated as necessary. If something breaks, it will be fixed, however new features are unlikely unless a need arises.

# How it Works
SlackMail requires SES to do two actions before it can perform:
1. SES saves the email in Amazon S3 under a unique key, then
2. SES uses Amazon Simple Notification Service to notify the `SES-Email-Notification-Handler` function that an email has been received.

`SES-Email-Notification-Handler` is a function that handles notifications from SES. In order, it:
1. Downloads the email from S3 using the key provided by SES, then
2. Reads and parses the raw email
3. Reads `slackmessage.json` and parses it, then replaces appropriate values (as `slackmessage.json` is used only as a webhook payload template)
4. Sends the payload to the designated channel using the provided Slack token

`SlackWebhookHandler` handles the buttons created by Slack from the previously mentioned webhook payload. When receiving a POST request from Slack, it verifies that the message did come from Slack (using signature verification), then, assuming the message is from Slack, passes it along to the `SlackActionHandler` function.

`SlackActionHandler` handles the invocation event from `SlackWebhookHandler`. If the action is to download the email, the function generates a presigned URL for the email object (valid for 30 minutes after generation), "uploads" a remote file to Slack, then sends the file in the designated channel. If the action is to delete the email, the function deletes the email from S3 then deletes the email message from Slack.

# Services Utilized
- Amazon Simple Email Service (aka Amazon SES)
- Amazon Simple Notification Service (aka Amazon SNS)
- Amazon Simple Storage Service (aka Amazon S3)
- AWS Lambda