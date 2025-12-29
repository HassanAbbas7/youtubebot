import asyncio
import os
import subprocess
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)
from config import TESTING, TELEGRAM_TOKEN, VIDEO_GEN_SCRIPT, VIDEO_PROCESS_SCRIPT
from traceback import print_exc
from sheets import fetch_rows, mark_row_done
from ai_client import generate_prompt, generate_image, get_prompt_for_video
from utils import new_job_id, clear_output
from status_store import set_status, get_status, list_statuses

# ----------------- CONFIG -----------------
OUTPUT_ROOT = Path("outputs")
AUTO = True  # Set True to skip all approvals
# -----------------------------------------

ROWS_CACHE = []
CURRENT_INDEX = 0
JOB_ROW_MAP = {}
ROW_LOCK = asyncio.Lock()
PROCESSING_ACTIVE = True

# -----------------------------------------------------------
# Convert duration to seconds
# -----------------------------------------------------------
def getSeconds(duration_str):
    parts = duration_str.split(":")
    if not parts:
        return duration_str

    if len(parts) == 2:
        mins, secs = map(int, parts)
    elif len(parts) == 3:
        hrs, mins, secs = map(int, parts)
        mins = hrs * 60 + mins
    elif len(parts) == 1:
        mins = 0
        secs = int(parts[0])

    total_seconds = mins * 60 + secs
    return total_seconds

# -----------------------------------------------------------
# PROCESS NEXT ROW
# -----------------------------------------------------------
async def process_next_row(chat_id, context):
    global CURRENT_INDEX, ROWS_CACHE, PROCESSING_ACTIVE

    if not PROCESSING_ACTIVE:
        await context.bot.send_message(chat_id, "Processing stopped. Use /start to restart from the beginning.")
        return

    while CURRENT_INDEX < len(ROWS_CACHE):
        row = ROWS_CACHE[CURRENT_INDEX]
        if row.get("Status", "").strip().lower() != "done":
            break
        CURRENT_INDEX += 1

    if CURRENT_INDEX >= len(ROWS_CACHE):
        await context.bot.send_message(chat_id, "All rows processed!")
        return

    row = ROWS_CACHE[CURRENT_INDEX]
    title = row.get("Title", "")
    prompt = row.get("Prompt", "")

    job_id = new_job_id()
    JOB_ROW_MAP[job_id] = CURRENT_INDEX

    try:
        if not prompt and not TESTING:
            raise ValueError("Prompt is empty!")

        image_url = generate_image(prompt)

    except Exception as e:
        await context.bot.send_message(chat_id, f"Image generation failed for '{title}': {e}")
        CURRENT_INDEX += 1
        await process_next_row(chat_id, context)
        return

    # Save status
    set_status(job_id, {
        "state": "awaiting_image_approval",
        "title": title,
        "prompt": prompt,
        "image": image_url
    })

    if AUTO:
        # Skip approval and auto-approve image
        class DummyQuery:
            def __init__(self, message):
                self.data = f"appr_image:{job_id}"
                self.message = message
            async def answer(self): pass

        class DummyMessage:
            chat = type("obj", (), {"id": chat_id})()
            async def reply_text(self, msg): pass

        dummy_update = type("obj", (), {"callback_query": DummyQuery(DummyMessage())})()
        await callback_handler(dummy_update, context)
    else:
        # Send image for approval
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Approve Image", callback_data=f"appr_image:{job_id}"),
                InlineKeyboardButton("Reject Image", callback_data=f"rej_image:{job_id}")
            ]
        ])
        await context.bot.send_photo(
            chat_id,
            photo=image_url,
            caption=f'Preview for "{title}"\n\nPrompt:\n{prompt[0:100]}...',
            reply_markup=keyboard
        )

# -----------------------------------------------------------
# /start
# -----------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ROWS_CACHE, CURRENT_INDEX, PROCESSING_ACTIVE
    chat_id = update.effective_chat.id

    await update.message.reply_text("Loading Google Sheets rows...")

    ROWS_CACHE = fetch_rows()
    PROCESSING_ACTIVE = True
    CURRENT_INDEX = 0

    await process_next_row(chat_id, context)

