import ffmpeg, os
BLENDED = os.path.join(os.path.dirname(__file__),'..','assets','blended')

def blend_uploaded(src: str, vid_id: str, ad: dict, slot: dict, reg: dict) -> str:
    s, d = slot.get('start',0), slot.get('duration',5)
    overlay = os.path.join(os.path.dirname(__file__),'..','assets','ads',ad['file'])
    out_fn = f"{vid_id}_{ad['id']}.mp4"
    out_p = os.path.join(BLENDED,out_fn)
    x,y = reg.get('x',0), reg.get('y',0)
    vid = ffmpeg.input(src)
    logo= ffmpeg.input(overlay)
    (ffmpeg.filter([vid,logo],'overlay',x=x,y=y,enable=f"between(t,{s},{s+d})")
           .output(out_p,codec='libx264',crf=23,preset='veryfast')
           .overwrite_output().run(quiet=True))
    return out_fn