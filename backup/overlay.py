import ffmpeg
import os
import shutil

def overlay(input_video, overlay):
    main = ffmpeg.input(input_video)

    overlay_vid = ffmpeg.input(
        overlay,
        stream_loop=-1
    )

    out = ffmpeg.filter(
        [main.video, overlay_vid],
        "overlay",
        x='(W-w)/2',
        y='(H-h)/2',
        eof_action='pass',
        shortest=1
    )

    base, ext = os.path.splitext(input_video)
    tmp_output = f"{base}_tmp{ext}"

    (
        ffmpeg
        .output(
            out,
            main.audio,
            tmp_output,
            vcodec='libx264',
            preset='veryfast',
            acodec='copy',
            movflags='+faststart',
            pix_fmt='yuv420p'
        )
        .run(overwrite_output=True)
    )


    os.remove(input_video) 
    shutil.move(tmp_output, input_video) 






# import subprocess
# import json
# import math

# # ---------- CONFIG ----------
# OVERLAY = "overlay/Main.mov"
# OUT = "overlay/prebaked_overlay.mov"

# START = 10            # first overlay start time (seconds)
# INTERVAL = 1800       # 30 minutes
# TOTAL_DUR = (3600*2) + 100 # total duration to bake (2 hours)
# WIDTH = 1920
# HEIGHT = 1080
# # ----------------------------

# def get_duration(path):
#     """Get video duration in seconds."""
#     out = subprocess.check_output([
#         "ffprobe", "-v", "quiet",
#         "-print_format", "json",
#         "-show_format", path
#     ])
#     return float(json.loads(out)["format"]["duration"])

# overlay_dur = get_duration(OVERLAY)
# instances = math.ceil((TOTAL_DUR - START) / INTERVAL)

# # --------- BUILD INPUTS ----------
# # First input is the transparent base
# inputs = ["-f", "lavfi", "-i", f"color=c=black@0.0:s={WIDTH}x{HEIGHT}:d={TOTAL_DUR},format=rgba"]

# # Add one input per overlay instance
# for _ in range(instances):
#     inputs += ["-i", OVERLAY]

# # --------- BUILD FILTERS ----------
# filters = []
# filters.append("[0:v]format=rgba[b0]")  # base label

# for i in range(instances):
#     t = START + i * INTERVAL
#     filters.append(f"[{i+1}:v]trim=0:{overlay_dur},setpts=PTS-STARTPTS+{t}/TB,format=rgba[v{i}]")
#     filters.append(f"[b{i}][v{i}]overlay=(W-w)/2:(H-h)/2:eof_action=pass[b{i+1}]")

# # --------- BUILD COMMAND ----------
# cmd = [
#     "ffmpeg", "-y",
#     *inputs,
#     "-filter_complex", ";".join(filters),
#     "-map", f"[b{instances}]",
#     "-c:v", "qtrle",
#     "-pix_fmt", "argb",  # 🔑 Force alpha channel
#     OUT
# ]

# # --------- RUN ----------
# subprocess.run(cmd, check=True)
# print(f"✅ Prebake complete: {OUT}")
