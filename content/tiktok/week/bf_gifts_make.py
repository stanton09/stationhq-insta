from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess, os, math
W,H=1080,1920; FPS=30
D='/home/claude/remote/content/blackfriday/'
OSW='/home/claude/fit/fonts/Oswald.ttf'; ANTON='/home/claude/fit/fonts/Anton-Regular.ttf'
def font(p,s):
    f=ImageFont.truetype(p,s)
    try: f.set_variation_by_name('Bold')
    except Exception: pass
    return f
cards=['bf_gifts_dark','bf_hats_snow','bf_mugs_stripe','bf_family_wood','bf_kids_paper','bf_stockings_stripe']
CARD_S=2.3; INTRO=2.0; OUTRO=2.8
out='/home/claude/bfvid/frames'; os.makedirs(out,exist_ok=True)
for f in os.listdir(out): os.remove(os.path.join(out,f))
def bg_from(img):
    b=img.resize((W,int(W*img.height/img.width))).resize((W,H)).filter(ImageFilter.GaussianBlur(40))
    return Image.blend(b,Image.new('RGB',(W,H),(0,0,0)),0.45)
def text_center(d,y,txt,f,fill=(255,255,255),stroke=6):
    d.text((W/2,y),txt,font=f,fill=fill,anchor='mm',stroke_width=stroke,stroke_fill=(0,0,0))
n=0
def save(im):
    global n; im.save(f'{out}/f{n:05d}.jpg',quality=90); n+=1
# intro: hook over first card blurred
first=Image.open(D+cards[0]+'.jpg').convert('RGB'); bg0=bg_from(first)
for i in range(int(INTRO*FPS)):
    im=bg0.copy(); d=ImageDraw.Draw(im); t=i/(INTRO*FPS)
    s=min(1,t*4)
    text_center(d,760,"Firefighter gifts",font(ANTON,int(120*(0.85+0.15*s))))
    text_center(d,900,"that aren't from a",font(ANTON,int(96*(0.85+0.15*s))))
    text_center(d,1030,"costume shop 🚒".replace(' 🚒',''),font(ANTON,int(120*(0.85+0.15*s))),fill=(255,214,70))
    text_center(d,1210,"Designed by an active firefighter",font(OSW,54),fill=(235,235,235),stroke=4)
    save(im)
# cards with slow zoom
for c in cards:
    img=Image.open(D+c+'.jpg').convert('RGB'); bg=bg_from(img)
    for i in range(int(CARD_S*FPS)):
        t=i/(CARD_S*FPS); z=1.0+0.06*t
        cw=int(1000*z); ch=int(cw*img.height/img.width)
        card=img.resize((cw,ch),Image.LANCZOS)
        im=bg.copy(); im.paste(card,((W-cw)//2,(H-ch)//2-40))
        d=ImageDraw.Draw(im)
        text_center(d,170,"20% OFF EVERYTHING",font(ANTON,92),fill=(255,214,70))
        text_center(d,H-200,"Link in bio  ·  shop.stationhq.app",font(OSW,52),stroke=4)
        save(im)
# outro
last=Image.open(D+'bf_everything_kraft.jpg').convert('RGB'); bgl=bg_from(last)
for i in range(int(OUTRO*FPS)):
    im=bgl.copy(); d=ImageDraw.Draw(im)
    text_center(d,700,"BLACK FRIDAY",font(ANTON,150),fill=(255,214,70))
    text_center(d,860,"20% off everything",font(ANTON,110))
    text_center(d,980,"Ends Dec 1",font(ANTON,90),fill=(255,90,90))
    text_center(d,1160,"Order by Dec 10 for Christmas",font(OSW,56),stroke=4)
    text_center(d,1320,"Link in bio",font(ANTON,80))
    save(im)
dur=n/FPS
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{out}/f%05d.jpg','-i','/home/claude/remote/brand/roy/music_ready_aim_fire.mp3',
  '-t',f'{dur:.2f}','-af',f'afade=t=in:d=0.3,afade=t=out:st={dur-1.2:.2f}:d=1.2,volume=0.8','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',
  '-c:a','aac','-b:a','160k','-shortest','/home/claude/bfvid/bf_gifts.mp4'],check=True)
print(n,dur)
