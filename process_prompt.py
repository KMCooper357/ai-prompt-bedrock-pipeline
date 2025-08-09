import os
import json
from pathlib import Path
import boto3
from jinja2 import Template

# Constants
BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

def render_template(template_path, variables):
    with open(template_path) as f:
        template = Template(f.read())
    return template.render(**variables)

def call_bedrock(prompt, max_tokens=1024):
    region = os.environ.get("AWS_REGION")
    if not region:
        raise ValueError("AWS_REGION environment variable is not set.")

    client = boto3.client("bedrock-runtime", region_name=region)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": f"Human: {prompt}"
            }
        ]
    }

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body)
    )

    response_body = json.loads(response["body"].read())
    content = response_body.get("content", [])

    if isinstance(content, list):
        return "".join([block.get("text", "") for block in content])
    return content

def upload_to_s3(file_path, bucket_name, key):
    s3 = boto3.client("s3")
    s3.upload_file(str(file_path), bucket_name, key)
    print(f"[S3 Upload] s3://{bucket_name}/{key}")

def copy_to_root_index(bucket_name, source_key):
    s3 = boto3.client("s3")
    s3.copy_object(
        Bucket=bucket_name,
        CopySource={'Bucket': bucket_name, 'Key': source_key},
        Key="index.html",
        ContentType='text/html',
        MetadataDirective='REPLACE'
    )
    print(f"[S3 Copy] {source_key} → index.html")

def main(env, bucket):
    prompts_dir = Path("prompts")
    templates_dir = Path("prompt_templates")
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    for prompt_file in prompts_dir.glob("*.json"):
        with open(prompt_file) as f:
            config = json.load(f)

        template_file = templates_dir / prompt_file.name.replace(".json", ".txt")
        if not template_file.exists():
            print(f"[WARN] Template missing for {prompt_file.name}. Skipping.")
            continue

        # Render + send to Bedrock
        rendered_prompt = render_template(template_file, config)
        bedrock_response = call_bedrock(rendered_prompt)

        # Write output
        output_ext = config.get("output_format", "html")
        output_filename = prompt_file.stem + f".{output_ext}"
        output_path = outputs_dir / output_filename

        with open(output_path, "w") as out_f:
            out_f.write(bedrock_response)

        # Upload to S3 path
        s3_key = f"{env}/outputs/{output_filename}"
        upload_to_s3(output_path, bucket, s3_key)

        # Copy to root index.html
        copy_to_root_index(bucket, s3_key)

def main(env: str = "beta") -> None:
    region = get_region()
    s3 = boto3.client("s3", region_name=region)

    bucket = (
        os.getenv("S3_BUCKET_BETA")
        if env == "beta"
        else os.getenv("S3_BUCKET_PROD")
    )
    if not bucket:
        raise ValueError(
            f"[❌] No S3 bucket defined for environment '{env}'.\n"
            f"➡️  Set {'S3_BUCKET_BETA' if env == 'beta' else 'S3_BUCKET_PROD'}."
        )

    # rest of your code...

