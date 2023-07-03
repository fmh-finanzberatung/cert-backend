from email.message import EmailMessage
import os
import requests
from flask import Flask, request, jsonify, json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin
from flask_caching import Cache
import smtplib
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

ALF_API_URL = "https://services1.fmh.de/webapi/banken-portal/graphql"
ALF_API_TOKEN = "JlrIZRj87Ozg30leAlPxBHIaqtTphjyc"
BE_API_URL = "https://cms.fmh.de/api/graphql"

app = Flask(__name__)
CORS(app)
cache = Cache()
cache.init_app(app)


# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["100 per minute"],
#     storage_uri="memory://",
#     strategy="fixed-window",  # or "moving-window"
# )

def make_graphql_request(url, query, variables=None, headers=None):
    """
    Makes a GraphQL request to the specified URL with the given query and optional variables and headers.
    Returns the JSON response.
    """
    payload = {
        'query': query,
        'variables': variables or {}
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # Raise an exception if the request was unsuccessful

    return response


@app.route('/token', methods=['GET'])
@cross_origin()
def get_token():
    query = '''mutation ($email: String!, $password: String!) {
           authenticateUserWithPassword(
             email: $email,
             password: $password
           ) {
             ... on UserAuthenticationWithPasswordSuccess {
               sessionToken
             }
             ... on UserAuthenticationWithPasswordFailure {
               message
             }
           }
         }
    '''

    variables = {
        "email": "info@hgbeyer.com",
        "password": "Mk9]6Fb0L2#e"
    }

    response = make_graphql_request(BE_API_URL, query, variables)
    return response.json(), response.status_code, {"Content-Type": "text/json"}


@app.route('/certificates', methods=['POST'])
# @cache.cached(timeout=3000)
@cross_origin()
def get_certificates():
    data = request.data
    requests_response = requests.post(
        url=ALF_API_URL,
        headers={
            "ApiKey": ALF_API_TOKEN,
            "Content-Type": "application/graphql",
        },
        data=request.data,
    )

    return requests_response.content, requests_response.status_code, {"Content-Type": "text/json"}


@app.route('/template', methods=['GET'])
@cache.cached(timeout=3000)
@cross_origin()
def get_template():
    requests_response = requests.get(url='https://www.fmh.de/api/templates/certificate/3555')

    return requests_response.content


@app.route('/send-email', methods=['POST'])
@cross_origin()
def send_email():
    data = request.get_json()
    firstname = data.get('vorname')
    lastname = data.get('nachname')
    company = data.get('unternehmen')
    email = data.get('email')
    phone = data.get('phone')

    # Perform basic validation
    if not firstname or not lastname or not company or not email:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        message = "Vorname: {}\nNachname: {}\nUnternehmen: {}\nEmail: {}\nTelefon: {}\n".format(firstname, lastname,
                                                                                                company, email, phone)

        # Create the email message
        email = EmailMessage()
        email['Subject'] = "Anfrage Vermittler Zertifikat"
        email['From'] = os.environ.get("SMTP_FROM", 'web@hgbeyer.com')
        email['To'] = os.environ.get("SMTP_TO", 'test@hgbeyer.com')
        email.set_content(message)

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(os.environ.get("SMTP_HOST"), os.environ.get("SMTP_PORT")) as smtp:
            smtp.starttls()
            smtp.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
            smtp.send_message(email)

        return jsonify({'message': 'Email sent successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e), 'info': os.environ.get("SMTP_HOST")}), 500


if __name__ == '__main__':
    app.run()
