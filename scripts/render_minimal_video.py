#!/usr/bin/env python3
"""Minimal 60fps Naiwa campaign: no QR, UI panels, captions, or page furniture.

Optional --smooth-frames accepts motion-interpolated loop PNGs made with
prepare_smooth_frames.py. The release pet atlas is never modified.
"""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import math
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw
from render_media import ROOT, ATLAS, DURATIONS, STATES, font

BG = (246, 245, 238)
INK = (23, 63, 52)
FPS = 60
SIZE = (1080, 1920)
SCENES = [
    (0.0, 3.0, 0, "intro"), (3.0, 5.4, 3, "wave"),
    (5.4, 8.0, 1, "right"), (8.0, 10.6, 2, "left"),
    (10.6, 13.0, 4, "jump"), (13.0, 15.5, 5, "failed"),
    (15.5, 18.0, 6, "waiting"), (18.0, 20.5, 7, "thinking"),
    (20.5, 23.0, 8, "review"), (23.0, 27.0, 9, "look"),
    (27.0, 30.0, 3, "outro"),
]
NATIVE = {}
SMOOTH = {}


def ease(x):
    x=max(0.0,min(1.0,x))
    return x*x*x*(x*(x*6-15)+10)


def build_sources(smooth_root=None):
    for row in range(10):
        count = STATES[row][3] if row<9 else 16
        frames=[]
        for col in range(count):
            r,c=(row,col) if row<9 else (9+col//8,col%8)
            frames.append(ATLAS.crop((192*c,208*r,192*(c+1),208*(r+1))))
        NATIVE[row]=frames
        slug=STATES[row][0] if row<9 else "look"
        if smooth_root and (smooth_root/slug/"loop.json").is_file():
            meta=json.loads((smooth_root/slug/"loop.json").read_text())
            first=meta.get("first_index",0 if (smooth_root/slug/"00000000.png").exists() else 1)
            SMOOTH[row]=(smooth_root/slug,meta["subframes"],first)


@lru_cache(maxsize=160)
def interpolated(row,index):
    root,_,first=SMOOTH[row]
    im=Image.open(root/f"{index+first:08d}.png").convert("RGB")
    # Recover a transparent matte from the flat cream video background.
    rgb=np.asarray(im).astype(np.float32)
    bg=np.array(BG,dtype=np.float32)
    delta=np.max(np.abs(rgb-bg),axis=2)
    alpha=np.clip((delta-2)/22,0,1)
    color=np.clip((rgb-bg*(1-alpha[:,:,None]))/np.maximum(alpha[:,:,None],.001),0,255)
    return Image.fromarray(np.dstack((color,alpha*255)).astype(np.uint8),"RGBA")


def pose(row,t):
    if row==9:
        u=(t%4)/.25
        col=int(u)%16; fraction=u%1
    else:
        ds=DURATIONS[row];ms=(t*1000)%sum(ds)
        for col,d in enumerate(ds):
            if ms<d: break
            ms-=d
        fraction=ms/ds[col]
    if row in SMOOTH:
        _,sub,_=SMOOTH[row]
        i=int((col+fraction)*sub)%(len(NATIVE[row])*sub)
        return interpolated(row,i)
    # Preserve the source pixels when optional interpolation is unavailable.
    return NATIVE[row][col]


def actor(scene,t,at_end=False):
    start,end,row,kind=scene
    local=max(0,t-start); u=min(1,local/(end-start))
    x=540.0; baseline=1480.0; scale=4.15
    if kind=="intro":
        scale*=.94+.06*ease(local/2.3)
        baseline+=70*(1-ease(local/1.5))
    elif kind=="right": x=540+190*ease(u)
    elif kind=="left": x=730-190*ease(u)
    elif kind=="outro": scale*=1-.055*ease(local/2)
    im=pose(row,local)
    # Smooth camera motion runs at the final 60fps, independent of sprite cadence.
    if kind in {"intro","wave","waiting","thinking","review","outro"}:
        baseline+=2.0*math.sin(local*math.tau/3.2)
    width=round(im.width/192*scale*192)
    height=round(im.height/208*scale*208)
    # Interpolated sources use twice the atlas resolution.
    if im.width!=192: width=round(192*scale);height=round(208*scale)
    im=im.resize((width,height),Image.Resampling.LANCZOS)
    layer=Image.new("RGBA",SIZE,(0,0,0,0))
    layer.alpha_composite(im,(round(x-width/2),round(baseline-height)))
    return layer


def label_layer(t):
    layer=Image.new("RGBA",SIZE,(0,0,0,0))
    d=ImageDraw.Draw(layer)
    def line(value,y,size,alpha,latin=False):
        f=font(size,latin);b=d.textbbox((0,0),value,font=f)
        d.text(((1080-b[2]+b[0])/2,y),value,font=f,fill=(*INK,round(255*alpha)))
    if t<3:
        a=ease(t/.8)*(1-ease((t-2.2)/.6))
        line("奶蛙 Naiwa",330+18*(1-ease(t/.9)),80,a)
    if t>=27:
        a=ease((t-27.2)/.8)
        line("奶蛙 Naiwa",330+14*(1-a),80,a)
        line("Jekyll-Chan/naiwa-codex-pet",1595,30,a,True)
    return layer


def frame(t):
    n=next((i for i,s in enumerate(SCENES) if s[0]<=t<s[1]),len(SCENES)-1)
    scene=SCENES[n]
    layer=actor(scene,t)
    result=Image.new("RGBA",SIZE,(*BG,255))
    result.alpha_composite(layer)
    # Short, eased pose transitions maintain a continuous stage and ground line.
    transition=.20
    if n>0 and t-scene[0]<transition:
        a=ease((t-scene[0])/transition)
        previous=Image.new("RGBA",SIZE,(*BG,255))
        previous.alpha_composite(actor(SCENES[n-1],SCENES[n-1][1]-.001))
        result=Image.blend(previous,result,a)
    result.alpha_composite(label_layer(t))
    return result.convert("RGB")


def render(smooth_root=None,output=None):
    build_sources(smooth_root)
    out=output or ROOT/"media/tiktok/naiwa-tiktok-1080x1920.mp4"
    out.parent.mkdir(parents=True,exist_ok=True)
    with imageio.get_writer(out,fps=FPS,codec="libx264",quality=8,macro_block_size=2,
                            ffmpeg_params=["-movflags","+faststart"]) as writer:
        for i in range(30*FPS):
            writer.append_data(np.asarray(frame(i/FPS)))
            if i%(FPS*5)==0:print(f"Rendered {i//FPS}/30 seconds",flush=True)
    timeline={"size":list(SIZE),"duration":30,"fps":FPS,"style":"minimal; no QR; text only in intro and outro",
              "motion":"continuous eased staging, full source action cycles"+("; RIFE-interpolated character loops" if SMOOTH else ""),
              "audio":"none","scenes":[{"from":a,"to":b,"state":STATES[r][0] if r<9 else "16-direction look","kind":k} for a,b,r,k in SCENES]}
    (out.parent/"timeline.json").write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding="utf-8")
    frame(1.3).save(out.parent/"video-cover.png")
    print(out,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--smooth-frames",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args();render(a.smooth_frames,a.output)
