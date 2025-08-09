# ai-prompt-bedrock-pipeline

This project automates the generation and deployment of AI-generated HTML content using Amazon Bedrock and AWS S3, triggered by GitHub workflows.

---

## What It Does

- Renders Jinja2-based prompt templates with dynamic variables
- Sends prompts to **Claude 3 Sonnet** via **Amazon Bedrock**
- Generates personalized HTML content
- Uploads outputs to S3 static website buckets (`beta` and `prod`)
- Uses GitHub Actions to automate testing and production deployments

---

## 🛠 Setup Guide

### 1. Set Up AWS Resources

####  Create S3 Buckets
Use the AWS CLI:

```bash
aws s3 mb s3://plc-content-beta
aws s3 mb s3://plc-content-prod
Enable static website hosting:

bash
Copy
Edit
aws s3 website s3://plc-content-beta --index-document index.html
aws s3 website s3://plc-content-prod --index-document index.html
 Make Buckets Public (Optional)
Use this bucket policy for public-read access:

json
Copy
Edit
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::plc-content-prod/*"
    }
  ]
}
 For production, consider using CloudFront + OAC for security.

2. Enable Amazon Bedrock & Claude 3
Go to the Amazon Bedrock console.

Enable Claude 3 Sonnet:

yaml
Copy
Edit
Model ID: anthropic.claude-3-sonnet-20240229-v1:0
Accept any terms & permissions.

Ensure your IAM role/user has permission to invoke Bedrock.

3. Project Structure
text
Copy
Edit
.
├── prompts/
│   └── welcome_prompt.json
├── prompt_templates/
│   └── welcome.txt
├── outputs/
├── .github/
│   └── workflows/
│       ├── on_pull_request.yml
│       └── on_merge.yml
├── generate_and_upload.py
└── README.md
 How to Use
A. Create a Prompt Template
prompt_templates/welcome.txt

text
Copy
Edit
Hi {{student_name}},

Welcome to Pixel Learning Co. Here are three quick tips:
1. {{tip1}}
2. {{tip2}}
3. {{tip3}}

Happy learning!
B. Create a Prompt Configuration
prompts/welcome_prompt.json

json
Copy
Edit
{
  "output_file": "welcome_{{student_name|lower}}.html",
  "variables": {
    "student_name": "Jordan",
    "tip1": "Explore the course dashboard",
    "tip2": "Join the forum",
    "tip3": "Set study reminders"
  },
  "make_index": true
}
 GitHub Secrets Configuration
Go to Repository Settings → Secrets → Actions, and add:

Secret Name	Value
AWS_ACCESS_KEY_ID	Your AWS access key
AWS_SECRET_ACCESS_KEY	Your AWS secret key
AWS_REGION	e.g., us-east-1
S3_BUCKET_BETA	e.g., plc-content-beta
S3_BUCKET_PROD	e.g., plc-content-prod

 GitHub Workflows
 On Pull Request: Test in Beta
.github/workflows/on_pull_request.yml

yaml
Copy
Edit
name: Beta Prompt Test

on:
  pull_request:
    branches: [main]

jobs:
  beta-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: pip install boto3 jinja2
      - name: Run Prompt Processor
        env:
          DEPLOY_ENV: beta
          AWS_REGION: ${{ secrets.AWS_REGION }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          S3_BUCKET_BETA: ${{ secrets.S3_BUCKET_BETA }}
        run: python generate_and_upload.py
 On Merge: Publish to Production
.github/workflows/on_merge.yml

yaml
Copy
Edit
name: Prod Prompt Publish

on:
  push:
    branches: [main]

jobs:
  prod-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: pip install boto3 jinja2
      - name: Run Prompt Processor
        env:
          DEPLOY_ENV: prod
          AWS_REGION: ${{ secrets.AWS_REGION }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          S3_BUCKET_PROD: ${{ secrets.S3_BUCKET_PROD }}
        run: python generate_and_upload.py
 View Generated Content
Once deployed, access your static website at:

arduino
Copy
Edit
http://plc-content-beta.s3-website-<region>.amazonaws.com
http://plc-content-prod.s3-website-<region>.amazonaws.com
Replace <region> with your actual AWS region (e.g., us-east-1).

 Key Benefits
Fully automated prompt → Claude → HTML → S3 workflow

Zero manual uploads or content pasting

Version-controlled generation pipeline

Easy staging (beta) and production workflows