# -----------------------------------------------------------
# /stop
# -----------------------------------------------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PROCESSING_ACTIVE
    PROCESSING_ACTIVE = False
    await update.message.reply_text("Processing stopped.")

# -----------------------------------------------------------
# /status
# -----------------------------------------------------------
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    statuses = list_statuses()
    if not statuses:
        await update.message.reply_text("No jobs yet.")
        return

    lines = [f"{jid[:8]} - {info.get('state')} - {info.get('title', '')}" for jid, info in statuses.items()]
    await update.message.reply_text("\n".join(lines))

# -----------------------------------------------------------
# CALLBACK HANDLER
# -----------------------------------------------------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_INDEX
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat.id

    # ---------------- IMAGE APPROVED ----------------
    if data.startswith("appr_image:"):
        job_id = data.split(":")[1]
        info = get_status(job_id)

        await context.bot.send_message(chat_id, "Image Accepted")

        image = info.get("image")
        out_mp4 = "temp/looped.mp4"
        row = ROWS_CACHE[CURRENT_INDEX]
        is_static = row.get("Static", "no").strip().lower() == "yes"

        prompt = ""
        if not is_static:
            prompt = get_prompt_for_video(image)

        await query.message.reply_text(f"Starting video generation (static={is_static})")
        O = ["python", VIDEO_GEN_SCRIPT, "--image", image, "--out", out_mp4, "--job", job_id, "--prompt", prompt]
        print(O)
        if is_static:
            O.append("--static")

        async with ROW_LOCK:
            proc = subprocess.Popen(
                O,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )

            info["state"] = "video_generating"
            info["out"] = out_mp4
            info["proc_pid"] = proc.pid
            set_status(job_id, info)

            asyncio.create_task(_monitor_and_continue(proc, job_id, chat_id, context))

    # ---------------- IMAGE REJECTED ----------------
    elif data.startswith("rej_image:"):
        job_id = data.split(":")[1]
        info = get_status(job_id)

        title = info.get("title")
        prompt = info.get("prompt")

        await query.message.reply_text("Image rejected. Regenerating image...")

        try:
            new_image_url = generate_image(prompt)
        except Exception as e:
            await query.message.reply_text(f"Image regeneration failed: {e}")
            return

        info["image"] = new_image_url
        info["state"] = "awaiting_image_approval"
        set_status(job_id, info)

        if AUTO:
            # Auto-approve regenerated image
            class DummyQuery:
                def __init__(self, message):
                    self.data = f"appr_image:{job_id}"
                    self.message = message
                async def answer(self): pass

            class DummyMessage:
                chat = type("obj", (), {"id": chat_id})()
                async def reply_text(self, msg): pass

            dummy_update = type("obj", (), {"callback_query": DummyQuery(DummyMessage())})()
            await callback_handler(dummy_update, context)
        else:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Approve Image", callback_data=f"appr_image:{job_id}"),
                    InlineKeyboardButton("Reject Image", callback_data=f"rej_image:{job_id}")
                ]
            ])
            await context.bot.send_photo(
                chat_id,
                photo=new_image_url,
                caption=f'Regenerated image for "{title}"',
                reply_markup=keyboard
            )

    # ---------------- VIDEO APPROVED ----------------
    elif data.startswith("appr_video:"):
        job_id = data.split(":")[1]
        info = get_status(job_id)

        await query.message.reply_text("Video approved. Processing video...")

        row = ROWS_CACHE[CURRENT_INDEX]
        music_folder = row.get("Folder path", "./music")
        title = row.get("Title", "NO_TITLE")
        duration = row.get("Min Length", "2:10").strip()
        output_folder = row.get("Outuput Folder", "output")
        overlay_ = row.get("Overlay", "")
        channel_name = row.get("Channel", "")
        publish_at = row.get("Publish at", "")

        total_seconds = getSeconds(duration)

        O = ["python", VIDEO_PROCESS_SCRIPT, "temp/out.mp4", music_folder, str(total_seconds), title + ".mp4", output_folder, overlay_, channel_name, publish_at]
        print(O) 
        proc = subprocess.Popen(
            O,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )

        info["state"] = "video_processing"
        info["proc_pid"] = proc.pid
        set_status(job_id, info)

        asyncio.create_task(_monitor_processed_video(proc, job_id, chat_id, context))

    # ---------------- VIDEO REJECTED ----------------
    elif data.startswith("rej_video:"):
        job_id = data.split(":")[1]
        info = get_status(job_id)

        title = info.get("title")
        prompt = info.get("prompt")

        await query.message.reply_text("Video rejected. Regenerating image...")

        try:
            image_url = generate_image(prompt)
        except Exception as e:
            await query.message.reply_text(f"Image regeneration failed: {e}")
            return

        info["image"] = image_url
        info["state"] = "awaiting_image_approval"
        set_status(job_id, info)

        if AUTO:
            # Auto-approve regenerated image
            class DummyQuery:
                def __init__(self, message):
                    self.data = f"appr_image:{job_id}"
                    self.message = message
                async def answer(self): pass

            class DummyMessage:
                chat = type("obj", (), {"id": chat_id})()
                async def reply_text(self, msg): pass

            dummy_update = type("obj", (), {"callback_query": DummyQuery(DummyMessage())})()
            await callback_handler(dummy_update, context)
        else:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Approve Image", callback_data=f"appr_image:{job_id}"),
                    InlineKeyboardButton("Reject Image", callback_data=f"rej_image:{job_id}")
                ]
            ])
            await context.bot.send_photo(
                chat_id,
                photo=image_url,
                caption=f'Regenerated image for "{title}"',
                reply_markup=keyboard
            )

