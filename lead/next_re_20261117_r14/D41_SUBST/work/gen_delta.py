# -*- coding: utf-8 -*-
"""Generate coverage_delta.tsv (8 columns, same as usual) from final_verdict.json."""
import os, sys, json
WORK=os.path.dirname(__file__)
ROOT=os.path.dirname(WORK)
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"

cov={}
for line in open(COV,encoding="utf-8",errors="replace"):
    f=line.rstrip("\n").split("\t")
    if len(f)>=5 and f[0]!="entry": cov[f[0].upper()]=(f[1],f[2],f[3],f[4])

verdict=json.load(open(os.path.join(WORK,"final_verdict.json"),encoding="utf-8"))

SEM={
"007C9442":"MSVC CRT 小堆分配核心 _nh_malloc(size,flag)：② 走身份替代（调用者契约）——被 CRT::malloc@0x7C9430[已证]（push [0xB782C4] 句柄 flag）与 CRT::_new@0x7C8E17[已证]（push 1 flag）两具名已证函数以特定参数直调，参数字节可核；③b④ 完整分配重试环（+0x00 cmp [esp+4],-0x20/ja 边界 → +0x07 alloc → +0x15 cmp 目标 → +0x1b realloc → +0x27 jne 回边）；④ 2 个 E8 边界直调站点 0x7C8E1D/0x7C943A（非自环）。4 字节 VA 全镜像出现 0 次，无虚表。",
"00406130":"AudioController 音频索引一致性校验（无虚表普通成员）：② 走身份替代（YRpp 绑定 + 字节双吻合）——YRpp/Audio.h:144 JMP_THIS(0x406130) 原文行给符号绑定；体内实测 [ecx+0xC]==0x87E294（AudioIndex==&AudioIDXData::Instance，Audio.h:53/116/123）、[ecx+8]=Voice（Audio.h:115）、[ecx+4]=f_4、[ecx]=f_0 共 4 项逐项吻合 YRpp 类声明；③b② 可证伪返回约定（+0x02 test [0x87E2A0]→ret0、+0x09 cmp [ecx+C],0x87E294→ret0、双比较后 +0x30 清 f_0）；④ 12 个 E8 直调站点（含 006F9ED0 等 3 个已证调用者）。4 字节 VA 全镜像 0 次。",
"00406170":"AudioController 取当前 Voice（无虚表普通成员）：② 走身份替代（YRpp 绑定 + 字节双吻合）——YRpp/Audio.h:147 JMP_THIS(0x406170) 原文行；体内 [ecx+0xC]==0x87E294（AudioIndex==&Instance，Audio.h:53/116/123）与 [ecx+8]=Voice（Audio.h:115）两项吻合 YRpp 声明；③b② 可证伪返回约定（+0x02 全局未就绪 ret0、+0x09 索引不符 ret0、+0x12 否则返回 Voice）；④ 2 个 E8 直调站点 0x750D60/0x750EFE（非自环）。4 字节 VA 全镜像 0 次。",
"0065CA80":"RawFileClass 构造器（无虚表全局静态对象/成员 ctor）：② 走身份替代（YRpp 绑定 + 字节双吻合）——YRpp/CCFileClass.h:100 JMP_THIS(0x65CA80) 原文行（RawFileClass(const char* pFileName)）；体内 +0x28 mov [this],0x7F0904 写真实 vfptr、+0x2e ret 4 单栈参 pFileName、+0x07..+0x26 十项字段写（CCFileClass.h:110-114 FileAccess/FilePointer/FileSize/Handle/FileName）≥2 项吻合；③b③ 内存形状断言（vt + 字段 + 对象尺寸），name 更正未执行保留 sub_；④ 47 个 E8 直调站点（含 AudioStream::PlayWAV 等 4 已证调用者）。4 字节 VA 全镜像 0 次。",
"00428B80":"按名查音频/动画条目并构造（无虚表自由函数）：② 走身份替代（调用者契约）——被 9 个已证函数（BulletTypeClass::LoadFromINI@0x46BEE0 等）以 lea ecx=局部缓冲/具体 this 直调，参数字节可核；③b④ 完整数组遍历环（+0x33 count[0x8B4160] → +0x43 read [0x8B4154]+esi*4 → +0x47 strcmp@0x7C8D20 → +0x51 inc esi/cmp/jl 边界），失败路径 +0x35 push 0x378 call 0x7C8E17；④ 74 个 E8 直调站点（非自环）。4 字节 VA 全镜像 0 次。",
"00405190":"音频样本对象池取用/复位（无虚表自由函数）：② 走身份替代（调用者契约）——被 VocClass::PlayGlobal@0x750920 与 VocClass::PlayAt@0x7509E0 两已证函数以 ecx=this 直调，参数字节可核；③b④ 完整链表遍历 I/O（+0x36 沿 [0x87E180] 链、+0x2B cmp edi,0x87E180/jne 哨兵边界、+0x3E 判标志→call 0x407450→写 +0x138、+0x41 call 0x7C8B3D free、推进）；④ 4 个 E8 直调站点（0x7509A3/0x750A75/0x750DA6 等，非自环）。4 字节 VA 全镜像 0 次。",
"004052F0":"音频对象数组清空/释放（无虚表自由函数）：② 走身份替代（调用者契约）——被 VocClass::PlayGlobal@0x750920 与 VocClass::PlayAt@0x7509E0 两已证函数以 ecx=this 直调，参数字节可核；③b④ 完整数组环（+0x43 count[esi+0xA8] → +0x4F read [edi]→call 0x401F90→写 0→inc ebx→cmp/jl 边界 → +0x60 收尾写标志）；④ 5 个 E8 直调站点（0x750973/0x750A31 等，非自环）。4 字节 VA 全镜像 0 次。",
"00401F90":"引用计数减一并钳位非负（无虚表自由函数）：② 走身份替代（调用者契约）——被 AudioController::~AudioController@0x405C00 与 DTOR_1@0x405D40 两已证函数以 ecx=[0x8B4154 列表解引] 直调，参数字节可核；③b② 可证伪约定（+0x02 dec [ecx+0xC]、+0x09 jge 保真、+0x0b 钳位 [ecx+0xC]=0 永不为负）；④ 12 个 E8 直调站点（非自环）。4 字节 VA 全镜像 0 次。",
"00405BE0":"AudioController 重置（清零 + AudioIndex=&Instance）：② 走身份替代（调用者契约）——被 14 个已证函数（AnimClass::AnimClass@0x421EA0 等，lea ecx=[esi+0x1A0] 具体子对象）直调，参数字节可核；③b③ 内存形状（+0x02 [ecx+0xC]=0x87E294=AudioIDXData::Instance，+0x09/+0x0c/+0x0e 清 f_0/f_4/Voice 共 4 字段，吻合 Audio.h:119-125 类声明）；④ 47 个 E8 直调站点（非自环）；按 §8.6 条1 清零+置默认仅算 P，故本行③b③靠 4 字段形状闭合而非机械清零。4 字节 VA 全镜像 0 次。",
}
BIND={"00406130":"YRpp/Audio.h:144 JMP_THIS","00406170":"YRpp/Audio.h:147 JMP_THIS","0065CA80":"YRpp/CCFileClass.h:100 JMP_THIS"}

rows=[]
for v in verdict:
    e=v["entry"]
    sub,name,sem0,grade=cov[e][0],cov[e][1],cov[e][2],cov[e][3]
    nk="symbolic" if not name.startswith("sub_") else "placeholder"
    ev="EVIDENCE/per_row_verdict.tsv#%s;EVIDENCE/final_sites.txt;EVIDENCE/scan_main.json" % e
    if v["channel"]==1: ev+=";"+BIND[e]
    rows.append([e,sub,name,SEM[e],"[已证]",ev,nk,"%s→[已证]"%grade])

hdr=["entry","subsystem","name","one_line_semantics","grade","evidence_path","name_kind","旧grade→新grade"]
with open(os.path.join(ROOT,"coverage_delta.tsv"),"w",encoding="utf-8") as f:
    f.write("\t".join(hdr)+"\n")
    for r in rows: f.write("\t".join(r)+"\n")
print("wrote coverage_delta.tsv with",len(rows),"data rows")
for r in rows: print(" ",r[0],r[1],r[2])
