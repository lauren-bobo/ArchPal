# AWS S3 Setup Guide for ArchPal

This guide walks you through setting up AWS S3 storage for user data, conversation history, and conversation data.

## Prerequisites

- AWS Account with appropriate permissions
- AWS Access Key ID and Secret Access Key (or IAM role with S3 permissions)
- Existing Cognito User Pool (already configured)

## Step 1: Create S3 Bucket

1. **Navigate to S3 Console**
   - Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
   - Click "Create bucket"

2. **Configure Bucket Settings**
   - **Bucket name**: Choose a unique name (e.g., `archpal-user-data-prod`)
     - Must be globally unique across all AWS accounts
     - Use lowercase letters, numbers, and hyphens only
   - **AWS Region**: Select the same region as your Cognito User Pool (e.g., `us-east-1`)
   - **Object Ownership**: Choose "ACLs disabled (recommended)"
   - **Block Public Access**: Keep all settings enabled (default)
   - **Bucket Versioning**: Enable if you want to track changes (optional)
   - **Default encryption**: Enable (recommended)
     - Choose "AWS managed keys (SSE-S3)" or "AWS KMS" for stronger encryption

3. **Create Bucket**
   - Click "Create bucket"
   - **Note the bucket name** - you'll need it for `secrets.toml`

## Step 2: Configure IAM Permissions

### Option A: Using Existing IAM User (Recommended for Development)

If you're using AWS Access Keys from an existing IAM user:

1. **Navigate to IAM Console**
   - Go to [IAM Console](https://console.aws.amazon.com/iam/)
   - Click "Users" → Select your user

2. **Attach S3 Policy**
   - Click "Add permissions" → "Attach policies directly"
   - Search for and attach: `AmazonS3FullAccess` (for development)
   - OR create a custom policy with minimal permissions (see Option B)

### Option B: Create Custom IAM Policy (Recommended for Production)

1. **Create Policy**
   - Go to IAM Console → "Policies" → "Create policy"
   - Click "JSON" tab and paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME/*",
                "arn:aws:s3:::YOUR-BUCKET-NAME"
            ]
        }
    ]
}
```

2. **Replace `YOUR-BUCKET-NAME`** with your actual bucket name
3. **Name the policy**: `ArchPalS3Access`
4. **Attach to your IAM user**

## Step 3: Get AWS Credentials

### If Using IAM User Access Keys:

1. **Navigate to IAM Console**
   - Go to [IAM Console](https://console.aws.amazon.com/iam/)
   - Click "Users" → Select your user
   - Click "Security credentials" tab

2. **Create Access Key** (if you don't have one)
   - Click "Create access key"
   - Choose "Application running outside AWS"
   - Click "Next" → "Create access key"
   - **Copy both values immediately** (you won't see the secret again):
     - Access key ID
     - Secret access key

### If Using IAM Role (for EC2/ECS/Lambda):

- The role should already have S3 permissions attached
- No access keys needed - boto3 will use the role automatically

## Step 4: Configure secrets.toml

Add the following to your `.streamlit/secrets.toml` file:

```toml
# ============================================
# AWS S3 Configuration
# ============================================
# Get these values from AWS Console:
# 1. Bucket name: S3 Console → Your bucket → Copy bucket name
# 2. Region: S3 Console → Your bucket → Properties → AWS Region
# 3. Access keys: IAM Console → Users → Your user → Security credentials

# S3 Bucket Name (from Step 1)
# Example: "archpal-user-data-prod"
s3_bucket_name = "YOUR-BUCKET-NAME-HERE"

# S3 Region (must match your bucket region)
# Example: "us-east-1"
s3_region = "us-east-1"

# AWS Access Key ID (from Step 3)
# If using IAM role, this can be empty
aws_access_key_id = "YOUR-ACCESS-KEY-ID-HERE"

# AWS Secret Access Key (from Step 3)
# If using IAM role, this can be empty
aws_secret_access_key = "YOUR-SECRET-ACCESS-KEY-HERE"

# Note: If you're already using AWS credentials for Bedrock,
# you can reuse the same credentials (aws_access_key_id and aws_secret_access_key)
# that are already in your secrets.toml file
```

## Step 5: Verify Setup

### Test S3 Access

1. **Run your Streamlit app**
2. **Login with Cognito**
3. **Fill out the user info form**
4. **Check S3 Console**:
   - Navigate to your bucket
   - You should see a folder structure:
     ```
     users/
       {cognito_user_id}/
         info.json
         conversations.json
         conversations/
           {conversation_id}.json
     ```

## Troubleshooting

### Error: "Access Denied" or "403 Forbidden"
- **Check IAM permissions**: Ensure your IAM user/role has S3 permissions
- **Check bucket policy**: Ensure bucket allows your IAM user/role
- **Verify credentials**: Double-check access key ID and secret in `secrets.toml`

### Error: "Bucket does not exist" or "404 Not Found"
- **Verify bucket name**: Check for typos in `s3_bucket_name` in `secrets.toml`
- **Check region**: Ensure `s3_region` matches your bucket's region
- **Verify bucket exists**: Check S3 Console to confirm bucket exists

### Error: "Invalid credentials"
- **Regenerate access keys**: Create new access keys in IAM Console
- **Check secret key**: Ensure no extra spaces or quotes in `secrets.toml`
- **Verify key format**: Access keys should be alphanumeric strings

### Error: "Region mismatch"
- **Check region**: Ensure `s3_region` in `secrets.toml` matches bucket region
- **Find bucket region**: S3 Console → Your bucket → Properties → AWS Region

## Security Best Practices

1. **Never commit secrets.toml** to version control
2. **Use IAM roles** instead of access keys when possible (EC2/ECS/Lambda)
3. **Rotate access keys** regularly (every 90 days recommended)
4. **Use least privilege**: Only grant S3 permissions needed for your bucket
5. **Enable bucket encryption**: Use SSE-S3 or SSE-KMS
6. **Enable bucket versioning**: For data recovery (optional)
7. **Set up CloudTrail**: To audit S3 access (optional)

## Cost Considerations

- **S3 Standard Storage**: ~$0.023 per GB/month
- **PUT requests**: ~$0.005 per 1,000 requests
- **GET requests**: ~$0.0004 per 1,000 requests
- **Data transfer**: Free within same region

For a typical ArchPal deployment:
- Storage: Minimal (JSON files are small)
- Requests: ~$0.01-0.10/month per 100 active users
- **Estimated cost**: < $1/month for small deployments

## Next Steps

After completing setup:
1. Test user info storage (login → fill form → check S3)
2. Test conversation creation (send message → check S3)
3. Test conversation history (check sidebar loads conversations)
4. Monitor S3 usage in AWS Console

## Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [S3 Pricing Calculator](https://calculator.aws/)
