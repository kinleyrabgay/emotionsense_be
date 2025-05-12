# Deploying Emotion Detection Backend to Render (Free Tier)

This guide will walk you through deploying the Emotion Detection backend to Render's free tier.

## Prerequisites

1. A GitHub account
2. A Render account (sign up at [render.com](https://render.com) - no credit card required for free tier)
3. Your project code ready to push to GitHub

## Setup Steps

### 1. Push Your Code to GitHub

First, ensure your code is in a GitHub repository:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Create a PostgreSQL Database on Render

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click on **New** and select **PostgreSQL**
3. Enter the following details:
   - **Name**: `emotion-detection-db`
   - **Plan**: Free
   - Leave other settings as default

4. Click **Create Database**
5. Note the **Internal Database URL** for the next step

### 3. Create a Web Service

1. From the Render dashboard, click **New** and select **Web Service**
2. Select **Build and deploy from a Git repository**
3. Connect your GitHub repository
4. Enter the following details:
   - **Name**: `emotion-detection-api`
   - **Runtime**: Python
   - **Build Command**: `bash build.sh`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

5. Add the following environment variables:
   - `DATABASE_URL`: The Internal Database URL from your PostgreSQL service
   - `SECRET_KEY`: [Generate a random string](https://passwordsgenerator.net/) or use Render's auto-generate feature
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: 1440

6. Click **Create Web Service**

### 4. Automatic Deployment from render.yaml

Alternatively, you can use the included `render.yaml` file for blueprint deployment:

1. From the Render dashboard, click **New** and select **Blueprint**
2. Connect your GitHub repository
3. Render will automatically detect the `render.yaml` file and set up the services
4. Review the settings and click **Apply**

### 5. Monitor Deployment

1. Watch the deployment logs to ensure everything is set up correctly
2. Once deployed, you can access your API at `https://emotion-detection-api.onrender.com`
3. The API documentation will be available at `https://emotion-detection-api.onrender.com/docs`

### 6. Test the API

1. Use the Swagger documentation at `/docs` to test the API endpoints
2. Try registering a user and logging in to verify authentication is working
3. Test the WebSocket connection using a client like Postman or a custom Flutter app

## Important Notes About Free Tier

1. **Sleep Mode**: Free services on Render will "sleep" after 15 minutes of inactivity. The first request after inactivity will take longer as the service spins up (~30 seconds).

2. **Resource Constraints**: Free tier has limited CPU and RAM. Avoid heavy computations or large payloads.

3. **Database Limitations**: The free PostgreSQL has a 1GB storage limit. Monitor usage to avoid reaching the limit.

4. **No Custom Domains**: Free tier uses Render's subdomain (`onrender.com`).

## Troubleshooting

### Common Issues and Solutions

1. **Database Connection Errors**:
   - Verify the `DATABASE_URL` environment variable is correctly set
   - Ensure the database is running (check Render dashboard)
   - Check if you're within the connection limit of the free tier

2. **Application Crashes**:
   - Check the logs in the Render dashboard
   - Verify all required environment variables are set
   - Ensure your code works locally before deploying

3. **Slow Initial Response**:
   - This is normal for free tier services due to the "sleep" feature
   - Subsequent requests will be faster until the service goes back to sleep

4. **Build Failures**:
   - Check if all dependencies are properly listed in `requirements.txt`
   - Ensure `build.sh` has execute permissions (`chmod +x build.sh`)
   - Review build logs for specific errors

5. **WebSocket Connection Issues**:
   - Use secure WebSocket protocol (`wss://`) instead of `ws://`
   - Make sure clients include the proper authentication token
   - Check Render's WebSocket documentation for any limitations

### Getting Help

If you're still having issues, you can:
- Check Render's [documentation](https://render.com/docs)
- Review the [FastAPI documentation](https://fastapi.tiangolo.com/)
- Consult the `websocket_README.md` file for specific WebSocket implementation details

## Upgrading Later

If you need to upgrade beyond the free tier:
1. Go to your service in the Render dashboard
2. Click on **Settings**
3. Under **Instance Type**, select a higher tier
4. Confirm the change

Upgrading will give you more resources, eliminate sleep mode, and allow for custom domains.

## Cost Management

- Monitor the usage metrics in your Render dashboard
- Set up billing alerts to avoid unexpected charges if you upgrade
- Remember that the free tier is sufficient for development and small-scale testing

## Deploy Notes for Face Recognition

The face recognition feature requires additional system dependencies when using the preferred `face_recognition` library. Render's free tier may have limitations for installing these dependencies. You have two options:

### Option 1: Use the OpenCV Fallback (Recommended for Free Tier)

The system automatically falls back to OpenCV if `face_recognition` is not available. This approach:
- Requires fewer system dependencies
- Is more compatible with Render's free tier
- Has lower accuracy but is functional for basic use cases

1. Ensure `opencv-python` is in your requirements.txt (it already is).
2. No additional configuration is needed - the fallback activates automatically.

### Option 2: Install Full Dependencies (May require paid tier)

If you need the higher accuracy of the full `face_recognition` library:

1. Ensure your `build.sh` file includes the necessary system installations:
   ```bash
   #!/usr/bin/env bash
   # Exit on error
   set -o errexit

   # Install system dependencies for face_recognition
   apt-get update
   apt-get install -y --no-install-recommends \
       build-essential \
       cmake \
       libopenblas-dev \
       liblapack-dev \
       libx11-dev \
       libgtk-3-dev

   # Install Python dependencies
   pip install -r requirements.txt
   
   # Create .env file if it doesn't exist
   if [ ! -f .env ]; then
       echo "Creating .env file"
       echo "DATABASE_URL=$DATABASE_URL" > .env
       echo "SECRET_KEY=$SECRET_KEY" >> .env
       echo "ACCESS_TOKEN_EXPIRE_MINUTES=$ACCESS_TOKEN_EXPIRE_MINUTES" >> .env
   fi
   ```

2. Make the build script executable:
   ```bash
   chmod +x build.sh
   ```

3. You may need to upgrade to a paid tier on Render that provides sufficient resources for building these dependencies.

### Monitoring Face Recognition Performance

1. Check the application logs in Render dashboard to see which recognition method is being used.
2. Look for log entries like:
   - "Using face_recognition library for face detection and encoding" (primary method)
   - "Using OpenCV for face detection and encoding (fallback mode)" (fallback method)

3. If using the fallback method, you may need to adjust the tolerance value in the code for better accuracy. 