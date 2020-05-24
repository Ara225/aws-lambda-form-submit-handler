# Recaptcha Validate
Extremely simple function which takes in a recaptcha validation key, goes out to Google to 
validate it, and returns the result. The secret key is stored in an encrypted environment variable managed by SAM called recaptchaKey