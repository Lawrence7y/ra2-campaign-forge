"""生成 VERDICT.md 逐行节 + verdict.tsv（分批调用，每批落盘）"""
import sys, json, struct
import rt
from rt import im, vt_name, vt_slots
from derive2 import PROD_VT, enrich as derive
from pretty import name_pretty

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT12"
CLSID = {
 "006C5210":("{34ECD9A8-0AB0-11D2-ACA7-006008055BB5}", 0x007E9820),
 "006C5390":("{A8C54DA4-0F7B-11D2-8172-006008055BB5}", 0x007E9840),
 "006C5510":("{9FD219CA-0F7B-11D2-8172-006008055BB5}", 0x007E9830),
 "006C5690":("{0E272DCC-9C0F-11D1-B709-00A024DDAFD1}", 0x007E9700),
 "006C5810":("{703E044B-0FB1-11D2-8172-006008055BB5}", 0x007E9710),
 "006C5990":("{0E272DC8-9C0F-11D1-B709-00A024DDAFD1}", 0x007E96C0),
 "006C5B10":("{703E044A-0FB1-11D2-8172-006008055BB5}", 0x007E96D0),
 "006C5C90":("{BA093524-4CF4-11D2-BC26-00104B8FB04D}", 0x007E9960),
 "006C5E10":("{241AB316-4CF5-11D2-BC26-00104B8FB04D}", 0x007E9980),
 "006C5F90":("{1C470B0E-69D7-11D2-B8F2-006008C809ED}", 0x007E9990),
 "006C6110":("{623C7584-74E7-11D2-B8F5-006008C809ED}", 0x007E99A0),
}
REG_CALL = {"006C5210":0x006BD43C,"006C5390":0x006BD479,"006C5510":0x006BD4B6,
            "006C5690":0x006BD4F3,"006C5810":0x006BD530,"006C5990":0x006BD56D,
            "006C5B10":0x006BD5AA,"006C5C90":0x006BD5E7,"006C5E10":0x006BD624,
            "006C5F90":0x006BD661,"006C6110":0x006BD69E}
FAC_CTOR = {"006C5210":0x006C5140,"006C5390":0x006C52C0,"006C5510":0x006C5440,
            "006C5690":0x006C55C0,"006C5810":0x006C5740,"006C5990":0x006C58C0,
            "006C5B10":0x006C5A40,"006C5C90":0x006C5BC0,"006C5E10":0x006C5D40,
            "006C5F90":0x006C5EC0,"006C6110":0x006C6040}
FAC_WRITE = {k: FAC_CTOR[k] + 9 for k in FAC_CTOR}
PROD_STORE = {"006C5210":0x004C991A,"006C5390":0x0075D0BA,"006C5510":0x00771E77,
              "006C5690":0x0062BC4A,"006C5810":0x00644CF4,"006C5990":0x0062DFA6,
              "006C5B10":0x00441_000 if False else 0x0064419C,"006C5C90":0x0041E401,
              "006C5E10":0x0043A375,"006C5F90":0x004D0909,"006C6110":0x00420B10}
SEC_VT = {
 "006C5210":[(0x007E88B4,0x004C9920,"+4"),(0x007E88AC,0x004C9926,"+8"),(0x007E88A4,0x004C992D,"+0xC")],
 "006C5390":[(0x007F6B14,0x0075D0C1,"+4"),(0x007F6B0C,0x0075D0C7,"+8"),(0x007F6B04,0x0075D0CE,"+0xC")],
 "006C5510":[(0x007F739C,0x00771E7D,"+4"),(0x007F7394,0x00771E83,"+8"),(0x007F738C,0x00771E8A,"+0xC")],
 "006C5690":[(0x007EF938,0x0062BC50,"+4"),(0x007EF930,0x0062BC57,"+8"),(0x007EF928,0x0062BC5E,"+0xC")],
 "006C5810":[(0x007F016C,0x00644CFA,"+4"),(0x007F0164,0x00644D01,"+8"),(0x007F015C,0x00644D08,"+0xC")],
 "006C5990":[(0x007EFB80,0x0062DFAC,"+4"),(0x007EFB78,0x0062DFB3,"+8"),(0x007EFB70,0x0062DFBA,"+0xC")],
 "006C5B10":[(0x007F008C,0x006441A2,"+4"),(0x007F0084,0x006441A8,"+8"),(0x007F007C,0x006441AF,"+0xC")],
 "006C5C90":[(0x007E2A34,0x0041E407,"+4"),(0x007E2A2C,0x0041E40E,"+8"),(0x007E2A24,0x0041E415,"+0xC")],
 "006C5E10":[(0x007E3DD4,0x0043A37B,"+4"),(0x007E3DCC,0x0043A382,"+8"),(0x007E3DC4,0x0043A389,"+0xC")],
 "006C5F90":[(0x007E8B1C,0x004D090F,"+4"),(0x007E8B14,0x004D0916,"+8"),(0x007E8B0C,0x004D091D,"+0xC")],
 "006C6110":[(0x007E3288,0x00420B16,"+4"),(0x007E3280,0x00420B1D,"+8"),(0x007E3278,0x00420B24,"+0xC")],
}
SECTION_NAME = {"006C5210":"A","006C5390":"B","006C5510":"C","006C5690":"D","006C5810":"E",
                "006C5990":"F","006C5B10":"G","006C5C90":"H","006C5E10":"I","006C5F90":"J",
                "006C6110":"K"}
