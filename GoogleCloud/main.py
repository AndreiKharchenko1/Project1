import os
from flask import Flask, request, render_template, redirect, url_for
from google_auth_oauthlib.flow import InstalledAppFlow  # This should be the only import you need for OAuth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.auth.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from werkzeug.utils import secure_filename

def authenticate_google_drive():
    creds = None
    # Check if token.json exists and load the credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If credentials are invalid or expired, prompt for re-authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh expired credentials
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES
            )
            creds = flow.run_local_server(port=0)  # Use run_local_server instead of run_console()

        # Save credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


# Initialize Flask app
app = Flask(__name__)

# Set your Google Drive folder ID here (the one you provided)
FOLDER_ID = '126ySc-UJ6qoc4NzXVB4b5M_cawlU4h0c'

# The file to store the credentials (token.json)
CREDENTIALS_FILE = 'token.json'
CLIENT_SECRET_FILE = 'client_secret.json'  # Make sure this file exists
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# This is the upload folder on the server
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Google Drive authentication
def authenticate_google_drive():
    creds = None
    # Check if token.json exists and load the credentials
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)

    # If credentials are invalid or expired, prompt for re-authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh expired credentials
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)  # Replace run_console() with run_local_server()

        # Save credentials for future use
        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


# Upload a file to Google Drive
def upload_to_drive(file_path, filename):
    try:
        service = authenticate_google_drive()

        file_metadata = {
            'name': filename,
            'parents': [FOLDER_ID]
        }
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        print('File ID: %s' % file['id'])
        return file['id']

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Now upload to Google Drive
            upload_to_drive(file_path, filename)

            return redirect(url_for('index'))

    # List all files in the Google Drive folder
    service = authenticate_google_drive()
    results = service.files().list(q=f"'{FOLDER_ID}' in parents", fields="files(id, name)").execute()
    files = results.get('files', [])

    return render_template("index.html", files=files)


# Define the redirect route for OAuth callback
@app.route("/callback")
def oauth2_callback():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, SCOPES, redirect_uri="http://localhost:8080/callback"
    )

    # Use the authorization response to fetch the tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Save the credentials to token.json for future use
    creds = flow.credentials
    with open(CREDENTIALS_FILE, 'w') as token:
        token.write(creds.to_json())

    # Redirect back to the home page or where necessary
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
