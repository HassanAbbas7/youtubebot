import uuid
from pathlib import Path
from config import OUTPUT_ROOT
import os
import shutil


def new_job_id():
    return uuid.uuid4().hex[:12]



def ensure_output_folder(*parts):
    p = Path(OUTPUT_ROOT).joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def clear_output():
    for filename in os.listdir("./temp"):
        file_path = os.path.join("./temp", filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))