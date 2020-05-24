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
                print(responseFromGoogle.json())
                if responseFromGoogle.status_code != 200:
                    returnDict["body"] = json.dumps({"Error": "ReCaptcha validation failed"})
                elif responseFromGoogle.json()["success"] == False:     
                    returnDict["statusCode"] = 200
                    returnDict["body"] = json.dumps({"Error": "ReCaptcha validation failed.", 
                                                     "error-codes": responseFromGoogle.json().get("error-codes", ["not provided."])})
                elif responseFromGoogle.json()["score"] < 0.5:
                    returnDict["statusCode"] = 200
                    returnDict["body"] = json.dumps({"Error": "Score below threshhold"})
        except Exception as e:
            print(e)                 
            returnDict["body"] = json.dumps({"Error": "Exception occurred"})
        finally:
            return returnDict