#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""稳健放置器 v2：找纯绿格(red<150,green>8000)才点击；点击路径不调用 force_foreground
（避免夺焦取消 ghost）。下单/拿起/放置全流程，逐次三重佐证。"""
import argparse, ctypes, json, os, sys, time
from PIL import ImageGrab
import w177_core as W, wb_probe as P, wc_probe as C
from w177_click import click_client, move_client, force_foreground, game_hwnd

HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
ICON=(2328,480)
try: ctypes.windll.user32.SetProcessDPIAware()
except Exception: pass
u32=ctypes.windll.user32

CAND=[(1300,500),(1280,470),(1320,530),(1360,560),(1400,590),(1440,620),
      (1260,560),(1220,600),(1180,640),(1500,500),(1540,470),(1580,500),
      (1660,470),(1700,500),(1740,530),(1780,560),(1820,590),(1860,620),
      (1900,650),(1940,680),(1980,700),(2020,660),(2060,620),(1560,640),
      (1500,680),(1620,680),(1680,700),(1740,720),(1800,680),(1200,500),
      (1150,560),(1100,620),(1050,680),(1350,650),(1450,700)]


def colors(img,sx,sy,rad=70):
    im=img.convert('RGB'); px=im.load(); r=g=0
    for y in range(max(0,sy-rad),min(img.height,sy+rad)):
        for x in range(max(0,sx-rad),min(img.width,sx+rad)):
            R,G,B=px[x,y]
            if R>150 and G<90 and B<90: r+=1
            if G>140 and R<120 and B<120: g+=1
    return r,g


def stable_credit(m,ph,tries=14,gap=0.2):
    prev=None; st=0
    for _ in range(tries):
        cur=m.u32(ph+0x30C)
        if cur==prev:
            st+=1
            if st>=2: return cur
        else: st=0
        prev=cur; time.sleep(gap)
    return m.u32(ph+0x30C)


def pnap(m,ph):
    return [o for o in C.napowr_objects(m,ph) if o['is_player']]
def placed(m,ph):
    return {o['obj'] for o in pnap(m,ph) if o['o1_81']==0 and o['o2_74']==1 and o['valid']}


def find_pure_green(pid,cands,used):
    for (x,y) in cands:
        if (x,y) in used: continue
        move_client(pid,x,y); time.sleep(0.16)
        img=ImageGrab.grab(all_screens=False)
        r,g=colors(img,x,y)
        if g>=8000 and r<150:
            return (x,y,r,g,img)
    return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--n',type=int,default=1)
    ap.add_argument('--prefix',default='A')
    ap.add_argument('--start-num',type=int,default=2)
    ap.add_argument('--reuse-limbo',action='store_true',help='skip order; pick up existing ready limbo')
    a=ap.parse_args()
    pid=W.pid_of(); m=W.Mem(pid); ph=P.player_house(m)
    used=set()
    log=os.path.join(EVID,a.prefix+'_auto2.jsonl')
    for k in range(a.n):
        num=a.start_num+k
        tag='%s%02d'%(a.prefix,num)
        rec={'tag':tag,'ts':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        c0=stable_credit(m,ph); before=placed(m,ph)
        rec['credit_before_order']=c0
        if not a.reuse_limbo or k>0:
            ok,info=click_client(pid,*ICON,'left'); time.sleep(0.35)
            c1=stable_credit(m,ph)
            rec['order']={'ok':ok,'credit_after':c1,'deduct_600':(c1==c0-600)}
            time.sleep(4.0)  # wait ready longer
        else:
            c1=c0
            rec['order']={'skipped_reuse':True}
        # pick up ghost
        ok2,_=click_client(pid,*ICON,'left'); time.sleep(0.30)
        rec['pickup']={'ok':ok2}
        found=find_pure_green(pid,CAND,used)
        if not found:
            rec['result']='NO_PURE_GREEN'; print(json.dumps(rec,ensure_ascii=False)); break
        x,y,r,g,img=found; used.add((x,y))
        img.save(os.path.join(EVID,tag+'_hover.png'))
        rec['target']={'xy':[x,y],'red':r,'green':g}
        # click WITHOUT force_foreground
        u32.SetCursorPos(x,y); time.sleep(0.10)
        u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.12); u32.mouse_event(0x0004,0,0,0,0)
        time.sleep(1.4)
        ImageGrab.grab(all_screens=False).save(os.path.join(EVID,tag+'_after.png'))
        c2=stable_credit(m,ph); after=placed(m,ph); new=after-before
        tri=None
        if new:
            obj=sorted(new)[0]
            o=[z for z in pnap(m,ph) if z['obj']==obj][0]
            in_chain=(obj in o['nodesA']) or (obj in o['nodesB'])
            tri={'obj':obj,'owner':o['owner'],'owner_is_player':o['is_player'],
                 'o1':o['o1_81'],'o2':o['o2_74'],'cell':[o['cellX'],o['cellY']],
                 'valid':o['valid'],'in_cell_chain':in_chain,'lenA':o['lenA'],'lenB':o['lenB']}
            tri['attested']=bool(tri['owner_is_player'] and tri['valid'] and in_chain and o['o1_81']==0 and o['o2_74']==1)
        rec['after']={'credit':c2,'new':sorted(new),'triple':tri}
        rec['success']=bool(tri and tri['attested'])
        print(json.dumps({'tag':tag,'xy':[x,y],'red':r,'green':g,
                          'deduct':rec.get('order',{}).get('deduct_600'),
                          'success':rec['success'],'triple':tri},ensure_ascii=False))
        with open(log,'a',encoding='utf-8') as f:
            f.write(json.dumps(rec,ensure_ascii=False,default=str)+'\n')
    print('final_credit',stable_credit(m,ph))
    return 0

if __name__=='__main__': sys.exit(main())
