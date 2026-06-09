"""Microsoft 365 (Graph) connector — INTERFACE STUB (PRD A1.1, A1.5).

This is the no-install telemetry path: pull calendar, meeting/call, and file
activity METADATA from the client's M365 tenant after admin consent. It needs a
registered Azure AD app + real tenant credentials, so it cannot run or be tested
here — the body below is the shape to fill in.

Install when implementing:  pip install msal requests
"""
from datetime import datetime


def authenticate(tenant_id: str, client_id: str, client_secret: str):
    """Return an access token via MSAL client-credentials flow.

    TODO:
        import msal
        app = msal.ConfidentialClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant_id}", client_credential=client_secret)
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return result["access_token"]
    """
    raise NotImplementedError("Fill in MSAL client-credentials flow.")


def pull_calendar(token: str, user_id: str, start: datetime, end: datetime) -> list[dict]:
    """GET /users/{id}/calendarView?startDateTime=..&endDateTime=.. → meeting events.

    Return rows ready for /events with category='meeting', metadata only
    (start, end, attendee_count, subject-category). NEVER store body content.
    """
    raise NotImplementedError("Call Graph calendarView and map to event rows.")


def pull_call_logs(token: str, user_id: str, start: datetime, end: datetime) -> list[dict]:
    """Teams call records → ACTUAL join/leave times (vs. just the booking)."""
    raise NotImplementedError("Call Graph communications/callRecords.")
