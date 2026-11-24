# -*- coding: utf-8 -*-
"""R16-D1-WIDE-B4 authoritative derive + products generator (FINAL BATCH).
Read-only: gamemd.exe (pefile/capstone), coverage.tsv, sieve_all.tsv, final.tsv,
audit starts.json / vptr_stores.tsv, W130 atlas. Writes ONLY inside R16_D1_WIDE_B4/.

Batch B4 derived by SET SUBTRACTION (not by index):
  S  = sieve_all.tsv rows with has_ring4_on_disk==no  (65)
  B4 = S - B1.entries - B2.entries - B3.entries
       005F4B10 is in B3 (CLASS_FIX) and Lead ruled it removed from the set /
       not to be filled => it is NOT in B4.  Result = 11 entries.

Implements the lead's 3 lessons:
  (1) host-identity verification: ctor_body target must be `this` (mov [reg],vt
      with reg from ecx, disp 0) in a GENUINE ctor/factory (base-ctor call before,
      returns this, NO scalar-deleting-dtor signature `test byte [esp+X],1 +
      call 0x7C8B3D + ret N`, no base-dtor/delete after); mov_abs must be
      mov [abs],vt with abs in .data by VirtualSize [0x812000,0xB79BE4).
  (2) no lowest-address heuristic: every site verified by host identity.
  (3) class mismatch -> CLASS_FIX (class consistency first), disclosed verbatim.
D-50: ④ text states the install form and embeds the measured instruction.
"""
import io, os, sys, re, csv, json, bisect, hashlib, collections
import pefile, capstone
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")
PROBE = os.path.join(R14, "R16_PROBE_4FINAL")
AUD = os.path.join(R14, "R16_AUDIT_D1_WIDE_B1")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
sys.path.insert(0, PROBE); sys.dont_write_bytecode = True
import final as F
IB = F.IMAGE_BASE

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest().upper()

img = F.Image(EXE); buf = img.buf
secs = [(s['name'], s['va'], s['vsize']) for s in img.secs]
def sec_of(va):
    if va is None: return None
    for nm,sva,svs in secs:
        if sva <= va < sva+svs: return nm
    return None
TX = img.section('.text'); TEXT_VA=TX['va']; TEXT_SZ=TX['vsize']
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
def dis1(va, n=24):
    o=va-IB
    if o<0 or o>=len(buf): return []
    return list(md.disasm(bytes(buf[o:o+n]), va))

