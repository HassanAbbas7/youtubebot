import argparse
import time
from pathlib import Path
import requests
from config import TESTING
import subprocess
from utils import clear_output
import os
import shutil
from ai_client import getVideo


parser = argparse.ArgumentParser()
parser.add_argument('--image', required=False)
parser.add_argument('--out', required=False)
parser.add_argument('--job', required=False)
parser.add_argument('--prompt', required=False)
parser.add_argument('--static', action='store_true')
args = parser.parse_args()


print(f"Starting video generation for job {args.job} from {args.image}")

clear_output()

out_path = Path(args.out)
out_path.parent.mkdir(parents=True, exist_ok=True)

if TESTING and not args.static:
    if not os.path.exists('./out.mp4'):
        video = "https://www.pexels.com/download/video/3195394/"
        response = requests.get(video)
        with open("./temp/out.mp4", 'wb') as f:
            f.write(response.content)

    shutil.copy('out.mp4', './temp/out.mp4')
    shutil.copy('./temp/out.mp4', './temp/looped.mp4')

else:
    # ---------------- STATIC IMAGE PATH ----------------
    if args.static:
        response = requests.get(args.image)
        with open("./temp/image.png", 'wb') as f:
            f.write(response.content)
            
        cmd = [
            "ffmpeg",
            "-loop", "1",
            "-i", "./temp/image.png",
            "-t", "5",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-y",
            out_path
        ]

        subprocess.run(cmd)

        # copy the looped.mp4 to out.mp4
        shutil.copy(out_path, './temp/out.mp4')


    else:
        video = getVideo(
            prompt=args.prompt,
            image_url=args.image
        )

        response = requests.get(video)
        with open("./temp/out.mp4", 'wb') as f:
            f.write(response.content)

        cmd = [
            "ffmpeg",
            "-stream_loop", str(3 - 1),
            "-i", "./temp/out.mp4",
            "-c", "copy",
            "-y",
            out_path
        ]
        subprocess.run(cmd)

    print(f"done {args.job} {out_path}")
