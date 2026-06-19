import dotenv
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
dotenv.load_dotenv()
# 1. Initialize the configuration and API client
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SMTP_KEY")

api_client = sib_api_v3_sdk.ApiClient(configuration)

# 2. Use the TransactionalEmailsApi class
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)

# 3. Define variables dynamically inside your app logic
user_email = "indrajit0071998@gmail.com"
user_name = "Ajoy Prasad"
reset_token = "abc123xyz_secure_token"
reset_link = f"https://yourapp.com{reset_token}"

# 4. Construct the immediate transactional email object
send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
    sender={"name": "Your App Security", "email": "ajoyprasad2002217@gmail.com"},
    to=[{"email": user_email, "name": user_name}],
    subject="Reset Your Password",
    html_content=f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {user_name},</p>
            <p>We received a request to reset your password. Click the button below to choose a new one. This link expires in 1 hour.</p>
            <p><a href="{reset_link}" style="background-color:#0076FF; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; display:inline-block;">Reset Password</a></p>
            <p>If you didn't request this, you can safely ignore this email.</p>
        </body>
    </html>
    """
)

# 5. Send the email instantly
try:
    api_response = api_instance.send_transac_email(send_smtp_email)
    print("Password reset email sent successfully!")
    print(f"Message ID: {api_response.message_id}")
except ApiException as e:
    print(f"Failed to send password reset: {e}")
