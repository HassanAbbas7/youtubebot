TELEGRAM_TOKEN = "8245124322:AAEaJ2xPBUVS3mVgtP38_kvg6gUQNo9AHys"
GOOGLE_SHEET_KEY = "1lUgi5Ie1En2qLhnsSd6GSn4j_CGjAfnGxRkHxRSkq5M"
GOOGLE_CREDS_JSON = "./creds.json"
AI_PROMPT_ENDPOINT = "https://api.kie.ai/apis/v1/jobs/createTask"
AI_IMAGE_ENDPOINT = "https://api.kie.ai/api/v1/jobs/createTask"
VIDEO_GEN_SCRIPT = "generator_worker.py" # script to run as subprocess
VIDEO_PROCESS_SCRIPT = "process_video.py" # script to run as subprocess
VIDEO_COMPRESSION_MODE = "strong"  # other options: fast, insane
OUTPUT_ROOT = "./outputs"
# Optional headers for AI endpoints
AI_API_KEY = "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"
KIE_API_KEY = "c71e2ce0a9ddc33eb8468f83f3667dd0"
# How many rows to fetch per run, or set to None to fetch all
SHEETS_FETCH_LIMIT = 1000
SET_TAIL_IMAGE = True

TESTING = False