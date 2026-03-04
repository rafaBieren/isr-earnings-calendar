import os

import resend


def send_error_email(job_name: str, error_msg: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("ALERT_EMAIL")

    if not api_key or not to_email:
        print("Resend credentials not found in env vars. Skipping email alert.")
        return

    resend.api_key = api_key

    subject = (
        f"\u26a0\ufe0f \u05e9\u05d2\u05d9\u05d0\u05d4 "
        f"\u05d1\u05e1\u05e7\u05e8\u05d9\u05d9\u05e4\u05e8 "
        f"\u05e9\u05dc \u05de\u05d0\u05d9\u05d4: {job_name}"
    )
    body = (
        f"\u05d4\u05ea\u05e8\u05d7\u05e9\u05d4 \u05e9\u05d2\u05d9\u05d0\u05d4 "
        f"\u05d1\u05de\u05d4\u05dc\u05da \u05e8\u05d9\u05e6\u05ea \u05de\u05e9\u05d9"
        f"\u05de\u05ea {job_name}:\n\n{error_msg}\n\n"
        "Please check the Railway logs."
    )

    params = {
        "from": "onboarding@resend.dev",
        "to": [to_email],
        "subject": subject,
        "text": body,
    }

    try:
        email_response = resend.Emails.send(params)
        print(
            "Error alert email sent successfully for "
            f"{job_name}. Resend ID: {email_response.get('id', 'unknown')}"
        )
    except Exception as e:
        print(f"Failed to send alert email via Resend: {e}")
