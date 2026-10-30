#!/usr/bin/env python3
"""Prepare motion-interpolated video loops using official RIFE ncnn Vulkan.

Get the processor and models from https://github.com/nihui/rife-ncnn-vulkan
The tool/model are external and are not redistributed in this repository.
Only the promotional video uses these frames; the installed pet is unchanged.
"""
import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image
from render_media import ATLAS, STATES


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rife",type=Path,required=True)
    p.add_argument("--model",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--gpu",default="-1",help="-1 is CPU; 0 is first GPU")
    p.add_argument("--states",default="all")
    p.add_argument("--subframes",type=int,default=16,help="Intermediate sampling per source interval")
    a=p.parse_args()
    if a.subframes<2:p.error("--subframes must be at least 2")
    wanted=a.states.split(",")
    for row in range(10):
        slug=STATES[row][0] if row<9 else "look"
        if wanted!=["all"] and slug not in wanted:continue
        count=STATES[row][3] if row<9 else 16
        target=a.output/slug;src=a.output/(slug+"-source")
        target.mkdir(parents=True,exist_ok=True);src.mkdir(parents=True,exist_ok=True)
        if (target/"loop.json").exists():
            meta=json.loads((target/"loop.json").read_text())
            if meta["subframes"]!=a.subframes:
                raise ValueError(f"Cached sampling differs for {slug}; choose a fresh output directory.")
            print(f"Cached {slug}",flush=True);continue
        for c in range(count+1):
            col=c%count;r,k=(row,col) if row<9 else (9+col//8,col%8)
            sprite=ATLAS.crop((192*k,208*r,192*(k+1),208*(r+1)))
            im=Image.new("RGBA",(192,208),(246,245,238,255));im.alpha_composite(sprite)
            im.convert("RGB").resize((384,416),Image.Resampling.LANCZOS).save(src/f"{c:08d}.png")
        cmd=[str(a.rife.resolve()),"-i",str(src.resolve()),"-o",str(target.resolve()),
             "-m",str(a.model.resolve()),"-n",str(count*a.subframes+1),"-g",a.gpu,"-j","1:2:2","-f","%08d.png"]
        print(f"Smoothing {slug}",flush=True)
        result=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        if result.returncode:raise RuntimeError(result.stderr[-2000:])
        frames=sorted(target.glob("*.png"))
        if len(frames)!=count*a.subframes+1:raise RuntimeError(f"Unexpected frame count for {slug}: {len(frames)}")
        (target/"loop.json").write_text(json.dumps({"subframes":a.subframes,"poses":count,"frames":len(frames),"first_index":int(frames[0].stem),
            "processor":"RIFE ncnn Vulkan","model":a.model.name}),encoding="utf-8")
        print(f"Ready {slug}: {len(frames)} frames",flush=True)


if __name__=="__main__":main()
