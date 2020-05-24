# Summary 
This is a simple AWS Lambda function written in Python that validates a ReCaptcha response token sent to it by client-side code, and if validation is successful, sends an email via AWS SES containing the form data.

It has JavaScript turn the form into JSON on the client side by iterating over the form fields before sending the data over (see the HTML 
file), which saves on a couple of things; the browser doesn't do a automatic redirect to POST destination as with normal form submit, and 
form fields can easily be ignored in the submission if desired. 

# Setting up
This uses AWS SAM to set up the environment, which makes it quite easy to deploy the stack. However, there's still a few things to do with this template, so it's not all as automated as I'd like

## Steps

### Check Setup
* Ensure that the from and to email address you want are setup in SES as needed
* Ensure that the ReCaptcha key is encrypted with a KMS key. If you do this via the Lambada GUI after deploying the stack, it needs to be a custom key
* To handle decrypting the key the lambada IAM user role will need access to decrypt with the key the ReCaptcha key is encrypted with, and also have access to send 
  email with SES. The template doesn't currently do this, so you need to add them manually after creating the stack with SAM deploy

### Configure Environment Variables
* Complete the emailFrom field in the template.yaml with the email you want to have the form data sent from 
* Complete the emailTo field with one email or a comma separated email list
* Complete the recaptchaKey field with your secret ReCaptcha key - this is expected to be encrypted with AWS KMS, but the code can easily be changed 
  to let plaintext work

### Deploy
AWS does a pretty good job of walking you though the steps, so I'm just going to refer you to the [developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for this bit. It's pretty unexceptional

### Test
There aren't currently any automated tests here - with the whole ReCaptcha thing, it's a bit difficult, but the sample client code HTML file should serve as a basic 
test - just change the URL and site key in it, load it into a web server, and click submit.

# Known Problems
* It doesn't validate URLs at the moment (Google does do this, but it'd still be nice to do)
* Doesn't setup key or IAM permissions properly on it's own
