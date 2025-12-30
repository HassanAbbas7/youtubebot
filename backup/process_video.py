import sys
import os
import random
import subprocess
import json
import math
import tempfile
import re
from config import VIDEO_COMPRESSION_MODE
import overlay
from upload_youtube import upload_video



def ffprobe_duration(path):
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", path
    ]
    out = subprocess.check_output(cmd).decode()
    return float(json.loads(out)["format"]["duration"])

def run(cmd_list):
    subprocess.run(cmd_list, check=True)

def sanitize_filename(filename):
    name, ext = os.path.splitext(filename)
    name = re.sub(r"[^\w\s-]", "", name)
    name = name.replace(" ", "_")
    return f"{name}{ext}"

def compress_video(input_path, output_path, mode="fast"):
    """
    Compress input video into output_path using different compression modes.
    """
    if mode == "fast":
        # Fast compression, decent size
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]
    elif mode == "strong":
        # Strong compression
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", "libx265",
            "-preset", "medium",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "96k",
            output_path
        ]
    elif mode == "insane":
        # Extreme compression, lower resolution
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", "libx265",
            "-preset", "slow",
            "-crf", "32",
            "-vf", "scale=-2:540",
            "-c:a", "aac",
            "-b:a", "64k",
            output_path
        ]
    else:
        raise ValueError("Unknown compression mode: choose fast, strong, or insane")
    print(f"Compressing video ({mode})...")
    run(cmd)
    print("Compression finished.")

def main():
    if len(sys.argv) < 9 or len(sys.argv) > 9:
        print("Usage: python script.py input_video.mp4 music_folder duration_seconds output_name output_folder [compression_mode]")
        print("compression_mode options: fast, strong, insane (default: fast)")
        sys.exit(1)

    input_video = os.path.abspath(sys.argv[1])
    music_folder = os.path.abspath(sys.argv[2])
    target_duration = int(sys.argv[3])
    output_name = sys.argv[4]
    output_folder = os.path.abspath(sys.argv[5])
    overlay_ = os.path.abspath(sys.argv[6])
    channel_name = sys.argv[7]
    publish_at = sys.argv[8]
    compression_mode = VIDEO_COMPRESSION_MODE

    with tempfile.TemporaryDirectory() as tmp:

        # ----------------------------------------------------------------------
        # STEP 0: Compress input video first
        # ----------------------------------------------------------------------
        compressed_video = os.path.join(tmp, "compressed_input.mp4")
        compress_video(input_video, compressed_video, compression_mode)

        # Use compressed video for all next steps
        input_video = compressed_video

        # ----------------------------------------------------------------------
        # STEP 1: Rename music files safely
        # ----------------------------------------------------------------------
        renamed_files = []
        for f in os.listdir(music_folder):
            if f.lower().endswith((".mp3", ".wav", ".aac", ".m4a")):
                old_path = os.path.join(music_folder, f)
                new_name = sanitize_filename(f)
                new_path = os.path.join(music_folder, new_name)
                if old_path != new_path:
                    os.rename(old_path, new_path)
                renamed_files.append(new_path)

        if not renamed_files:
            print("No audio files found.")
            sys.exit(1)

        # ----------------------------------------------------------------------
        # STEP 2: Pick songs until duration is enough
        # ----------------------------------------------------------------------
        random.shuffle(renamed_files)
        selected_songs = []
        total_audio_duration = 0.0
        while total_audio_duration < target_duration:
            song = random.choice(renamed_files)
            d = ffprobe_duration(song)
            selected_songs.append(song)
            total_audio_duration += d

        # ----------------------------------------------------------------------
        # TEMP FILES
        # ----------------------------------------------------------------------
        video_list = os.path.join(tmp, "video_list.txt")
        audio_list = os.path.join(tmp, "audio_list.txt")
        looped_video = os.path.join(tmp, "video.mp4")
        merged_audio = os.path.join(tmp, "audio.wav")

        # ----------------------------------------------------------------------
        # STEP 3: Loop compressed video
        # ----------------------------------------------------------------------
        video_duration = ffprobe_duration(input_video)
        loops = math.ceil(target_duration / video_duration)

        with open(video_list, "w", encoding="utf-8") as f:
            for _ in range(loops):
                escaped = input_video.replace("\\", "\\\\").replace("'", "\\'")
                f.write(f"file '{escaped}'\n")

        run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", video_list,
            "-t", str(target_duration),
            "-c:v", "copy",
            looped_video
        ])

        # ----------------------------------------------------------------------
        # STEP 4: Build and merge audio
        # ----------------------------------------------------------------------
        with open(audio_list, "w", encoding="utf-8") as f:
            for p in selected_songs:
                escaped = p.replace("\\", "\\\\").replace("'", "\\'")
                f.write(f"file '{escaped}'\n")

        run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", audio_list,
            "-t", str(target_duration),
            "-acodec", "pcm_s16le",
            merged_audio
        ])

        # ----------------------------------------------------------------------
        # STEP 5: Final merge
        # ----------------------------------------------------------------------
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, output_name)

        run([
            "ffmpeg", "-y",
            "-i", looped_video,
            "-i", merged_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ])

        if overlay_:
            overlay.overlay(output_path, overlay_)

        if publish_at:
            upload_video(
                channel_name,
                output_path,
                output_name,
                publish_at
            )
        

        print(f"Generated {output_path}")
        print("All music files have been sanitized and renamed.")

if __name__ == "__main__":
    main()
