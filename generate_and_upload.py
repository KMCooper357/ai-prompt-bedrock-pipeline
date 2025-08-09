# generate_and_upload.py

import boto3
import os
import json
import pathlib
import jinja2
from jinja2 import Template

# ---------- Constants ----------
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
BETA_PREFIX = os.getenv("BETA_PREFIX", "beta/")
PROD_PREFIX = os.getenv("PROD_PREFIX", "prod/")

# ---------- Helpers ----------

def get_region() -> str:
    """Return AWS region from environment variables or raise an error."""
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if not region:
        raise ValueError(
            "[❌] No AWS region specified.\n"
            "➡️  Set AWS_REGION or AWS_DEFAULT_REGION (e.g., 'us-east-1')."
        )
    return region

def render_prompt(template_path: str, config: dict) -> str:
    """Render a Jinja2 template with variables from a config dictionary."""
    template = jinja2.Template(pathlib.Path(template_path).read_text())
    return template.render(**config["variables"])

def construct_body(prompt: str, max_tokens: int = 300) -> dict:
    """Create the request body for Bedrock model invocation."""
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": f"Human: {prompt}"}
        ],
    }

def call_bedrock(prompt: str, max_tokens: int, region: str) -> str:
    """Invoke Claude 3 Sonnet via Bedrock and return the model output."""
    br = boto3.client("bedrock-runtime", region_name=region)
    response = br.invoke_model(
        body=json.dumps(construct_body(prompt, max_tokens)),
        modelId=MODEL_ID,
    )
    result = json.loads(response["body"].read())
    return "".join(chunk["text"] for chunk in result["content"])

# ---------- Main Workflow ----------

def main(env: str = "beta") -> None:
    """Render prompts, generate completions, and upload outputs to S3."""
    region = get_region()
    s3 = boto3.client("s3", region_name=region)

    # Choose correct bucket based on environment
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

    prefix = BETA_PREFIX if env == "beta" else PROD_PREFIX
    pathlib.Path("outputs").mkdir(exist_ok=True)

    for config_path in pathlib.Path("prompts").glob("*.json"):
        cfg = json.loads(config_path.read_text())

        # 1️⃣ Render the prompt
        template_file = f"prompt_templates/{config_path.stem.replace('_prompt', '')}.txt"
        rendered_prompt = render_prompt(template_file, cfg)

        # 2️⃣ Render the output filename
        filename_rendered = Template(cfg["output_file"]).render(**cfg["variables"])

        # 3️⃣ Generate model completion
        completion = call_bedrock(rendered_prompt, max_tokens=300, region=region)

        # 4️⃣ Save output locally
        output_path = pathlib.Path("outputs") / filename_rendered
        output_path.write_text(completion, encoding="utf-8")

        # 5️⃣ Upload to S3
        s3_key = f"{prefix}{filename_rendered}"
        s3.upload_file(
            output_path.as_posix(),
            bucket,
            s3_key,
            ExtraArgs={"ContentType": "text/html"}
        )
        print(f"✅ Uploaded ➜ s3://{bucket}/{s3_key}")

        # 6️⃣ Optionally publish as index.html
        if cfg.get("make_index", False):
            index_key = f"{prefix}index.html"
            s3.upload_file(
                output_path.as_posix(),
                bucket,
                index_key,
                ExtraArgs={"ContentType": "text/html"}
            )
            print(f"↪️  Also published as ➜ s3://{bucket}/{index_key}")

if __name__ == "__main__":
    main(os.getenv("DEPLOY_ENV", "beta"))