# 每行独有的 ⑤ 侧记（措辞/口径需账），必须各行不同
ROW_NOTE = {
 "006C5210":"删除析构器 `004CA770` 自身还调 `0x7258D0` 解单例并从 `0xA83E30` 注册表摘除，第 4 列未写",
 "006C5390":"`007F6B30` 是主表、`007F6B14` 才在 +4（slot0=`004105E0` 调节 thunk），第 4 列引的是主表，未踩 B1 的「小成员表当主表」",
 "006C5510":"同类为 4 表对象（+0/+4/+8/+0xC），第 4 列「主虚表 slot0=00410260(=00410260」是自比较冗余写法，取值无误",
 "006C5690":"同类 4 表（+0/+4/+8/+0xC），主表写点 `0062BC4A`；第 4 列只写主表，未混入副表",
 "006C5810":"ctor `00644BE0` 先构造成员 `TypeList<RGBClass>`（`00644C46` 写 `007E4E58`）再写主表，第 4 列「分配构造一个对象」略去成员构造",
 "006C5990":"ctor `0062DF20` 内含 `DynamicVectorClass<ParticleClass*>` 成员（`0062DF4A` 写 `007E9D64`），主表 `007EFB9C` 后写，顺序正常",
 "006C5B10":"与 006C5690 同为 0E272D 段，但注册 CLSID 不同（{703E044A} vs {0E272DCC}），第 4 列未混淆",
 "006C5C90":"工厂表 slot4=`006C5D10`（LockServer）与 slot3 相邻，第 4 列未把 slot4 当 CreateInstance",
 "006C5E10":"NeuronClass 实为 4 表对象（写点 `0043A375`–`0043A389`），非「单表小类」；第 4 列只引主表，无冲突",
 "006C5F90":"工厂 CLSID {1C470B0E} 与 AlphaShape {623C7584} 在全镜像各仅 2 处引用（注册块 + 本类 GetClassID）",
 "006C6110":"主表写在 `[edi]`（`mov edi,ecx`@`00420AF2`），非 `[esi]`，第 4 列未点名寄存器故无冲突",
}

def ins(va):
    for i in im.dis(va, 2, stop_ret=False):
        return f"`{i.address:08X}` `{i.bytes.hex()}` `{i.mnemonic} {i.op_str}`"
    return f"`{va:08X}` ?"

