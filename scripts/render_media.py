#!/usr/bin/env python3
"""Compose campaign graphics and video from Naiwa's existing sprite pixels.

No character artwork is generated or redrawn. Requires requirements-dev.txt.
Fonts can be overridden for Linux/Windows using NAIWA_FONT and NAIWA_LATIN_FONT.
"""
from pathlib import Path
import json
import math
import os
import sys
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import qrcode

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "media"
TIKTOK = OUT / "tiktok"
TIKTOK.mkdir(parents=True, exist_ok=True)
ATLAS = Image.open(ROOT / "pets/naiwa/spritesheet.png").convert("RGBA")
FONT = os.environ.get("NAIWA_FONT", "/System/Library/Fonts/Hiragino Sans GB.ttc")
LATIN = os.environ.get("NAIWA_LATIN_FONT", "/System/Library/Fonts/Avenir Next.ttc")
BG = "#F6F5EE"
INK = "#173F34"
SOFT = "#E1ECE1"
MINT = "#D2E5D6"
YELLOW = "#F5CD53"
GREY = "#63756B"
WHITE = "#FFFFFF"
REPO = "https://github.com/Jekyll-Chan/naiwa-codex-pet"
SHARE = "https://chatgpt.com/s/sharepet_6ae4aa47fa508191b009739633003af2"
STATES = [
    ("idle", "发呆，也是陪伴", "IDLE", 6),
    ("running-right", "向右，小跑两步", "MOVE RIGHT", 8),
    ("running-left", "向左，跟上你", "MOVE LEFT", 8),
    ("waving", "嗨，又见面了", "SAY HELLO", 4),
    ("jumping", "开心到起飞", "LITTLE JUMP", 5),
    ("failed", "没关系，再试一次", "TRY AGAIN", 8),
    ("waiting", "等你一个点头", "NEEDS INPUT", 6),
    ("running", "正在认真思考", "FOCUS MODE", 6),
    ("review", "帮你再检查一遍", "FINAL CHECK", 6),
]
DURATIONS = [[280,110,110,140,140,320],[120]*7+[220],[120]*7+[220],
             [140]*3+[280],[140]*4+[280],[140]*7+[240],[150]*5+[260],
             [120]*5+[220],[150]*5+[280]]
ANGLES = ["000","022.5","045","067.5","090","112.5","135","157.5",
          "180","202.5","225","247.5","270","292.5","315","337.5"]


def font(size, latin=False):
    return ImageFont.truetype(LATIN if latin else FONT, size)


def text(im, xy, value, size, fill=INK, latin=False):
    ImageDraw.Draw(im).text(xy, value, font=font(size, latin), fill=fill)


def box(im, bounds, fill=WHITE, radius=36, outline=None, width=2):
    ImageDraw.Draw(im).rounded_rectangle(bounds, radius, fill=fill, outline=outline, width=width)


def centered(im, y, value, size, fill=INK, latin=False):
    f = font(size, latin)
    b = ImageDraw.Draw(im).textbbox((0,0),value,font=f)
    text(im, ((im.width-(b[2]-b[0]))/2,y),value,size,fill,latin)


def cell(row, col):
    return ATLAS.crop((192*col,208*row,192*(col+1),208*(row+1)))


def frame_at(row, seconds):
    ds = DURATIONS[row]
    t = int(seconds*1000) % sum(ds)
    for c, d in enumerate(ds):
        if t < d: return c
        t -= d
    return 0


def pet(im, row, col, bounds, tight=True):
    sprite = cell(row,col)
    if tight: sprite = sprite.crop(sprite.getbbox())
    x1,y1,x2,y2 = bounds
    scale = min((x2-x1)/sprite.width,(y2-y1)/sprite.height)
    sprite = sprite.resize((round(sprite.width*scale),round(sprite.height*scale)),Image.Resampling.LANCZOS)
    im.alpha_composite(sprite,(round((x1+x2-sprite.width)/2),round(y2-sprite.height)))


def base(page, kicker):
    im = Image.new("RGBA",(1080,1920),BG)
    box(im,(64,64,274,118),INK,27)
    text(im,(87,72),"NAIWA / 奶蛙",24,WHITE)
    text(im,(64,155),kicker,25,GREY,True)
    ImageDraw.Draw(im).line((64,1778,1016,1778),fill="#C5D3C8",width=2)
    text(im,(64,1800),"A LITTLE COMPANY FOR YOUR CODEX.",22,GREY,True)
    text(im,(941,1800),f"{page:02d} / 07",21,GREY,True)
    return im


