import json
import boto3
import requests
import os

def lambda_handler(event, context):
    # Fetch environment variables
    app_id = os.environ['ADZUNA_APP_ID']
    app_key = os.environ['ADZUNA_APP_KEY']
    bucket_name = os.environ['S3_BUCKET_NAME']
    
    # API endpoint
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    # List of job roles
    job_roles = [
        "software engineer", "data engineer", "machine learning engineer",
        "backend developer", "devops engineer", "data analyst", "AI Engineer"
    ]

    # Initialize S3 client
    s3 = boto3.client('s3')

    for role in job_roles:
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 50,
            "what": role,
            "where": "India",
            "content-type": "application/json"
        }

        # Call API
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()

            # Format role name for filename
            role_slug = role.lower().replace(" ", "_")
            s3_key = f"raw/job_data/adzuna_job_posting_data_{role_slug}.json"

            # Upload to S3
            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=json.dumps(data))
        else:
            print(f"❌ Failed to fetch data for role: {role} | Status Code: {response.status_code}")

    return {
        'statusCode': 200,
        'body': json.dumps('✅ Job data for all roles uploaded to S3 successfully!')
    }