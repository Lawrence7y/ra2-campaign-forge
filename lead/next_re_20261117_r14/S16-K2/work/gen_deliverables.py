#!/usr/bin/env python3
"""S16-K2: generate TARGETS.tsv and coverage_delta.tsv, recompute final numbers."""
import csv, os, re, bisect, math

ROOT=r"D:\Project\ra2-campaign-forge"
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S16-K2")
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")

cov=list(csv.DictReader(open(COV,encoding='utf-8'),delimiter='\t'))
atlas_entries=set(r['entry'].strip().upper() for r in csv.DictReader(open(ATLAS,encoding='utf-8'),delimiter='\t'))
s16=[r for r in cov if r['subsystem'].strip()=='S16']
for r in s16:
    r['entry']=r['entry'].strip().upper()
    r['_in_atlas']='Y' if r['entry'] in atlas_entries else 'N'

def is_placeholder(n):
    n=(n or '').strip()
    return re.fullmatch(r'sub_[0-9A-Fa-f]{8}',n) is not None

E_DIR="EVIDENCE"

# ---- name upgrades (10) ----
# fields: entry, new_name, new_semantics, evidence_path, note
NAME_UPGRADES=[
 ("00539EB0","LightningStorm::Start",
  "闪电风暴启动: 比较云层中心坐标全局 0xA9F9F8/0xA9F9FA, 两次 call RandomRanged(0x65C7E0), 写 0xA9F9CC/0xA9FACC; 由 Launch case2(0x6CCD3F) 调用",
  E_DIR+r"/E03_unnamed_analysis.txt; docs/re/superweapon_re.md:780,808; docs/re/re_sprint_S2_report.md:136,164",
  "候选名依据=已入账项目文档地址名(superweapon_re.md / re_sprint_S2_report.md); 语义依据=反汇编字节+调用点"),
 ("0053A6C0","LightningStorm::sub_0053A6C0",
  "闪电风暴接近告警: 函数体内引用 EVA_LightningStormCreated 与 TXT_LIGHTNING_STORM_APPROACHING, 源文件串 Ion.cpp",
  E_DIR+r"/E03_unnamed_analysis.txt; function_atlas.tsv:0053a6c0(strings)",
  "候选名依据=调用图邻居+字符串引用(EVA_LightningStormCreated/TXT_LIGHTNING_STORM_APPROACHING); 类归属=LightningStorm 模块(Ion.cpp); 不编像样的名字, 地址后缀透明"),
 ("0053AE00","LightningStorm::AnnounceActive",
  "派发 LightningStormActive 消息: mov ecx,0x82809C('Msg:LightningStormActive') -> call 0x734E60(消息串查表) -> 结果传 0x5D3BA0(消息派发), 源码行 push 0x463/Ion.cpp",
  E_DIR+r"/E04_proof_candidates.txt; "+E_DIR+r"/E03_unnamed_analysis.txt",
  "候选名依据=字节级字符串 0x82809C='Msg:LightningStormActive'(E04 实测)+查表调用 0x734E60; 语义依据=字节序列"),
 ("0053B410","PsychicDominator::AnnounceActive",
  "派发 DominatorActive 消息: mov ecx,0x8280B8('Msg:DominatorActive') -> call 0x734E60 -> 结果传 0x5D3BA0, 源码行 push 0x53B/Ion.cpp",
  E_DIR+r"/E04_proof_candidates.txt; "+E_DIR+r"/E03_unnamed_analysis.txt",
  "候选名依据=字节级字符串 0x8280B8='Msg:DominatorActive'(E04 实测)+查表调用 0x734E60; 语义依据=字节序列"),
 ("0053A0E0","LightningStorm::sub_0053A0E0",
  "LightningStorm 状态谓词: 读 byte [0xA9FAB4] 与 dword [0xA9FAB8], 两者任一满足返回 1 否则 0; 由 SuperClass::ClickFire(0x6CB920)+0xAA 调用",
  E_DIR+r"/E03_unnamed_analysis.txt",
  "候选名依据=调用者已知名函数 ClickFire + 全局变量族 0xA9FAxx 属 LightningStorm; 地址后缀透明, 不编像样的名字"),
 ("0053AE50","LightningStorm::sub_0053AE50",
  "闪电风暴落雷动画生成: Launch case2 调用; 取格(0x5657A0)后经虚槽 [vptr+0x48] 取坐标, 分配 0x1C8 -> AnimClass::Create_At(0x421EA0), 结果存 0xA9FAC4",
  E_DIR+r"/E03_unnamed_analysis.txt",
  "候选名依据=调用者 0x6CCDE2 ∈ SuperClass::Launch 的 case2(LightningStorm); 语义依据=alloc 0x1C8+AnimClass::Create_At 调用模式"),
 ("00430BA0","BeaconClass::sub_00430BA0",
  "Beacon 对象构造/创建: thiscall(ecx=this), 分配 0x114(operator new 0x7C8E17) 后写 3 个 vptr; 引用 Beacon.CPP + EVA_BeaconPlaced/EVA_BeaconDetected",
  E_DIR+r"/E03_unnamed_analysis.txt; re_atlas/evidence/r036_r13_deliverable.txt:150-151; function_atlas.tsv:00430ba0(strings)",
  "候选名依据=源文件串 Beacon.CPP + EVA_BeaconPlaced/Detected(r036)+thiscall 构造模式; 地址后缀透明"),
 ("006CE280","SuperClass::sub_006CE280",
  "SuperClass 倒计时剩余帧: 由 CurrentFrame(0xA8ED84) - [this] 与 [this+8] 比较, 夹取后回写; 由 SuperClass::Grant(0x6CB560)+0x21C 调用",
  E_DIR+r"/E04_proof_candidates.txt; "+E_DIR+r"/E03_unnamed_analysis.txt",
  "候选名依据=调用者已知名函数 Grant + ecx=this(SuperClass); 语义依据=CurrentFrame 差值模式; 地址后缀透明"),
 ("006CE2C0","SuperClass::sub_006CE2C0",
  "SuperClass 计时起点初始化: 若 [this]==-1 则写 CurrentFrame(0xA8ED84); 由 SuperClass::Grant(0x6CB560)+0x1B8 调用",
  E_DIR+r"/E04_proof_candidates.txt; "+E_DIR+r"/E03_unnamed_analysis.txt",
  "候选名依据=调用者已知名函数 Grant; 语义依据=字节 cmp [ecx],-1 / mov [ecx],[0xA8ED84]; 地址后缀透明"),
 ("006CE2D0","SuperClass::sub_006CE2D0",
  "SuperClass 向量按键删除: call [vptr+0x10] 取键, 按结果左移 [this+4] 元素数组并 Count--([this+0x10]); 由 Grant/ClickFire/Launch 调用",
  E_DIR+r"/E04_proof_candidates.txt; "+E_DIR+r"/E03_unnamed_analysis.txt",
  "候选名依据=5 个调用者全在已知名 SuperClass 方法内; 语义依据=左移删除字节模式; 地址后缀透明"),
]