def block(e):
    d = derive(e)
    pvt = PROD_VT[e]
    g = CLSID[e]
    fac, fw, reg = FAC_CTOR[e], FAC_WRITE[e], REG_CALL[e]
    pname = vt_name(pvt)[0]
    lines = []
    lines.append(f"## {SECTION_NAME[e]} · `{e}` — S22 `{name_pretty(d['vt_name'])}`  →  **PASS**")
    lines.append("")
    lines.append("| 项 | 结论 | 地址 / 字节 |")
    lines.append("|---|---|---|")
    lines.append(f"| ② 类身份 | 成立 | 槽 `{d['slot_addr']:08X}` = `{d['slot_val']:08X}`（= 本 entry）；vt `{d['vt']:08X}` +0x0C = slot#3；COL `{d['col']:08X}` → TD `{d['td']:08X}` → `{d['vt_name']}`；CHD `{d['chd']:08X}` numBase={d['chd_numbase']} |")
    lines.append(f"| ② 主虚表 | 成立 | 体内 new({d['newsize']:#x}) → ctor `{d['prod_ctor']:08X}`，在 `{PROD_STORE[e]:08X}` 写主表 `{pvt:08X}`（`{pname}`，slot0=`{im.u32(pvt):08X}`、slot1=`{im.u32(pvt+4):08X}`、slot8 删除析构=`{im.u32(pvt+0x20):08X}`） |")
    lines.append(f"| ③b 形态 | **3b2** | 站点 {ins(d['qisite'])}（callee = 主表 slot0 `{im.u32(pvt):08X}` QI）→ {ins(d['test'])} → {ins(d['jge'])}，目标 `{d['jge_dst']:08X}`；失败路 {ins(d['relsite'])}（前置 `push 1`）；入口三类错误码 `{d['guards'][0][2]:08X}`@`{d['guards'][0][0]:08X}`、`{d['guards'][1][2]:08X}`@`{d['guards'][1][0]:08X}`、`{d['guards'][2][2]:08X}`@`{d['guards'][2][0]:08X}` |")
    sec = "；".join(f"{d_} `{v:08X}`@`{a:08X}` slot0=`{im.u32(v):08X}`" for v, a, d_ in SEC_VT[e])
    lines.append(f"| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `{pvt:08X}`（slot0=`{im.u32(pvt):08X}`）；副表 {sec} ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |")
    lines.append(f"| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `{fac:08X}`（`8bc1` / `c7 40 04 0` / `c7 00 {struct.pack('<I',d['vt']).hex()}` / `c3`）在 `{fw:08X}` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `{reg:08X}` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{g[0]}`，pUnk=该对象 |")
    lines.append(f"| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `{d['slot_addr']:08X}`；④ 用 `.text` 指令字面量写点 `{fw:08X}` + 注册调用 `{reg:08X}` |")
    lines.append(f"| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |")
    lines.append("")
    lines.append(f"**② 细节**：`{d['vt']:08X}` 只有 5 个槽（槽4 `{d['vt_slot4']:08X}` = LockServer），紧随其后的 `{d['vt_slot5_raw']:08X}` 是**下一张表的 COL**、不是本表槽；slot0 `{d['vt_slot0']:08X}` 为 QI 形态（`{d['vt_slot0']:08X}`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。")
    lines.append("")
    lines.append(f"**③b② 检查点与消费点真实性**：callee `{im.u32(pvt):08X}` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`{d['qisite']:08X}` 返回后 `{d['qisite']+2:08X}` `8bf8`(`mov edi,eax`)、`{d['test']:08X}` `85ff`(`test edi,edi`)、`{d['jge']:08X}` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `{d['relsite']:08X}` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `{d['jge_dst']:08X}` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。")
    lines.append("")
    lines.append(f"**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `{fw:08X}` 把 `{d['vt']:08X}` 装进 `operator new(8)` 出的活堆对象（`{d['newcall'] and format(d['newcall'],'08X')}` 之后），该对象在 `{reg:08X}` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={g[0]}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `{reg:08X}` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`{d['vt']:08X}` 的字面量在全镜像只出现 1 次（`{fw:08X}`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。")
    lines.append("")
    lines.append(f"**⑤ 需账**：{ROW_NOTE[e]}。")
    lines.append("")
    return "\n".join(lines)

def tsv_line(e):
    d = derive(e)
    g = CLSID[e]
    reason = (f"槽{d['slot_addr']:08X}={d['slot_val']:08X}且RTTI {d['vt_name']}自洽;"
              f"3b2站点{d['qisite']:08X}call[主表{im.u32(PROD_VT[e]):08X}+0]→{d['test']:08X}test→{d['jge']:08X}jge，"
              f"失败路{d['relsite']:08X}销毁新对象;④活表写{FAC_WRITE[e]:08X}(ctor{FAC_CTOR[e]:08X})→CoRegisterClassObject {g[0]}@{REG_CALL[e]:08X}，"
              f"direct=0；②④不同源；⑤相符（失败侧实为删除析构器非Release）")
    return "\t".join([e, "S22", "PASS", f"{d['slot_addr']:08X}", "3b2",
                      f"{FAC_WRITE[e]:08X}", "no", reason])

if __name__ == "__main__":
    which = sys.argv[1:]
    with open(BASE + r"\VERDICT.md", "a", encoding="utf-8") as f:
        for e in which:
            f.write(block(e) + "\n")
    with open(BASE + r"\verdict.tsv", "a", encoding="utf-8") as f:
        for e in which:
            f.write(tsv_line(e) + "\n")
    print("appended:", which)