# -----------------------------------------------------------
# Monitor video generation
# -----------------------------------------------------------
async def _monitor_and_continue(proc, job_id, chat_id, context):
    while True:
        if proc.poll() is not None:
            _, _ = proc.communicate()
            out_path = "temp/looped.mp4"

            if out_path and Path(out_path).exists():
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Approve Video", callback_data=f"appr_video:{job_id}"),
                        InlineKeyboardButton("Reject Video", callback_data=f"rej_video:{job_id}")
                    ]
                ])
                if AUTO:
                    # Auto-approve video
                    class DummyQuery:
                        def __init__(self, message):
                            self.data = f"appr_video:{job_id}"
                            self.message = message
                        async def answer(self): pass
                    class DummyMessage:
                        chat = type("obj", (), {"id": chat_id})()
                        async def reply_text(self, msg): pass
                    dummy_update = type("obj", (), {"callback_query": DummyQuery(DummyMessage())})()
                    await callback_handler(dummy_update, context)
                else:
                    await context.bot.send_message(
                        chat_id,
                        "Do you approve this video?",
                        reply_markup=keyboard
                    )

                old = get_status(job_id)
                old["state"] = "awaiting_video_approval"
                old["out"] = out_path
                set_status(job_id, old)
            else:
                await context.bot.send_message(chat_id, f"Video finished but output missing for job {job_id}")

            break

        await asyncio.sleep(1)

# -----------------------------------------------------------
# Monitor processed video
# -----------------------------------------------------------
async def _monitor_processed_video(proc, job_id, chat_id, context):
    global CURRENT_INDEX
    while True:
        if proc.poll() is not None:
            _, _ = proc.communicate()

            info = get_status(job_id)
            row = ROWS_CACHE[CURRENT_INDEX]
            output_folder = row.get("Outuput Folder", "output")
            processed_path = f"{output_folder}/{row.get('Title','NO_TITLE')}.mp4"

            if processed_path and Path(processed_path).exists():
                await context.bot.send_message(chat_id, f"Video \"{row.get('Title', 'NO_TITLE')}\" completed. Moving to next row.")
                clear_output()

                row_idx = JOB_ROW_MAP.get(job_id)
                if row_idx is not None:
                    try:
                        mark_row_done(row_idx)
                    except Exception as e:
                        print("Couldnt mark row as done")
                        print(e)
                        pass

                CURRENT_INDEX += 1
                await process_next_row(chat_id, context)
            else:
                await context.bot.send_message(chat_id, "Processing finished but output missing")

            break

        await asyncio.sleep(1)

# -----------------------------------------------------------
# MAIN
# -----------------------------------------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
