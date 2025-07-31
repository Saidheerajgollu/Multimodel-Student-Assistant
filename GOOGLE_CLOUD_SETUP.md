# Google Cloud Storage Setup Guide

This guide will help you set up Google Cloud Storage for persistent vector storage in your Streamlit app.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Cloud Storage API

## Step 2: Create a Storage Bucket

1. In the Cloud Console, go to **Cloud Storage > Buckets**
2. Click **Create Bucket**
3. Choose a unique name for your bucket (e.g., `my-study-assistant-data`)
4. Select a location close to you
5. Choose **Standard** storage class
6. Click **Create**

## Step 3: Create Service Account

1. Go to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**
3. Name it `streamlit-app-service-account`
4. Add description: `Service account for Streamlit app`
5. Click **Create and Continue**
6. Grant the **Storage Object Admin** role
7. Click **Done**

## Step 4: Generate Service Account Key

1. Click on your service account
2. Go to **Keys** tab
3. Click **Add Key > Create New Key**
4. Choose **JSON** format
5. Download the JSON file

## Step 5: Configure Streamlit Secrets

In your Streamlit Cloud app:

1. Go to your app settings
2. Add these secrets:

```toml
GOOGLE_CLOUD_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
'''

GOOGLE_CLOUD_BUCKET = "your-bucket-name"
```

## Step 6: Update Your App

The app will now:
- ✅ Store FAISS vector index in Google Cloud Storage
- ✅ Load existing data on app restart
- ✅ Work without SQLite dependency
- ✅ Persist data across deployments

## Troubleshooting

### Common Issues:

1. **Permission Denied**: Make sure your service account has Storage Object Admin role
2. **Bucket Not Found**: Verify the bucket name in secrets
3. **Invalid Credentials**: Check that the JSON key is properly formatted in secrets

### Local Development:

For local testing, you can use:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

## Benefits

- **No SQLite dependency**: Works on Streamlit Cloud
- **Persistent storage**: Data survives app restarts
- **Scalable**: Can handle large amounts of data
- **Secure**: Uses Google Cloud's security features 