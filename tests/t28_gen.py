# Génère les PDF de test de t28 dans /tmp/claude-0/pdf (a12 : 12 pages bruitées ~9 Mo ; b700 : 700 pages ~56 Mo ; scan15 : 15 pages de type scan ~10 Mo)
from PIL import Image, ImageDraw, ImageFilter
import os,random
D='/tmp/claude-0/pdf';os.makedirs(D,exist_ok=True)
def noise(path,n,w,h):
  ims=[Image.frombytes('RGB',(w,h),os.urandom(w*h*3)) for _ in range(n)];ims[0].save(path,save_all=True,append_images=ims[1:],resolution=72,quality=95)
noise(D+'/a12.pdf',12,700,900);noise(D+'/b700.pdf',700,220,300)
ims=[]
for i in range(15):
  im=Image.new('RGB',(1700,2200),(250,248,240));d=ImageDraw.Draw(im)
  for y in range(150,2100,38):
    x=120
    while x<1550:
      w=random.randint(30,140);d.rectangle([x,y,x+w,y+14],fill=(30,30,40));x+=w+18
  d.ellipse([1200,1800,1500,2050],outline=(20,60,200),width=8);ims.append(im.filter(ImageFilter.GaussianBlur(0.8)))
ims[0].save(D+'/scan15.pdf',save_all=True,append_images=ims[1:],resolution=200,quality=97)
