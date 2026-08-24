"""
AETHER - autonomous publish run
Picks a topic itself, runs the full free pipeline, uploads publicly to
YouTube with CC attribution in the description, and logs the result to
jobs.json so it shows up in the dashboard too. Meant to be run headless by
GitHub Actions, per channel.

Usage: python auto_publish.py <channel>   e.g. python auto_publish.py mystery
"""
import asyncio
import logging
import sys

import jobs
from fetch_footage import fetch_footage_for_scenes
from generate_voice import generate_voice_for_scenes
from assemble_video import assemble, DEFAULT_STYLE
from attribution import build_attribution_block
from upload_youtube import upload_video, set_thumbnail
from thumbnail import generate_thumbnail
from channels import get_channel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("auto_publish.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("auto_publish")


def main(channel_name: str) -> None:
    channel = get_channel(channel_name)
    voice = getattr(channel, "VOICE", "en-US-EricNeural")
    style = getattr(channel, "STYLE", DEFAULT_STYLE)
    made_for_kids = getattr(channel, "MADE_FOR_KIDS", False)
    category_id = getattr(channel, "CATEGORY_ID", "27")

    topic = channel.pick_topic()
    log.info(f"[{channel_name}] Selected topic: {topic}")
    job_id = jobs.create_job(topic, upload=True)

    try:
        jobs.update_job(job_id, step="planning topic")
        jobs.update_job(job_id, step="researching facts")
        jobs.update_job(job_id, step="writing script")
        scenes = channel.generate_script(topic)
        if not scenes:
            log.warning("Empty script on first attempt, retrying once")
            scenes = channel.generate_script(topic)
        if not scenes:
            raise RuntimeError("Script generation returned no scenes - is Ollama running?")
        # script_engine already retries internally for a thin script, but
        # this is the last line of defense - one video actually published
        # at 6 seconds long because nothing checked total content length
        total_words = sum(len(s["narration"].split()) for s in scenes)
        if total_words < 25:
            raise RuntimeError(f"Script too thin ({total_words} words across {len(scenes)} scenes) - refusing to publish")
        log.info(f"Script: {len(scenes)} scenes, {total_words} words")

        jobs.update_job(job_id, step="fetching footage")
        footage_source = getattr(channel, "FOOTAGE_SOURCE", "openverse")
        scenes = fetch_footage_for_scenes(scenes, source=footage_source)

        jobs.update_job(job_id, step="generating voiceover")
        scenes = asyncio.run(generate_voice_for_scenes(scenes, voice=voice))

        jobs.update_job(job_id, step="quality checking")
        for index, scene in enumerate(scenes, start=1):
            if not scene.get("narration") or not scene.get("voice_path"):
                raise RuntimeError(f"Quality check failed for scene {index}")

        jobs.update_job(job_id, step="assembling video")
        video_path = assemble({"topic": topic, "scenes": scenes}, style=style)
        jobs.update_job(job_id, video_path=video_path)
        log.info(f"Assembled: {video_path}")

        jobs.update_job(job_id, step="preparing metadata")
        credits = build_attribution_block(scenes)
        title, description, tags = channel.build_youtube_metadata(topic, credits)
        jobs.update_job(job_id, step="uploading to YouTube")
        video_id = upload_video(
            video_path, title, description, tags, privacy="public",
            client_secret_file=channel.CLIENT_SECRET_FILE,
            token_file=channel.TOKEN_FILE,
            category_id=category_id,
            made_for_kids=made_for_kids,
        )
        jobs.update_job(job_id, youtube_url=f"https://youtu.be/{video_id}")
        log.info(f"Uploaded: https://youtu.be/{video_id}")

        jobs.update_job(job_id, step="setting thumbnail")
        thumb_path = generate_thumbnail(topic, scenes)
        if thumb_path:
            set_thumbnail(video_id, thumb_path, client_secret_file=channel.CLIENT_SECRET_FILE, token_file=channel.TOKEN_FILE)
            log.info(f"Thumbnail set: {thumb_path}")

        jobs.update_job(job_id, status="done", step="done")
    except Exception as e:
        log.exception("auto_publish run failed")
        jobs.update_job(job_id, status="error", error=str(e))
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python auto_publish.py <channel>  (mystery | philosophy | kids)")
    try:
        main(sys.argv[1])
    except Exception:
        sys.exit(1)