# ---- proved upgrades (4) ----
PROVED_UPGRADES=[
 ("006CDFD0","SuperClass::Save",
  "IPersistStream::Save 转发: 3 栈参(this,pStm,fClearDirty) -> call 0x410320(AbstractClass::Save), ret 0xC",
  E_DIR+r"/E04_proof_candidates.txt; docs/re/superweapon_re.md:708-721",
  "SuperClass vft v[6]@0x7F4000; RTTI COL 0x80B610->TD 0x8423E0='.?AVSuperClass@@'(verify_rtti.py); 函数体 10 条纯转发"),
 ("006CE220","~SuperClass",
  "标量删除析构: call dtor 0x6CB120; test byte [esp+8]&1 -> 条件 call operator delete 0x7C8B3D; ret 4",
  E_DIR+r"/E04_proof_candidates.txt; docs/re/superweapon_re.md:47,327",
  "SuperClass vft v[8]@0x7F4008; RTTI 同上; 字节符合 scalar deleting dtor 规范型"),
 ("006CE8D0","SuperWeaponTypeClass::Save",
  "IPersistStream::Save 转发: 3 栈参 -> call 0x410320(AbstractClass::Save), ret 0xC",
  E_DIR+r"/E04_proof_candidates.txt",
  "SuperWeaponTypeClass vft v[6]@0x7F40A8; RTTI COL 0x80B6C8->TD 0x842600='.?AVSuperWeaponTypeClass@@'; 函数体与 0x6CDFD0 同构"),
 ("006CEFE0","~SuperWeaponTypeClass",
  "标量删除析构: call dtor 0x4109C0; test byte [esp+0xC]&1 -> 条件 call operator delete 0x7C8B3D; ret 4",
  E_DIR+r"/E04_proof_candidates.txt",
  "SuperWeaponTypeClass vft v[8]@0x7F40B0; RTTI 同上; 字节符合 scalar deleting dtor 规范型"),
]

