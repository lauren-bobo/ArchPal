# Pre-Signup Lambda Trigger Setup

This Lambda function enforces @uga.edu email validation during Cognito signup.

## AWS Console Setup

### 1. Create Lambda Function

1. Go to **AWS Lambda Console** → **Create function**
2. Choose **Author from scratch**
3. Configuration:
   - **Function name**: `cognito-presignup-uga-validator`
   - **Runtime**: Node.js 20.x (or latest)
   - **Architecture**: x86_64
   - **Execution role**: Create new role with basic Lambda permissions
4. Click **Create function**

### 2. Add Function Code

1. In the Lambda function editor, replace the code with the contents of `pre-signup-validator.mjs`
2. Click **Deploy**

### 3. Add Cognito Permission

1. Go to **Configuration** → **Permissions**
2. Click on the **Execution role** link (opens IAM)
3. The default Lambda execution role is sufficient for this function

### 4. Attach Lambda to Cognito User Pool

1. Go to **AWS Cognito Console** → User Pool `rzpit2`
2. Click **User pool properties** tab
3. Scroll to **Lambda triggers**
4. Click **Add Lambda trigger**
5. Select trigger type: **Pre sign-up**
6. Select your Lambda function: `cognito-presignup-uga-validator`
7. Click **Save changes**

## Test

1. Try signing up with a non-UGA email (e.g., `test@gmail.com`)
   - Should fail with error: "Only @uga.edu email addresses are allowed"
2. Try signing up with a UGA email (e.g., `test@uga.edu`)
   - Should succeed and auto-confirm

## Troubleshooting

If validation isn't working:
1. Check Lambda logs in **CloudWatch Logs**
2. Verify the trigger is attached in Cognito User Pool properties
3. Ensure Lambda has the correct permissions