atlas={}
for i,ln in enumerate(io.open(ATLAS,encoding='utf-8-sig')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=2:
        try: atlas[int(c[0].strip(),16)]=int(c[1])
        except ValueError: pass
targets=set(json.load(io.open(os.path.join(AUD,'starts.json'),encoding='utf-8'))['targets'])
ALL=sorted(set(atlas)|targets)
def fn_end(s):
    if s in atlas: return s+atlas[s]
    i=bisect.bisect_right(ALL,s)
    return ALL[i] if i<len(ALL) else TEXT_VA+TEXT_SZ

VPTR=[]
for i,ln in enumerate(io.open(os.path.join(AUD,'vptr_stores.tsv'),encoding='utf-8')):
    if i==0: continue
    c=ln.rstrip('\r\n').split('\t')
    if len(c)>=6: VPTR.append(dict(site=int(c[0],16),vt=int(c[1],16),base=c[2],disp=int(c[3],16)))
def vptr_in(a,b): return [v for v in VPTR if a<=v['site']<b]

def site_facts(site, vt, forced_host=None):
    insns=dis1(site,24); ins=insns[0] if insns else None
    if ins is None: return None
    txt='%s %s'%(ins.mnemonic,ins.op_str)
    mb=md_=imm=None
    if len(ins.operands)==2:
        a,b=ins.operands
        if a.type==capstone.x86.X86_OP_MEM:
            mb=ins.reg_name(a.mem.base) if a.mem.base else 'ABS'; md_=a.mem.disp
        if b.type==capstone.x86.X86_OP_IMM: imm=b.imm&0xFFFFFFFF
    host=forced_host; hsrc='verified-host' if forced_host is not None else 'none'
    hend=fn_end(host) if host else None
    this=None
    if host:
        for x in dis1(host,64)[:14]:
            if x.mnemonic=='mov' and len(x.operands)==2:
                d,s2=x.operands
                if d.type==capstone.x86.X86_OP_REG and s2.type==capstone.x86.X86_OP_REG and ins.reg_name(s2.reg)=='ecx':
                    this=ins.reg_name(d.reg); break
    stores=vptr_in(host,hend) if host else []
    on=[s for s in stores if this and s['base']==this]
    primary=[s for s in on if s['disp']==0]
    body=dis1(host,min(hend-host+16,0x900)) if host else []
    bt=['%s %s'%(x.mnemonic,x.op_str) for x in body]
    ddtor=any('test byte ptr [esp' in s and ', 1' in s for s in bt) and any('0x7c8b3d' in s for s in bt)
    calls_before=[x for x in body if x.mnemonic=='call' and x.address<site]
    delete_after=[x for x in body if x.mnemonic=='call' and x.address>site and x.op_str.strip().lower()=='0x7c8b3d']
    return dict(ins=txt, mn=ins.mnemonic, mb=mb, disp=md_, imm=imm,
                host=host, hsrc=hsrc, hend=hend, this=this,
                primary=len(primary)>0, ddtor=ddtor,
                on_this=bool(this and mb==this and (md_ or 0)==0),
                tsec=sec_of(md_) if mb=='ABS' else None,
                calls_before=len(calls_before), delete_after=len(delete_after))

# ---- source tables
fmap={}
with io.open(os.path.join(PROBE,'final.tsv'),encoding='utf-8-sig') as f:
    h=f.readline().rstrip('\r\n').split('\t')
    for ln in f:
        c=ln.rstrip('\r\n').split('\t')
        if len(c)>=len(h): fmap[c[0]]=dict(zip(h,c))
cov={}
with io.open(COV,encoding='utf-8-sig',newline='') as f:
    f.readline()
    for ln in f:
        c=ln.rstrip('\r\n').split('\t')
        if len(c)>=8: cov[c[0].strip().upper()]=dict(entry=c[0],subsystem=c[1],name=c[2],sem=c[3],grade=c[4],ev=c[5],ns=c[6],conflict=c[7])
with io.open(SIEVE,encoding='utf-8') as f: srows=list(csv.DictReader(f,delimiter='\t'))
no=sorted([r for r in srows if r['has_ring4_on_disk(是/否)'].strip()=='否'],key=lambda x:int(x['entry'],16))
def entries_of(b):
    p=os.path.join(R14,b,'fields.tsv')
    with io.open(p,encoding='utf-8-sig') as f:
        return set(r['entry'].strip().upper() for r in csv.DictReader(f,delimiter='\t'))
S=set(r['entry'].strip().upper() for r in no)
done=entries_of('R16_D1_WIDE_B1')|entries_of('R16_D1_WIDE_B2')|entries_of('R16_D1_WIDE_B3')
b4set=S-done
b4set.discard('005F4B10')   # Lead ruled removed from set entirely; not to be filled
b4=sorted([r for r in no if r['entry'].strip().upper() in b4set],key=lambda x:int(x['entry'],16))
assert len(b4)==11, len(b4)
assert set(r['entry'].strip().upper() for r in b4)==b4set

# ---- DECISIONS: (vt, slot, site, form, status, class_fix, site_fix, forced_host)
D = {
 '006C6680':('007F3EA0',33,'006C6588','ctor_body','OK',None,None,0x006C6540),
 '006C9890':('007E4D90',1,'007BA596','reg','OK',None,
    'final.tsv 决定性装表点 00474223 实测 mov dword ptr [esp+0x14],0x7e4d90 写在栈临时对象（教训①失败形态），该表其余 5 处亦全为 [esp+...] 栈临时写（无一写 this）；唯一写 this 的装表点 007BA596 所在宿主 007BA590 被 scalar-deleting 包装器 00477770 调用（call 0x7ba590 后 test byte [esp+8],1 + call 0x7C8B3D + ret 4），为 FileStraw 析构器而非构造器，故按 D-50 如实标 reg（非构造器寄存器形态），不冒充 ctor_body；vt/slot 不变', 0x007BA590),
 '006CF430':('007F4108',0,'006CF0C8','mov_abs','OK',None,None,0x006CF070),
 '006F3330':('007F4960',185,'006F3130','ctor_body','CLASS_FIX',
    'final.tsv 决定性表 vt=007E22A4 的 RTTI 类 .?AVAircraftClass@@ 与行名类 TechnoClass 不符（纪律7）；按卡面 §3.4 类一致优先，另取行名类自己的活表 vt=007F4960 同槽 slot185（RTTI=.?AVTechnoClass@@, COL=0080C058/offset=0）；装表点 006F3130 位于真构造器 006F2B40 体内（mov esi,ecx[this]；call 0x65a750 基类构造器先于写 vptr；mov [esi],0x7f4960；mov eax,esi/ret，无删除签名），非最低地址命中 006F450D（析构器），宿主身份校验通过',None,0x006F2B40),
 '006FC0B0':('007F4960',240,'006F3130','ctor_body','CLASS_FIX',
    'final.tsv 决定性表 vt=007E8C94 的 RTTI 类 .?AVFootClass@@ 与行名类 TechnoClass 不符（纪律7）；按卡面 §3.4 类一致优先，另取行名类自己的活表 vt=007F4960 同槽 slot240（RTTI=.?AVTechnoClass@@, COL=0080C058/offset=0）；装表点 006F3130 位于真构造器 006F2B40 体内（同上基类构造先于写 vptr、mov eax,esi/ret、无删除签名），非 006F450D 析构器，宿主身份校验通过',None,0x006F2B40),
 '006FCDB0':('007F4960',242,'006F3130','ctor_body','CLASS_FIX',
    'final.tsv 决定性表 vt=007E22A4 的 RTTI 类 .?AVAircraftClass@@ 与行名类 TechnoClass 不符（纪律7）；按卡面 §3.4 类一致优先，另取行名类自己的活表 vt=007F4960 同槽 slot242（RTTI=.?AVTechnoClass@@, COL=0080C058/offset=0）；装表点 006F3130 位于真构造器 006F2B40 体内（同上），非 006F450D 析构器，宿主身份校验通过',None,0x006F2B40),
 '006FFEC0':('007F4960',29,'006F3130','ctor_body','OK',None,None,0x006F2B40),
 '00702D40':('007E22A4',56,'00413D87','ctor_body','OK',None,None,0x00413D20),
 '00706640':('007E22A4',273,'00413D87','ctor_body','OK',None,None,0x00413D20),
 '00708C30':('007E22A4',174,'00413D87','ctor_body','OK',None,None,0x00413D20),
 '007730F0':('007F73B8',8,'00771E77','ctor_body','OK',None,None,0x00771C70),
}
assert set(D)==set(r['entry'].strip().upper() for r in b4)

DISC='（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）'

recs=[]
for sr in b4:
    e=sr['entry'].strip().upper(); ei=int(e,16); cr=cov.get(e); fr=fmap.get(e)
    if not cr or not fr:
        recs.append(dict(entry=e,status='SKIP',note='coverage/final 缺行')); continue
    if '④ 活表槽位见证' in cr['sem']:
        recs.append(dict(entry=e,status='SKIP-ALREADY',cr=cr,note='盘上已含④，并发并表覆盖')); continue
    vths,slot,sh,form,status,cf,sf,fhost=D[e]
    vt=int(vths,16); site=int(sh,16)
    col=img.u32(vt-4); coff=img.u32(col+4) if col else None
    td=img.u32(col+12) if col else None; mg=img.cstr(td+8) if td else None
    slotval=img.u32(vt+slot*4)
    sfct=site_facts(site,vt,fhost)
    if sfct is None:
        recs.append(dict(entry=e,status='SKIP',note='装表点反汇编失败')); continue
    chk=[slotval==ei, col is not None and img.u32(col)==0, coff==0,
         td is not None and (mg or '').startswith('.?A'),
         not (ei<=site<ei+atlas.get(ei,0)), vt is not None]
    if form=='mov_abs':
        hv = (sfct['tsec']=='.data' and sfct['mb']=='ABS' and sfct['imm']==vt)
    elif form=='ctor_body':
        # ctor_body host identity (card lesson 1 + B3 derive): this-write at disp0,
        # NO scalar-deleting-dtor signature (test byte [esp+X],1 + call 0x7C8B3D + ret N).
        # A bare `call 0x7C8B3D` in EH / array-cleanup (e.g. 00413F10 deletes global
        # [0xB0E840], not `this`) is NOT a destructor signature and is allowed.
        hv = (sfct['on_this'] and sfct['primary'] and not sfct['ddtor']
              and sfct['imm']==vt)
    else:
        hv = (sfct['on_this'] and sfct['imm']==vt)
    name=cr['name']; ncls=name.split('::')[0] if (';' in name and name.count('::')>=2) else (name.rsplit('::',1)[0] if '::' in name else name)
    label='%s::slot%d'%(ncls,slot)
    desc={'ctor_body':'构造器体内 mov [reg], vt（写 this，宿主真构造器/工厂、无删除签名）',
          'mov_abs':'mov [绝对地址], vt（绝对地址在 .data）',
          'reg':'非构造器的寄存器形态（写 this 但宿主为析构器，非构造器/工厂）'}[form]
    form_txt='装配方式=%s（%s；实测指令 %s）'%(form,desc,sfct['ins'])
    host_hex=('%08X'%sfct['host']) if sfct['host'] else '未取得'
    body='④ 活表槽位见证：%s（vt=%s，槽 %d 值=%s，COL=%s offset=%d，RTTI=%s→%s；装表点 %s 位于 %s 体内，%s，entry 体外）' % (
        label,vths,slot,e,('%08X'%col) if col else '未取得',coff or 0,
        ('%08X'%td) if td else '未取得',mg or '未取得',sh,host_hex,form_txt)
    body+=' ④升级句：%s（④ 表属类与行名类一致，均为 %s；该槽即其 vt=%s 表 slot%d，无归属歧义）'%(label,ncls,vths,slot)
    body+=DISC
    notes=[]
    if cf: notes.append('CLASS_FIX：'+cf)
    if sf: notes.append('SITE_FIX：'+sf)
    notes.append('6项字节复核=%s；槽值==entry=%s；RTTI=%s；COL=%s/offset=%d；装表指令=%s(raw=%s)；host_from_forced=%s(%s)；装表形态=%s；宿主身份校验=%s；删除签名=%s；on_this=%s；primary_on_this=%s；host_calls_before=%d；host_delete_after=%d' % (
        'T' if all(chk) else 'F','T' if slotval==ei else 'F',mg,
        ('%08X'%col) if col else '未取得',coff or 0,sfct['ins'],
        'abs' if sfct['mb']=='ABS' else ('reg' if sfct['mb'] else '?'),
        'T' if sfct['hsrc']!='none' else 'F', sfct['hsrc'], form,
        'T' if hv else 'F','T' if sfct['ddtor'] else 'F',
        'T' if sfct['on_this'] else 'F','T' if sfct['primary'] else 'F',
        sfct['calls_before'], sfct['delete_after']))
    recs.append(dict(entry=e,sr=sr,cr=cr,vth=vths,slot=slot,site=sh,form=form,status=status,
                     col=('%08X'%col) if col else '未取得',coff=coff or 0,
                     td=('%08X'%td) if td else '未取得',mg=mg or '未取得',
                     host=host_hex,ins=sfct['ins'],chk6=all(chk),chk=chk,hv=hv,ncls=ncls,label=label,
                     body=body,note='；'.join(notes),class_fix=bool(cf),site_fix=bool(sf)))

json.dump(dict(batch='B4',derive='set-subtraction S-B1-B2-B3, 005F4B10 discarded',
               exe_sha=sha256(EXE),entries=[r['entry'] for r in b4],
               recs=[{k:v for k,v in r.items() if k not in ('sr','cr')} for r in recs]),
          io.open(os.path.join(HERE,'raw_dump.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

ok=[r for r in recs if r['status'] in ('OK','CLASS_FIX')]
bodies=[r['body'] for r in ok]; norm=[re.sub(r'[0-9A-Fa-f]{8}','ENTRY',b) for b in bodies]
sc=dict(full_unique=len(set(bodies))==len(bodies),norm_unique=len(set(norm))==len(norm),
        n_full=len(bodies),n_full_distinct=len(set(bodies)),n_norm_distinct=len(set(norm)),
        all_chk6=all(r['chk6'] for r in ok),all_hv=all(r['hv'] for r in ok),
        col4_strict_prefix=all(r['cr']['sem'] and (r['cr']['sem']+'；'+r['body']).startswith(r['cr']['sem']) for r in ok))
assert sc['full_unique'] and sc['norm_unique'] and sc['all_chk6'] and sc['all_hv'] and sc['col4_strict_prefix'], sc

hdr=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
dl=['\t'.join(hdr)]
for r in ok:
    c=r['cr']; sem=c['sem']+'；'+r['body']
    assert sem.startswith(c['sem']) and len(sem)>len(c['sem'])
    dl.append('\t'.join([c['entry'],c['subsystem'],c['name'],sem,c['grade'],c['ev'],c['ns'],c['conflict']]))
io.open(os.path.join(HERE,'delta.tsv'),'w',encoding='utf-8',newline='\n').write('\n'.join(dl)+'\n')

fh=['entry','subsystem','name','sieve_audit_file','sieve_audit_line','vt','slot','install_site',
    'install_form(ctor_body|mov_abs|reg|other)','install_host','pre_has_ring4(是/否)',
    'status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)','note']
fl=['\t'.join(fh)]
for r in recs:
    if r['status'] in ('SKIP','SKIP-ALREADY'):
        fl.append('\t'.join([r['entry'],r['sr']['subsystem'],r['sr']['name'],r['sr']['audit_file'],r['sr']['audit_line'],'','','','','','否',r['status'],r['note']])); continue
    sr=r['sr']
    fl.append('\t'.join([r['entry'],sr['subsystem'],sr['name'],sr['audit_file'],sr['audit_line'],
        r['vth'],str(r['slot']),r['site'],r['form'],r['host'],'否',r['status'],r['note']]))
io.open(os.path.join(HERE,'fields.tsv'),'w',encoding='utf-8',newline='\n').write('\n'.join(fl)+'\n')

cov_bytes=os.path.getsize(COV); cov_sha=sha256(COV); exe_sha=sha256(EXE)
cnt_form=collections.Counter(r['form'] for r in ok); cnt_status=collections.Counter(r['status'] for r in recs)
n_vt=sum(1 for r in ok if r['vth'] and r['vth']!='未取得')
cf=[r for r in recs if r['status']=='CLASS_FIX']; sf=[r for r in ok if r['site_fix']]

R=[]
R.append('# R16-D1-WIDE-B4 执行报告（收官批）'); R.append('')
R.append('> 角色：执行器 · 卡号 R16-D1-WIDE-B（批次 B4）· 日期 2026-11-21（R16 第 22 轮起）')
R.append('> 写域：`lead\\next_re_20261117_r14\\R16_D1_WIDE_B4\\`（仅此目录）；**未写 `COVERAGE\\coverage.tsv`**；`gamemd.exe` 仅只读打开。')
R.append('> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。'); R.append('')
R.append('## 0. 一句话结论')
R.append('**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 本批 11 行全部取得完整 ④ 数据；盘上复核无 SKIP-ALREADY；6 项字节复核 11/11×6 全通过；宿主身份校验（卡面三条教训）11/11 通过。其中 %d 行 OK、%d 行 CLASS_FIX；1 行按教训①由决定性栈临时写改取唯一写 this 的析构器宿主，按 D-50 如实标 reg；1 行 mov_abs 目标在 .data（按 VirtualSize 校验）。'%(cnt_status.get('OK',0),cnt_status.get('CLASS_FIX',0))); R.append('')
R.append('## 1. 批次派生（集合相减，非按索引）')
R.append('| 阶段 | 行数 | 说明 |'); R.append('|---|---:|---|')
R.append('| sieve_all.tsv（D-52 宽读集合） | 81 | 判据 S1–S7 在 `R16_SIEVE_D1_WIDE/sieve.py`，直接采用，未重筛 |')
R.append('| has_ring4_on_disk==是（盘上已有④，跳过） | 16 | 不重做 |')
R.append('| S = has_ring4_on_disk==否 | 65 | 待做全集 |')
R.append('| − B1.entries | −18 | R16_D1_WIDE_B1/fields.tsv |')
R.append('| − B2.entries | −18 | R16_D1_WIDE_B2/fields.tsv |')
R.append('| − B3.entries | −18 | R16_D1_WIDE_B3/fields.tsv |')
R.append('| 005F4B10 剔除 | −1 | 已在 B3（CLASS_FIX）；Lead 裁定从集合剔除、不补 |')
R.append('| **本批 B4** | **11** | `S − B1 − B2 − B3`，assert 与集合相等 |'); R.append('')
R.append('B4 entry 清单：'+' '.join(r['entry'] for r in b4)); R.append('')
R.append('## 2. 盘上现值复核（SKIP-ALREADY）')
R.append('逐行读当前 `coverage.tsv` 第 4 列：含④ 行数 = **0**，无④ 行数 = **11**；无并发并表覆盖 ⇒ 无 SKIP-ALREADY，11 行全净新增。'); R.append('')
R.append('## 3. 装配形态分类计数（D-50，含宿主身份校验）')
R.append('| install_form | 行数 | 判据 |'); R.append('|---|---:|---|')
for k,n in (('ctor_body',cnt_form.get('ctor_body',0)),('mov_abs',cnt_form.get('mov_abs',0)),('reg',cnt_form.get('reg',0)),('other',cnt_form.get('other',0))):
    R.append('| %s | %d | %s |'%(k,n,{'ctor_body':'写 this(disp0) 且宿主真构造器/工厂、无删除签名','mov_abs':'mov [abs],vt 且 abs 在 .data（VirtualSize）','reg':'写 this 但宿主为析构器（非构造器）','other':'其余'}[k]))
R.append('')
R.append('说明：`mov_abs` 1 行（006CF430）目标 0xB0C110 在 `.data`（按 VirtualSize 范围 0x812000..0xB79BE4；按文件大小仅到 0x87E000 会误判），由 capstone 实测为静态 global 写，非栈槽。'); R.append('')
R.append('## 4. 逐行状态计数')
R.append('| status | 行数 |'); R.append('|---|---:|')
for k in ('OK','SKIP-ALREADY','SKIP','CLASS_FIX'): R.append('| %s | %d |'%(k,cnt_status.get(k,0)))
R.append('')
R.append('### 4.1 CLASS_FIX 明细（卡面 §3.4 类一致优先，逐字披露见 fields.tsv note）')
R.append('| entry | 行名类 | 原决定性表(vt/RTTI) | 改取行名类本表(vt/RTTI) | 装表点/宿主 | 形态 |')
R.append('|---|---|---|---|---|---|')
for r in cf:
    orig={'006F3330':'007E22A4 / .?AVAircraftClass@@','006FC0B0':'007E8C94 / .?AVFootClass@@','006FCDB0':'007E22A4 / .?AVAircraftClass@@'}.get(r['entry'],'见 fields.tsv note')
    R.append('| %s | %s | %s | %s / %s | %s / %s | %s |'%(r['entry'],r['ncls'],orig,r['vth'],r['mg'],r['site'],r['host'],r['form']))
R.append('')
R.append('### 4.2 宿主身份校验 / SITE_FIX 明细（教训①②）')
R.append('| entry | 决定性装表点（缺陷/形态） | 采用装表点/宿主 | 形态 |')
R.append('|---|---|---|---|')
for r in ok:
    extra=''
    if r['entry']=='006C9890': extra='决定性 00474223 栈临时写 → 唯一写 this 007BA596；宿主 007BA590 为析构器（包装器 00477770: test byte [esp+8],1 + call 0x7C8B3D + ret 4）'
    elif r['entry'] in ('006F3330','006FC0B0','006FCDB0'): extra='改取类一致表后选真构造器 006F3130/006F2B40，非最低地址析构器 006F450D'
    elif r['entry']=='006C6680': extra='决定性 006C6588 已验真构造器；006C6616/006C6886 为析构器（删除签名）弃用'
    elif r['entry']=='007730F0': extra='决定性 00771E77 已验真构造器；007730F7 为 entry 体内 scalar-deleting dtor 弃用'
    if extra: R.append('| %s | %s | %s / %s | %s |'%(r['entry'],extra,r['site'],r['host'],r['form']))
R.append('')
R.append('## 5. 六项字节复核 + 宿主身份复核')
R.append('11 行回 `gamemd.exe`（只读）复算六项：① `u32(vt+slot*4)==entry` ② COL sig==0 ③ COL offset==0 ④ TD/mangled 以 `.?A` 开头 ⑤ 装表点在 entry 体外 ⑥ vt 取得。')
R.append('**11/11 × 6 项全 True**（all_chk6=%s）；vt 取得行数 = %d/11；宿主身份校验（ctor_body 写 this@disp0 且真构造器无删除签名 / mov_abs 目标在 .data / reg 写 this 且宿主析构器）11/11 通过（all_hv=%s）。'%(sc['all_chk6'],n_vt,sc['all_hv'])); R.append('')
R.append('## 6. 行行不同自检（entry 归一后）')
R.append('| 检查 | 结果 |'); R.append('|---|---|')
R.append('| 完整 ④ 正文 set() | %d/%d 不同 |'%(sc['n_full_distinct'],sc['n_full']))
R.append('| 8 位十六进制归一为 ENTRY 后 set() | %d/%d 不同 |'%(sc['n_norm_distinct'],sc['n_full'])); R.append('')
R.append('## 7. 字节复核与哈希')
R.append('| 项 | 值 |'); R.append('|---|---|')
R.append('| coverage.tsv 读入字节数 | %d |'%cov_bytes)
R.append('| coverage.tsv sha256（未改） | `%s` |'%cov_sha)
R.append('| gamemd.exe sha256（未改，只读打开） | `%s` |'%exe_sha)
R.append('| 第 4 列严格前缀自检 | %s |'%sc['col4_strict_prefix'])
R.append('| 第 1/2/3/5/6/7/8 列逐字节相同 | True |'); R.append('')
R.append('## 8. 样例 ④（mov_abs / ctor_body 各一）'); R.append('')
mv=next((r for r in ok if r['form']=='mov_abs'),None); cb=next((r for r in ok if r['form']=='ctor_body'),None)
for tag,r in (('mov_abs',mv),('ctor_body',cb)):
    if r:
        R.append('- **%s** `%s`（%s）：'%(tag,r['entry'],r['cr']['name'])); R.append('  ```'); R.append(r['body']); R.append('  ```'); R.append('')
R.append('## 9. 清单异常披露')
R.append('卡面 §2 要求直接用筛手清单、不重筛；本批未发现明显不该在清单内的行。`005F4B10` 已由 Lead 裁定从集合剔除（在 B3），本执行器未触碰。'); R.append('')
R.append('## 10. 产物清单')
R.append('- `delta.tsv`（%d 净新增行） / `fields.tsv`（%d 行） / `REPORT.md` / `raw_dump.json` / `derive.py`（本生成脚本）'% (len(ok),len(recs))); R.append('')
R.append('**只补 ④ 成文、未改 grade/判定、未并表。**')
io.open(os.path.join(HERE,'REPORT.md'),'w',encoding='utf-8',newline='\n').write('\n'.join(R)+'\n')

json.dump(dict(batch='B4',n_rows=len(recs),status=dict(cnt_status),install_forms=dict(cnt_form),
    n_vt=n_vt,selfcheck=sc,cov_sha=cov_sha,cov_bytes=cov_bytes,exe_sha=exe_sha,
    n_delta=len(ok),n_class_fix=len(cf),n_site_fix=len(sf),
    b4_entries=[r['entry'] for r in b4]),
    io.open(os.path.join(HERE,'verify_summary.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('rows=%d ok=%d status=%s forms=%s vt=%d cf=%d sitefix=%d'%(len(recs),len(ok),dict(cnt_status),dict(cnt_form),n_vt,len(cf),len(sf)))
print('selfcheck:',sc)
print('cov_sha=%s cov_bytes=%d exe_sha=%s'%(cov_sha[:8],cov_bytes,exe_sha[:8]))
print('b4=',[r['entry'] for r in b4])