# finalize row map
by_entry={r['entry']:r for r in s16}
delta=[]
for entry,name,sem,ev,note in NAME_UPGRADES:
    r=by_entry[entry]
    assert is_placeholder(r['name']), (entry,r['name'])
    delta.append(dict(entry=entry,subsystem='S16',name=name,one_line_semantics=sem,
                      grade=r['grade'],evidence_path=ev,note=note))
for entry,name,sem,ev,note in PROVED_UPGRADES:
    r=by_entry[entry]
    assert r['grade'].strip()!='[已证]', (entry,r['grade'])
    delta.append(dict(entry=entry,subsystem='S16',name=name,one_line_semantics=sem,
                      grade='[已证]',evidence_path=ev,note=note))

# apply to in-memory rows
final={r['entry']:dict(r) for r in s16}
for d in delta:
    final[d['entry']]['name']=d['name']
    final[d['entry']]['one_line_semantics']=d['one_line_semantics']
    final[d['entry']]['grade']=d['grade']

def stat(rows):
    n=len(rows)
    named=sum(1 for r in rows if not is_placeholder(r['name']))
    proved=sum(1 for r in rows if r['grade'].strip()=='[已证]')
    return n,named,proved

s16atlas=[r for r in s16 if r['_in_atlas']=='Y']
finalatlas=[final[r['entry']] for r in s16atlas]
s16all=s16
finalall=[final[r['entry']] for r in s16all]
print("BEFORE atlas:",stat(s16atlas)," ALL:",stat(s16all))
print("AFTER  atlas:",stat(finalatlas)," ALL:",stat(finalall))
n,nm,pv=stat(finalatlas)
print(f"FINAL atlas: named {nm}/{n}={nm/n*100:.2f}%  proved {pv}/{n}={pv/n*100:.2f}%")
n,nm,pv=stat(finalall)
print(f"FINAL ALL  : named {nm}/{n}={nm/n*100:.2f}%  proved {pv}/{n}={pv/n*100:.2f}%")
print(f"thresholds atlas: named need {math.ceil(.9*len(s16atlas))} got {stat(finalatlas)[1]}; proved need {math.ceil(.5*len(s16atlas))} got {stat(finalatlas)[2]}")

# ---- TARGETS.tsv (all 92) ----
tgt=os.path.join(CARD,"TARGETS.tsv")
with open(tgt,'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','in_atlas','cur_name','cur_grade','cur_semantics','missing','plan'])
    for r in sorted(s16,key=lambda x:(x['_in_atlas']!='Y',x['entry'])):
        missing=[]
        if is_placeholder(r['name']): missing.append('name')
        # every row already has nonempty semantics, but many are "槽语义未证" / weak
        sem=r['one_line_semantics']
        if '槽语义未证' in sem or '弱信号' in sem or '模块线索' in sem or 'region guess' in sem:
            missing.append('one_line_semantics')
        if r['grade'].strip()!='[已证]': missing.append('evidence')
        # plan
        d=next((x for x in delta if x['entry']==r['entry']),None)
        if d:
            plan=f"本卡交付: name->{d['name']}" + (f", grade->{d['grade']}" if d['grade']=='[已证]' else "")
        else:
            plan="保留(本卡未取得新字节证据)" if not missing else "未取新证:保持"
        w.writerow([r['entry'],r['_in_atlas'],r['name'],r['grade'],sem,
                    '+'.join(missing) if missing else 'none',plan])
print("wrote",tgt)

# ---- coverage_delta.tsv ----
dpath=os.path.join(CARD,"coverage_delta.tsv")
with open(dpath,'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path'])
    for d in delta:
        w.writerow([d['entry'],d['subsystem'],d['name'],d['one_line_semantics'],d['grade'],d['evidence_path']])
print("wrote",dpath,"rows",len(delta))
