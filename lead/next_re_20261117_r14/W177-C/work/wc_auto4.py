#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-C 目标A 稳健终版：下单扣600->等ready(7s)->点图标拿ghost(未激活则重试)->整块footprint纯绿才点击->三重佐证。"""
import argparse, ctypes, json, os, sys, time
from PIL import ImageGrab
import w177_core as W, wb_probe as P, wc_probe as C
from w177_click import click_client, move_client, force_foreground, game_hwnd

HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
ICON=(2328,480); u32=ctypes.windll.user32
try: u32.SetProcessDPIAware()
except Exception: pass

CAND=[(1450,720),(1350,720),(1650,780),(1750,780),(1850,780),(1950,780),
      (2050,780),(1450,780),(1550,420),(1650,420),(1750,420),(1550,660),
      (1650,660),(1850,660),(1950,660),(2050,660),(1250,660),(1350,660),
      (1150,480),(1250,720),(1150,720),(1750,480),(1850,540),(2050,720)]


def colors(img,sx,sy,rad=120):
    im=img.convert('RGB'); px=im.load(); r=g=0
    for y in range(max(0,sy-rad),min(img.height,sy+rad)):
        for x in range(max(0,sx-rad),min(img.width,sx+rad)):
            R,G,B=px[x,y]
            if R>150 and G<90 and B<90: r+=1
            if G>140 and R<120 and B<120: g+=1
    return r,g


def stable_credit(m,ph,tries=20,gap=0.18):
    prev=None; st=0
    for _ in range(tries):
        cur=m.u32(ph+0x30C)
        if cur==prev:
            st+=1
            if st>=2: return cur
        else: st=0
        prev=cur; time.sleep(gap)
    return m.u32(ph+0x30C)


def pnap(m,ph): return [o for o in C.napowr_objects(m,ph) if o['is_player']]
def placed(m,ph): return {o['obj'] for o in pnap(m,ph) if o['o1_81']==0 and o['o2_74']==1 and o['valid']}


def find_green(pid,cands,used):
    for (x,y) in cands:
        if (x,y) in used: continue
        move_client(pid,x,y); time.sleep(0.13)
        img=ImageGrab.grab(all_screens=False)
        r,g=colors(img,x,y,120)
        if r<200 and g>9000: return (x,y,r,g)
    return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--n',type=int,default=8)
    ap.add_argument('--start-num',type=int,default=3)
    ap.add_argument('--prefix',default='A')
    ap.add_argument('--active-ghost',action='store_true')
    ap.add_argument('--wait-ready',type=float,default=7.0)
    a=ap.parse_args()
    pid=W.pid_of(); m=W.Mem(pid); ph=P.player_house(m)
    used=set(); log=os.path.join(EVID,a.prefix+'_auto4.jsonl')
    for k in range(a.n):
        num=a.start_num+k; tag='%s%02d'%(a.prefix,num)
        rec={'tag':tag,'ts':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        c0=stable_credit(m,ph); before=placed(m,ph); rec['credit_before_order']=c0
        first_active=(k==0 and a.active_ghost)
        if first_active:
            rec['order']={'skipped_active_ghost':True}
            found=find_green(pid,CAND,used)
            rec['pickup']={'active_ghost':True,'green_found':bool(found)}
        else:
            ok,info=click_client(pid,*ICON,'left'); time.sleep(0.35)
            c1=stable_credit(m,ph)
            rec['order']={'ok':ok,'credit_after':c1,'deduct_600':(c1==c0-600)}
            time.sleep(a.wait_ready)
            found=None; picks=[]
            for attempt in range(5):
                ok2,_=click_client(pid,*ICON,'left'); time.sleep(0.30)
                found=find_green(pid,CAND,used)
                picks.append({'attempt':attempt,'ok':ok2,'green_found':bool(found)})
                if found: break
                time.sleep(0.8)
            rec['pickup_retries']=picks
        if not found:
            rec['result']='NO_GREEN'; print(json.dumps(rec,ensure_ascii=False))
            with open(log,'a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
            break
        x,y,r,g=found; used.add((x,y))
        move_client(pid,x,y); time.sleep(0.12)
        force_foreground(game_hwnd(pid)); time.sleep(0.12)
        img=ImageGrab.grab(all_screens=False)
        r2,g2=colors(img,x,y,120)
        img.save(os.path.join(EVID,tag+'_hover.png'))
        rec['target']={'xy':[x,y],'red':r,'green':g,'red_fg':r2,'green_fg':g2}
        u32.SetCursorPos(x,y); time.sleep(0.08)
        u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.12); u32.mouse_event(0x0004,0,0,0,0)
        time.sleep(1.5)
        ImageGrab.grab(all_screens=False).save(os.path.join(EVID,tag+'_after.png'))
        c2=stable_credit(m,ph); after=placed(m,ph); new=after-before
        tri=None
        if new:
            obj=sorted(new)[0]; o=[z for z in pnap(m,ph) if z['obj']==obj][0]
            in_chain=(obj in o['nodesA']) or (obj in o['nodesB'])
            tri={'obj':obj,'owner':o['owner'],'owner_is_player':o['is_player'],
                 'o1':o['o1_81'],'o2':o['o2_74'],'cell':[o['cellX'],o['cellY']],
                 'valid':o['valid'],'in_cell_chain':in_chain,'lenA':o['lenA'],'lenB':o['lenB']}
            tri['attested']=bool(tri['owner_is_player'] and tri['valid'] and in_chain and o['o1_81']==0 and o['o2_74']==1)
        rec['after']={'credit':c2,'new':sorted(new),'triple':tri}
        rec['success']=bool(tri and tri['attested'])
        print(json.dumps({'tag':tag,'xy':[x,y],'r':r,'g':g,
                          'deduct':rec.get('order',{}).get('deduct_600'),
                          'success':rec['success'],'triple':tri},ensure_ascii=False))
        with open(log,'a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False,default=str)+'\n')
    print('final_credit',stable_credit(m,ph))
    return 0

if __name__=='__main__': sys.exit(main())
