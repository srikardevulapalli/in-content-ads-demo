import os
import ffmpeg
import tempfile
import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline
from ffmpeg import Error

# Where blended videos go
BLENDED_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'blended')

# Load SD Img2Img pipeline once
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if device=="cuda" else torch.float32,
).to(device)
pipe.safety_checker = None

def blend_uploaded(src_path: str, vid_id: str, ad: dict, slot: dict, region: dict) -> str:
    """
    Uses SD Img2Img to harmonize the ad PNG into the scene over the ad window.
    Extracts frames, pastes ad, runs Img2Img, then reassembles the clip.
    """
    start    = slot.get("start", 0)
    duration = slot.get("duration", 5)
    end_time = start + duration

    overlay_png = os.path.join(os.path.dirname(__file__),
                               "..", "assets", "ads", ad["file"])
    if not os.path.isfile(overlay_png):
        raise FileNotFoundError(f"Ad PNG not found: {overlay_png}")

    # Probe source video for fps, width, height
    meta = ffmpeg.probe(src_path)
    vs   = next(s for s in meta["streams"] if s["codec_type"]=="video")
    fps  = eval(vs["r_frame_rate"])
    vw, vh = int(vs["width"]), int(vs["height"])

    # Temporary workspace
    tmpdir     = tempfile.mkdtemp(prefix="sd_blend_")
    frames_dir = os.path.join(tmpdir, "frames")
    sd_dir     = os.path.join(tmpdir, "sd")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(sd_dir,     exist_ok=True)

    # 1) Extract frames in the ad window
    (
        ffmpeg
          .input(src_path, ss=start, t=duration)
          .output(os.path.join(frames_dir, "frame_%04d.png"),
                  format="image2", r=fps)
          .overwrite_output().run(quiet=True)
    )

    # 2) Process each frame with SD Img2Img
    frame_files = sorted(os.listdir(frames_dir))
    for fname in frame_files:
        frame_path = os.path.join(frames_dir, fname)
        frame = Image.open(frame_path).convert("RGB")

        # Paste ad PNG into region
        ad_img = Image.open(overlay_png).convert("RGBA")
        w, h   = region["w"], region["h"]
        # Use LANCZOS for high-quality resize
        ad_img = ad_img.resize((w, h), resample=Image.LANCZOS)
        tmp = frame.copy()
        tmp.paste(ad_img, (region["x"], region["y"]), ad_img)

        # Create mask for Img2Img (only ad region)
        mask = Image.new("L", frame.size, 0)
        mask_region = Image.new("L", (w, h), 255)
        mask.paste(mask_region, (region["x"], region["y"]))

        result = pipe(
            prompt="",  # empty: harmonize only
            image=tmp,
            mask_image=mask,
            strength=0.7,
            num_inference_steps=25
        ).images[0]

        result.save(os.path.join(sd_dir, fname))

    # 3) Reassemble SD frames into a video clip
    sd_clip = os.path.join(tmpdir, "ad_sd.mp4")
    (
        ffmpeg
          .input(os.path.join(sd_dir, "frame_%04d.png"), format="image2", r=fps)
          .output(sd_clip, vcodec="libx264", pix_fmt="yuv420p", r=fps)
          .overwrite_output().run(quiet=True)
    )

    # 4) Overlay the SD clip back into the original video
    out_name = f"{vid_id}_{ad['id']}.mp4"
    out_path = os.path.join(BLENDED_DIR, out_name)
    try:
        (
            ffmpeg
              .input(src_path)
              .overlay(
                  ffmpeg.input(sd_clip),
                  x=0, y=0,
                  enable=f"between(t,{start},{end_time})"
              )
              .output(out_path, codec="libx264", crf=23, preset="veryfast")
              .overwrite_output().run()
        )
    except Error as e:
        stderr = e.stderr.decode("utf-8", "ignore") if e.stderr else str(e)
        raise RuntimeError(f"Overlay error:\n{stderr}") from e
    finally:
        # Clean up temp files
        for d in (frames_dir, sd_dir):
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))
            os.rmdir(d)
        os.rmdir(tmpdir)

    return out_name