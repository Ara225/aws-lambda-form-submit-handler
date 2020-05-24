import json
import requests
from os import environ
import boto3
from base64 import b64decode

def send_email(formData):
    """
    Function to send the email via AWS's Simple Email Service
    Parameters
    ----------
    formData: dict, required
        Form data as JSON

    Returns
    ------
    Nothing
    """
    # The subject line for the email.
    emailSubject = "Form Submitted"
    formDataAsHTML = ""
    formDataAsText = ""
    for item in formData:
        # Exclude the Google form field
        if item == "g-recaptcha-response":
            continue
        formDataAsHTML += "<p>The form field with the name " + item + " had the value " + formData[item] + "</p>"
        formDataAsText += "The form field with the name " + item + " had the value " + formData[item] + "\r\n"

    # The email body for recipients with non-HTML email clients.
    emailTextBody = ("Form Submission Data\r\n" + formDataAsText)
    # The HTML body of the email.
    emailHTMLBody = """<html>
                        <head></head>
                        <body>
                          <h1>Form Submission Data</h1>""" + formDataAsHTML + """
                        </body>
                    </html>
                """            
    # The character encoding for the email.
    charset = "UTF-8"
    
    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name="eu-west-2")

    #Provide the contents of the email.
    response = client.send_email(
        Destination={
            'ToAddresses': environ["emailTo"].split(","),
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': charset,
                    'Data': emailHTMLBody,
                },
                'Text': {
                    'Charset': charset,
                    'Data': emailTextBody,
                },
            },
            'Subject': {
                'Charset': charset,
                'Data': emailSubject,
            },
        },
        Source=environ["emailFrom"]
    )


def lambda_handler(event, context):
    """
    Simple function which takes in a recaptcha validation key and form data (in JSON format), goes out to Google to 
    validate it, and sends it via email. The secret recaptcha key is stored in an encrypted environment variable managed by SAM 
    called recaptchaKey
    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    if event["httpMethod"] == "POST":
        # Decrypt the environment variable
        recaptchaKey = boto3.client('kms').decrypt(CiphertextBlob=b64decode(environ['recaptchaKey']))['Plaintext'].decode('utf-8')
        # Remove the Access-Control-Allow-* headers if requests will always be from the same domain
        returnDict = {
                        "statusCode": 500,
                        'headers': {
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Headers": "Content-Type",
                            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                        }
                    }
        try:
            if not event["body"]:
                returnDict["body"] = json.dumps({"Error": "Empty body"})
            else:
                body = json.loads(event["body"])
                responseFromGoogle = requests.post("https://www.google.com/recaptcha/api/siteverify", {"secret": recaptchaKey, 
                "response": body["g-recaptcha-response"]})
                # Fallback - failure should be indicated by success being False not a HTTP error
                if responseFromGoogle.status_code != 200:
                    returnDict["body"] = json.dumps({"Error": "ReCaptcha validation failed"})
                # If the request failed
                elif responseFromGoogle.json()["success"] == False:     
                    returnDict["statusCode"] = 200
                    returnDict["body"] = json.dumps({"Error": "ReCaptcha validation failed.", 
                                                     "error-codes": responseFromGoogle.json().get("error-codes", [])
                                                   })
                elif responseFromGoogle.json()["score"] < 0.5:
                    returnDict["statusCode"] = 200
                    returnDict["body"] = json.dumps({"Error": "Score below threshhold"})
                else:
                    try:
                        send_email(body)
                        returnDict["statusCode"] = 200
                        returnDict["body"] = json.dumps({"message": "Email sent successfully"})
                        print("Email sent!")
                    except Exception as e:
                        print(e.response['Error']['Message'])
                        returnDict["body"] = json.dumps({"Error": "Unable to send email"})
        except Exception as e:
            print(e)                 
            returnDict["body"] = json.dumps({"Error": "Exception occurred"})
        finally:
            return returnDict