def cover(t=0):
    im=base(1,"MEET YOUR NEW DESKMATE")
    text(im,(64,234),"奶蛙",150)
    text(im,(68,420),"Naiwa",86,latin=True)
    text(im,(68,550),"给你的 Codex，添一点陪伴。",42)
    box(im,(64,660,1016,1470),MINT,70)
    # Existing generated sprite, enlarged without changing its character design.
    pet(im,0,frame_at(0,t),(240,720,840,1380))
    box(im,(730,735,960,791),WHITE,28)
    text(im,(757,747),"HELLO, HUMAN.",21,INK,True)
    text(im,(67,1530),"会思考 · 会等待 · 会和你庆祝",34)
    text(im,(67,1605),"9 种动画状态  /  16 个注视方向",30,GREY)
    return im


def desktop(t=0):
    im=base(2,"COMPANY WHILE YOU CREATE")
    text(im,(64,235),"你专注创造。",76)
    text(im,(64,340),"它陪在一旁。",76)
    text(im,(64,476),"工作状态，一眼就懂。",35,GREY)
    box(im,(64,600,1016,1460),SOFT,52)
    box(im,(106,651,974,1188),WHITE,28)
    text(im,(142,690),"TODAY'S LITTLE PROJECT",25,INK,True)
    for i,w in enumerate([540,680,430,610,500]):
        box(im,(142,765+i*60,142+w,783+i*60),"#DDE5DC",9)
    box(im,(142,1090,562,1141),INK,25)
    text(im,(166,1101),"把想法慢慢做出来",25,WHITE)
    pet(im,7,frame_at(7,t),(615,1000,936,1410))
    box(im,(128,1280,594,1384),WHITE,32)
    text(im,(159,1308),"奶蛙正在认真思考…",29)
    text(im,(72,1525),"发起任务 → 等待输入 → 检查完成",31)
    text(im,(72,1602),"使用效果示意 · 非 Codex 界面实录",25,GREY)
    return im


def state_page(page, indices, heading, subtitle):
    im=base(page,"EVERY MOOD, EVERY MOMENT")
    text(im,(64,235),heading,76)
    text(im,(64,351),subtitle,32,GREY)
    for slot,row in enumerate(indices):
        top=485+slot*402
        box(im,(64,top,1016,top+366),WHITE,38)
        pet(im,row,[0,0,0,2,2,4,2,2,2][row],(100,top+24,330,top+335))
        text(im,(391,top+69),f"0{row+1} / {STATES[row][2]}",24,GREY,True)
        text(im,(391,top+134),STATES[row][1],38)
        descriptions=["呼吸和眨眼的安静循环。","拖动时，朝屏幕右侧小跑。","换个方向，也跟得上。",
            "伸出小手，向你打招呼。","起跳、腾空，再稳稳落地。","失落一下，然后继续。",
            "等你批准，或给一点帮助。","脚步不动，脑袋在忙。","凑近看看，认真检查。"]
        text(im,(391,top+210),descriptions[row],24,GREY)
    return im


