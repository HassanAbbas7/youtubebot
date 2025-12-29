import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timezone



# =========================
# CONFIG
# =========================
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "youtube.json"
TOKENS_DIR = "tokens"

def date_to_iso8601(date_str, hour=0, minute=0, second=0):
    # Detect whether time is included
    if " " in date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    else:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt = dt.replace(hour=hour, minute=minute, second=second)

    dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")
# =========================
# AUTHENTICATION
# =========================
def authenticate_youtube(channel_name: str):
    """
    Authenticates ONE YouTube channel and caches its token.
    Each channel_name maps to a separate token file.
    """
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    os.makedirs(TOKENS_DIR, exist_ok=True)

    token_path = os.path.join(TOKENS_DIR, f"{channel_name}.json")
    credentials = None

    # Load existing token
    if os.path.exists(token_path):
        credentials = Credentials.from_authorized_user_file(
            token_path, SCOPES
        )

    # Refresh or do OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                SCOPES
            )
            credentials = flow.run_local_server(
                port=8080,
                prompt="consent",
                access_type="offline"
            )

        # Save token
        with open(token_path, "w") as f:
            f.write(credentials.to_json())

    return googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials
    )


# =========================
# UPLOAD VIDEO
# =========================
def upload_video(
    channel_name: str,
    video_path: str = "",
    title: str = "",
    publish_at: str = "",
    category_id: str = "22",
    privacy_status: str = "private",
):
    """
    Uploads a video to the specified channel.
    """


    youtube = authenticate_youtube(channel_name)

    if not video_path:
        print(f"Successfully Registered '{channel_name}'")
        return

    request_body = {
        "snippet": {
            "title": title,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            # "publishAt": date_to_iso8601(publish_at)
        }
    }
    if publish_at:
        request_body["status"]["publishAt"] = date_to_iso8601(publish_at)

    print(request_body)

    media = googleapiclient.http.MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[{channel_name}] Upload {int(status.progress() * 100)}%")

    print(f"[{channel_name}] Uploaded video ID: {response['id']}")
    return response["id"]



if __name__ == "__main__":

    # channels = ["Sanctum Quest", "TimeWarp Lofi", "Stranger Boy Lofi", "Tokyo 90s Lofi"] # Add upto 100 channels (youtube API free tier limit)

    # for channel in channels:
        upload_video(
            channel_name="Sanctum Quest",
            video_path="/root/Documents/Output/Sanctum Quest/Yule Rest for the Weary Knight 🎄 Medieval Firelight.mp4",
            title="Yule Rest for the Weary Knight 🎄 Medieval Firelight.mp4",
            publish_at="2025-12-23 16:30"
        )