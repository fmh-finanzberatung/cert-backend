import requests
from flask import Flask, request, jsonify, json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_caching import Cache

ALF_API_URL = "https://services1.fmh.de/webapi/banken-portal/graphql"
ALF_API_TOKEN = "JlrIZRj87Ozg30leAlPxBHIaqtTphjyc"

app = Flask(__name__)
CORS(app)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute", "1 per second"],
    storage_uri="memory://",
    strategy="fixed-window",  # or "moving-window"
)


@app.route('/certificates', methods=['POST'])
@cache.cached(timeout=3000)
def get_certificates():
    data = request.data
    requests_response = requests.post(
        url=ALF_API_URL,
        headers={
            "ApiKey": ALF_API_TOKEN,
            "Content-Type": "application/json",
        },
        data=request.data,
    )

    return requests_response.content, 200, {"Content-Type": "text/json"}


@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    company = data.get('company')
    email = data.get('email')
    phone = data.get('phone')

    # Perform basic validation
    if not firstname or not lastname or not company or not email or not phone:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        message = firstname + lastname + company + email + phone

        # Create the email message
        email = EmailMessage()
        email['Subject'] = "Anfrage Vermittler Zertifikat"
        email['From'] = 'web@hgbeyer.com'
        email['To'] = 'test@hgbeyer.com'
        email.set_content(message)

        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.example.com', 587) as smtp:
            smtp.starttls()
            smtp.login('your-username', 'your-password')
            smtp.send_message(email)

        return jsonify({'message': 'Email sent successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run()
