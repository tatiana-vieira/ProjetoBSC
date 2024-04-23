import sendgrid
from sendgrid import Mail  # For newer versions
from sendgrid.helpers.mail import Mail  # For older versions (check documentation)

def send_email(from_email, to_emails, subject, html_content, api_key):
    sg = sendgrid.SendGridAPIClient(apikey=api_key)

    message = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        html_content=html_content
    )

    response = sg.send(message)
    return response