def look_page(t=None):
    im=base(6,"A CURIOUS LITTLE COMPANION")
    text(im,(64,235),"你的方向，",76)
    text(im,(64,340),"就是它的目光。",76)
    text(im,(64,474),"16 个方向，顺时针看世界。",32,GREY)
    for i,a in enumerate(ANGLES):
        x=64+(i%4)*244; y=602+(i//4)*277
        box(im,(x,y,x+220,y+253),WHITE,26)
        pet(im,9+i//8,i%8,(x+30,y+16,x+190,y+209))
        text(im,(x+63,y+216),a+"°",22,GREY,True)
    return im


def qr(im,url,xy,size=220):
    q=qrcode.QRCode(box_size=8,border=2,error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(url);q.make(fit=True)
    pic=q.make_image(fill_color=INK,back_color=WHITE).convert("RGBA").resize((size,size),Image.Resampling.NEAREST)
    im.alpha_composite(pic,xy)


def cta(t=0):
    im=base(7,"TAKE NAIWA HOME")
    text(im,(64,235),"把奶蛙带回家。",76)
    text(im,(64,365),"给下一次专注，多一个陪伴。",36,GREY)
    box(im,(64,509,1016,1173),MINT,55)
    pet(im,3,frame_at(3,t),(337,565,745,1110))
    box(im,(64,1236,1016,1665),WHITE,38)
    text(im,(100,1280),"Jekyll-Chan /",30,GREY,True)
    text(im,(100,1332),"naiwa-codex-pet",42,INK,True)
    text(im,(100,1427),"GitHub 下载 · 安装说明 · 全形态预览",27)
    text(im,(100,1490),"分享链接，也可以直接领养。",27,GREY)
    qr(im,REPO,(726,1285),235)
    text(im,(754,1540),"扫码查看项目",23,GREY)
    return im


def hero_state(row,t):
    im=base(3+min(row//3,2),"NINE WAYS TO BE THERE")
    text(im,(64,232),STATES[row][1],67)
    text(im,(67,348),STATES[row][2],33,GREY,True)
    box(im,(64,506,1016,1467),MINT,66)
    pet(im,row,frame_at(row,t),(244,595,836,1367),tight=False)
    for i in range(9):
        ImageDraw.Draw(im).ellipse((139+i*93,1560,161+i*93,1582),fill=INK if i==row else "#CCD7CD")
    centered(im,1633,f"{row+1:02d} / 09   ANIMATION STATES",24,GREY,True)
    return im


def look_video(t):
    im=base(6,"SIXTEEN LITTLE LOOKS")
    text(im,(64,235),"它会看向你。",76)
    text(im,(67,353),"16 个方向，一整圈好奇心。",33,GREY)
    box(im,(64,506,1016,1470),MINT,66)
    i=int(t/0.375)%16
    pet(im,9+i//8,i%8,(244,595,836,1367),tight=False)
    centered(im,1550,ANGLES[i]+"°",46,INK,True)
    centered(im,1633,"REAL SPRITE ANIMATION / 实际动画帧",23,GREY)
    return im


def all_states(t):
    im=base(5,"THE WHOLE LITTLE FAMILY")
    text(im,(64,235),"每个状态，都有它。",67)
    text(im,(67,352),"陪你走过一次完整的工作节奏。",32,GREY)
    for r in range(9):
        x=64+(r%3)*326;y=540+(r//3)*381
        box(im,(x,y,x+300,y+353),WHITE,28)
        pet(im,r,frame_at(r,t),(x+56,y+28,x+244,y+271),tight=False)
        text(im,(x+27,y+292),STATES[r][2],20,GREY,True)
    return im


def main():
    slides=[cover(),desktop(),state_page(3,[0,1,2],"安静，也有小动作。","待机与左右移动 / 01–03"),
            state_page(4,[3,4,5],"情绪，都藏不住。","打招呼、跳跃与失落 / 04–06"),
            state_page(5,[6,7,8],"陪你把事情做好。","等待、思考与检查 / 07–09"),look_page(),cta()]
    for i,im in enumerate(slides,1): im.convert("RGB").save(TIKTOK/f"{i:02d}.png")
    # Compact GitHub social/README banner.
    banner=Image.new("RGBA",(1600,900),BG)
    text(banner,(100,130),"奶蛙",140);text(banner,(105,320),"NAIWA",70,INK,True)
    text(banner,(105,464),"给你的 Codex，添一点陪伴。",39)
    text(banner,(105,573),"9 ANIMATION STATES   /   16 LOOK DIRECTIONS",24,GREY,True)
    box(banner,(916,66,1530,830),MINT,66)
    pet(banner,0,0,(1010,125,1436,777))
    banner.convert("RGB").save(OUT/"naiwa-banner.png")
    # Per-state transparent GIFs from the exact release atlas.
    anim=OUT/"animations";anim.mkdir(exist_ok=True)
    for r,(slug,_,_,count) in enumerate(STATES):
        fs=[cell(r,c) for c in range(count)]
        fs[0].save(anim/f"{slug}.gif",save_all=True,append_images=fs[1:],duration=DURATIONS[r],loop=0,disposal=2)
    loop=[cell(9+i//8,i%8) for i in range(16)]
    loop[0].save(anim/"look-around.gif",save_all=True,append_images=loop[1:],duration=160,loop=0,disposal=2)
    if "--images-only" in sys.argv: return
    fps=24;duration=32
    # Video uses 12 distinct frames/sec, encoded as 24fps for upload compatibility.
    with imageio.get_writer(TIKTOK/"naiwa-tiktok-1080x1920.mp4",fps=fps,codec="libx264",quality=8,macro_block_size=2,
                            ffmpeg_params=["-pix_fmt","yuv420p","-movflags","+faststart"]) as writer:
        for n in range(duration*12):
            t=n/12
            if t<4: im=cover(t)
            elif t<8: im=desktop(t-4)
            elif t<17: im=hero_state(min(8,int(t-8)),t-8)
            elif t<23: im=look_video(t-17)
            elif t<28: im=all_states(t-23)
            else: im=cta(t-28)
            arr=np.asarray(im.convert("RGB"));writer.append_data(arr);writer.append_data(arr)
    (TIKTOK/"timeline.json").write_text(json.dumps({"size":[1080,1920],"duration":32,"fps":24,"audio":"none; add a licensed sound in TikTok", "scenes":[
        {"from":0,"to":4,"scene":"Meet Naiwa"},{"from":4,"to":8,"scene":"Illustrated usage, not app footage"},
        {"from":8,"to":17,"scene":"All 9 animation states, one second each"},
        {"from":17,"to":23,"scene":"All 16 look directions, 0.375 seconds each"},
        {"from":23,"to":28,"scene":"All states together"},{"from":28,"to":32,"scene":"GitHub and adoption CTA"}]},indent=2),encoding="utf-8")
    print(TIKTOK)


if __name__ == "__main__": main()
