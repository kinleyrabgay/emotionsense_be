# Deploying to Render

This guide will help you deploy the Emotion Detection API to [Render](https://render.com).

## Pre-requisites

1. A Render account
2. A MongoDB Atlas account (or other MongoDB provider)
3. Your project code in a Git repository (GitHub, GitLab, etc.)

## Setup

### 1. MongoDB Atlas Setup

1. Create a MongoDB Atlas cluster if you don't have one
2. Create a database named `emotionsense`
3. Create a database user with read/write permissions
4. Get your connection string from MongoDB Atlas:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/emotionsense
   ```

### 2. Render Deployment

#### Option 1: Using the Dashboard

1. Log in to your Render dashboard
2. Click "New" and select "Web Service"
3. Connect your Git repository
4. Configure the service:
   - **Name**: `emotion-detection-api` (or your preferred name)
   - **Runtime**: `Python`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
   - **Health Check Path**: `/health`
5. Add environment variables:
   - `DATABASE_URL`: Your MongoDB connection string
   - `SECRET_KEY`: A secret key for JWT token encryption
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440` (or your preferred value)
6. Click "Create Web Service"

#### Option 2: Using Blueprint (render.yaml)

1. Log in to your Render dashboard
2. Click "New" and select "Blueprint"
3. Connect your Git repository
4. Render will detect the `render.yaml` file and set up your services
5. Provide the required environment variables when prompted
6. Deploy your services

## Verifying Deployment

After deployment completes:

1. Go to your Render dashboard and click on your web service
2. Click on the URL to access your API
3. Navigate to `/docs` to see the Swagger UI documentation
4. Test the API endpoints to ensure everything is working properly

## Troubleshooting

If you encounter issues:

1. Check the Render logs for error messages
2. Verify your MongoDB connection string is correct
3. Ensure all environment variables are set properly
4. Check the application logs for specific errors

## Resources

- [Render Documentation](https://render.com/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)

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