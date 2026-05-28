import os
import json


def is_cloud():
    """Detect if running on GCP VM."""
    if os.environ.get("GOOGLE_CLOUD", "").lower() in ("1", "true"):
        return True
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/",
            headers={"Metadata-Flavor": "Google"},
        )
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False


def get_project_id():
    """Get GCP project ID from environment or default."""
    return os.environ.get("CONNECTOR_PROJECT", "msr-msia-sales-analysis")


def get_secret(secret_id, project_id=None):
    """Retrieve a secret from local file first, then GCP Secret Manager."""
    local_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "secrets_local.json"
    )
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            secrets = json.load(f)
        if secret_id in secrets:
            return secrets[secret_id]

    if project_id is None:
        project_id = get_project_id()

    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_secret_json(secret_id, project_id=None):
    """Retrieve and parse a JSON secret."""
    return json.loads(get_secret(secret_id, project_id))