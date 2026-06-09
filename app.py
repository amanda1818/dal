"""Google Workspace connector — INTERFACE STUB (PRD A1.2).

No-install telemetry from the client's Workspace after admin consent: Calendar,
Gmail metadata, Drive activity, Meet logs. Needs a Google Cloud project with a
service account + domain-wide delegation, so it can't be tested here.

Install when implementing:  pip install google-api-python-client google-auth
"""
from datetime import datetime


def build_service(service_account_json: str, subject_email: str):
    """Return an authorised Calendar/Drive/Reports service via domain-wide delegation.

    TODO:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(service_account_json, scopes=[...]).with_subject(subject_email)
        return build("calendar", "v3", credentials=creds)
    """
    raise NotImplementedError("Fill in Google service-account delegation.")


def pull_calendar(service, start: datetime, end: datetime) -> list[dict]:
    """events().list(...) → meeting rows (metadata only) for /events."""
    raise NotImplementedError("Call Calendar events().list and map to event rows.")
