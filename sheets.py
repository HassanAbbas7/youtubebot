import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict
from config import GOOGLE_CREDS_JSON, GOOGLE_SHEET_KEY, SHEETS_FETCH_LIMIT


SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]




def open_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_KEY).sheet1
    return sheet




def fetch_rows() -> List[Dict]:
    sheet = open_sheet()
    all_values = sheet.get_all_records()
    if SHEETS_FETCH_LIMIT:
        all_values = all_values[:SHEETS_FETCH_LIMIT]
        # Expect columns: Title, Prompt, Min Lenght, Folder path, Outuput Folder, Status, Channel
        return all_values



def mark_row_done(row_index: int):
    sheet = open_sheet()

    headers = sheet.row_values(1)
    try:
        status_col = headers.index('Status') + 1
    except ValueError:
        status_col = 6

    # ALWAYS update after determining the correct column
    sheet.update_cell(row_index + 2, status_col, 'done')
