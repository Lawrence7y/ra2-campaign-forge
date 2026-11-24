#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 精细剖面：1px 列/行亮度，找凸缘边沿精确位置。"""
import os, sys, json
from PIL import Image

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I\EVIDENCE"

def lum(px,x,y):
    r,g,b=px[x,y][:3]; return 0.299*r+0.587*g+0.114*b

def main():
    src=sys.argv[1] if len(sys.argv)>1 else os.path.join(EVID,"after_deploy.png")
    img=Image.open(src).convert("RGB"); px=img.load()
    # 精细列剖面：空槽行带 y∈[600,1300]，x∈[2268,2420] 1px
    print("=== COL x2268..2420 (y600..1300 avg), 1px ===")
    for x in range(2268,2420):
        s=n=0
        for y in range(600,1300,3):
            s+=lum(px,x,y); n+=1
        print("%d:%.0f"%(x,s/n))
    # 精细行剖面：左列 interior x∈[2290,2380]，y∈[410,540] 1px
    print("=== ROW y410..540 (x2290..2380 avg), 1px ===")
    for y in range(410,540):
        s=n=0
        for x in range(2290,2380,2):
            s+=lum(px,x,y); n+=1
        print("%d:%.0f"%(y,s/n))

if __name__=="__main__": main()
