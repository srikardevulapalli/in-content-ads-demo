import ffmpeg
import os

BLENDED_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'blended')

def blend_uploaded(src: str, vid_id: str, ad: dict, slot: dict, region: dict) -> str:
    start, duration = slot.get('start',0), slot.get('duration',5)
    overlay = os.path.join(os.path.dirname(__file__), '..', 'assets', 'ads', ad['file'])
    out_fn  = f"{vid_id}_{ad['id']}.mp4"
    out_p   = os.path.join(BLENDED_DIR, out_fn)
    x, y    = region.get('x',0), region.get('y',0)

    vid  = ffmpeg.input(src)
    logo = ffmpeg.input(overlay)
    (
        ffmpeg
          .filter([vid, logo], 'overlay', x=x, y=y, enable=f"between(t,{start},{start+duration})")
          .output(out_p, codec='libx264', crf=23, preset='veryfast')
          .overwrite_output()
          .run(quiet=True)
    )
    return out_fn