from django.shortcuts import render

# Create your views here.
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from django.shortcuts import redirect, render
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.core.files.storage import default_storage
from googleapiclient.http import MediaFileUpload


# OAuth2 Flow to Get User Consent
def google_drive_auth(request):
    flow = Flow.from_client_secrets_file(
        os.path.join(os.getcwd(), 'credentials.json'),
        scopes=['https://www.googleapis.com/auth/drive.file'],
        redirect_uri='http://localhost:8000/auth/callback'
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

# Handle OAuth2 Callback
def google_drive_callback(request):
    flow = Flow.from_client_secrets_file(
        os.path.join(os.getcwd(), 'credentials.json'),
        scopes=['https://www.googleapis.com/auth/drive.file'],
        redirect_uri='http://localhost:8000/auth/callback'
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    return redirect('/upload/')

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def upload_to_drive(request):
    if 'credentials' not in request.session:
        return redirect('/auth/')

    creds = Credentials(**request.session['credentials'])
    drive_service = build('drive', 'v3', credentials=creds)

    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        file_path = default_storage.save(file.name, file)

        file_metadata = {'name': file.name}
        media = MediaFileUpload(file_path, resumable=True)

        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return render(request, 'upload_success.html', {'file_id': file.get('id')})

    return render(request, 'upload.html')

def list_drive_files(request):
    if 'credentials' not in request.session:
        return redirect('/auth/')

    creds = Credentials(**request.session['credentials'])
    drive_service = build('drive', 'v3', credentials=creds)

    results = drive_service.files().list(pageSize=10, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    return render(request, 'list_files.html', {'files': files})

def download_drive_file(request, file_id):
    if 'credentials' not in request.session:
        return redirect('/auth/')

    creds = Credentials(**request.session['credentials'])
    drive_service = build('drive', 'v3', credentials=creds)

    request_file = drive_service.files().get_media(fileId=file_id)
    file_path = os.path.join(os.getcwd(), f"{file_id}.jpg")

    with open(file_path, 'wb') as f:
        f.write(request_file.execute())
    
    return redirect(file_path)
