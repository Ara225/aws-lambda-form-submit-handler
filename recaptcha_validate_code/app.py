import json
import requests
from os import environ
import boto3
from base64 import b64decode

def lambda_handler(event, context):
    """
    Extremely simple function which takes in a recaptcha validation key, goes out to Google to 
    validate it, and returns the result. The secret key is stored in an encrypted environment variable managed by SAM 
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
    # Decrypt the environment variable
    recaptchaKey = boto3.client('kms').decrypt(CiphertextBlob=b64decode(environ['recaptchaKey']))['Plaintext'].decode('utf-8')
    if event["httpMethod"] == "POST":
        try:
            if not event["body"]:
                return {
                    "statusCode": 500,
                    'headers': {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                    },
                    "body": json.dumps({
                        "Error": "Empty body"
                    }),
                }
            else:
                respon = requests.post("https://www.google.com/recaptcha/api/siteverify", {"secret": recaptchaKey, 
                "response": event["body"]})
                print(respon.text)
                return {
                    "statusCode": 200,
                    'headers': {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                    },
                    "body": json.dumps({
                        "message": respon.json()
                    }),
                }
        except Exception as e:
            print(e)                 
            return {
                "statusCode": 500,
                'headers': {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({
                    "message": "Exception occurred"
                }),
            }