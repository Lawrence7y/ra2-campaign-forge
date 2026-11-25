# -*- coding: utf-8 -*-
"""R127: 追加看板第 127 轮段（看板当前 107 行，未到 260 行阈值，不归档）。

纪律：wx 独占备份 -> 断言旧 sha256 与旧 CR -> 断言新文本零反引号 -> 单次写入 ->
回读校验（sha、CR、行数 <= 300、新段标记存在）。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
BRD = os.path.join(R14, 'STATUS_BOARD.md')

EXPECT_SHA = '18a9ea180c36695b'
EXPECT_CR = 0
# 看板有 107 个 LF 且以换行结尾，故 split('\n') 得 108 项（末项为空串）。
EXPECT_LINES = 108

TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

SEC_BOARD = '''
## 🟢 R17 第 127 轮（2026-11-25 03:0x–04:0x）· IPersist / IPersistStream 由 OleSaveToStream 的参数角色定名完毕；0x7e36c0 = IApplication、0x7e9b20 = ISwizzle

### 一 · 起点：R126 台账 GK 的前两条未取得项

R126 留下的悬案有两条：① 0x7f7c70 与 0x7f7c80 谁是 IPersist、谁是 IPersistStream 不由字节给出；② 0x7e36c0 与 0x7e9b20 的 QI 体不被任何类的 slot0 引用，只能给出「查了哪些 IID」，给不出接口名。

本轮两条都取得，另外撤回 R124 起一处错误表述：0x7e36c0 与 0x7e9b20 根本不是 QI 体，它们是 .rdata 里各 16 字节的 IID 常量。

### 二 · 定名走的是实参契约，不是共现频率

R125 已经把 0x7f7c70 从排除法升级为正向证据（「更窄那个多一个 slot 3」），但两个名字仍分不开。本轮换判据：看 QI 结果被当作哪个实参。

导入表实测 ole32!OleSaveToStream 恰 1 槽 0x7e15f4、ole32!OleLoadFromStream 恰 1 槽 0x7e15f8，名字与 DLL 都取自本映像导入表字节。OleSaveToStream 第 2 实参的契约是 IPersistStream。

0x820270（0109 的 .data 拷贝）作为 riid 的 8 个 QI 站点，从 push 之后**正向反汇编到 ret 为止**（换掉了 40 字节窗口，避免窗口太短漏计）全部命中 call [0x7e15f4]，8/8：0x4af856 到 0x4af8a5、0x4b6313 到 0x4b6364、0x4db76a 到 0x4db7be、0x50469e 到 0x5046c9、0x54b83c 到 0x54b88b、0x69ef66 到 0x69efb5、0x719d96 到 0x719de5、0x75c756 到 0x75c7a5。

0x7f7c80 的 60 处 push 中，35 处在 40 字节内紧接 ff 15 f4 15 7e 00。反向：0x818858 与 0x7f7c70 的 16 个站点，正向扫到 ret 为止没有一处命中。所以 0109 对 = IPersistStream。

010C 那侧靠方法数上限：16 个站点上 QI 结果只在 +0xc 出现（0x42cab5 的 ff 50 0c），三个 GetClassID 站点 0x4d5892、0x73e7b7、0x742815 都是 call [reg+0xc] 带 4 字节出参，紧接着 mov edi,<类自己的 CLSID> 与 repe cmpsd，三个 CLSID 互不相同（92612C46-F71F-11D1-AC9F-006008055BB5、4A582747-9839-11D1-B709-00A024DDAFD1、4A582743-9839-11D1-B709-00A024DDAFD1）。与 IPersist 只有一个 GetClassID 相符、与 IPersistStream 的 4 方法不符。

两对必须在 L1 的两个候选里二选一，且方向单向可失败，故是唯一解。

**上限如实写**：字节仍读不出 IPersist 这三个字的拼写，方向靠外部 GUID 约定（109 = IPersistStream、10C = IPersist）补上。

### 三 · 撤回一处错表述

0x7e36c0 = {96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}，0x7e9b20 = {5FF0CA70-8B12-11D1-B708-00A024DDAFD1}，两者都在 .rdata、各 16 字节，是 IID 常量。R124 到 R126 把它们称作「QI 体」是错的，本轮撤回。

它们的接受点（体内把 riid 与它做 repe cmpsd 的 QI 体）实测三处：0x429360 在 vtable 0x7e36d4 的 slot0（.?AVApplicationClass@@）、0x429270 在 vtable 0x7ea564 的 slot3（.?AVTiberianSunClassFactory@@）、0x6cf430 在 vtable 0x7f4108 的 slot0（.?AVSwizzleManagerClass@@）。

### 四 · 补一个我自己先前的结构性盲点

r127b 走「vtable 槽 -> 函数入口 -> 体内比较」这条路，盲点是「入口没被任何 vtable 槽直接指向的 QI 体看不见」，而我在 r127b/r127c 里都没测这一点。r127d 专门补：不看 vtable 的两条路 —— 全映像 bf / 68 两种锚点枚举（0x7e36c0 的 bf 在 0x4292ab 与 0x42937f、68 在 0x429409 / 0x429489 / 0x4f6936；0x7e9b20 的 bf 在 0x6cf44e、68 在 0x429555，全在 .text），以及全 .rdata 里 u32 == 三个入口的位置逐个判槽。

三个入口各恰 1 处宿主，与 r127b 完全一致；三个入口被当作 bf/68 立即数引用的次数**全为 0**，即除 vtable 槽外没有第二条引用路径，宿主集合就是完整集合。反控：0x429580 与 0x6cf400 给 0 命中、0x429210 给 1 命中（.?AVTiberianSunClassFactory@@ 的 slot0）、0x40f000 给 1 命中但解不出类名。

### 五 · 定名

0x7e36c0 = .?AUIApplication@@：两个宿主的 mdisp 0 非 IUnknown 接口名交集唯一。TiberianSunClassFactory 那处是 IClassFactory::CreateInstance 的形状（ret 0x10 = 4 实参，把 0x89a29c 处的对象拿来做 riid 比对，而 0x429200 处把该对象写成了 0x7e36d4 = ApplicationClass 的 mdisp0 虚表）。

0x7e9b20 = .?AUISwizzle@@：SwizzleManagerClass 的 RTTI 恰 3 条基类（.?AVSwizzleManagerClass@@ / .?AUISwizzle@@ / .?AUIUnknown@@），mdisp 全 0、ncb 2/1/0，非 IUnknown 的接口名唯一。

两个 QI 体（0x429360、0x6cf430）都同时显式比较 0x7f7c90（IID_IUnknown），所以它们对应的 IID 不是 IUnknown。

0x429360 的 QI 体还有第三分支接受 0x7ea6e8 = {96F02EC7-6FE8-11D1-B6FD-00A024DDAFD1}，出参写成 .data 单例 0x87f7e8 而不是 this。**本轮不给它定名**：接受值不是本对象，mdisp 判据对它无效。

### 六 · 本轮自己的判据错误（S-167 到 S-176）

这一节比结论更值得记。

S-167：自审卡把 repe cmpsd 写成 F3 A5（那是 repe movsd），实际字节 F3 A7。S-168：接受点判据用固定 300 字节窗口，跨过函数边界，把 0x429210 与 0x6cf410 也算成接受点。S-169：改用「向前找 0xC2/0xC3 后接连续填充」求函数入口，但 0xC2/0xC3 会以立即数字节形式出现（0x429210 之前就有 c7 05 9c a2 89 00 d4 36 7e 00 c3）。S-170：改用 disasm_lite 指令对齐求入口 —— .text 里嵌着数据（.byte 伪指令 65 处），线性反汇编在数据上错位。三次都失败后放弃自算函数边界，改为纯字节枚举 + 与 r127b 站点集合做双向差集。

S-171：r127d 第一版把段基址存成 RVA 而非 VA，锚点整体少 0x400000。S-172：r127e 的 E4 第一版把「窗口内所有 call [reg+off]」都算进来，把 0x742899 的 call [edx+0x1c8]（ebp 另一个对象的虚调用）当成 QI 结果的虚槽调用。S-176 是同一个错在 E7 上的复现。

S-173 是最重的一条：**我派给审计员的卡写错了**。卡 R127-AUDIT-IPERSIST.md 第 5 条让审计员「复算 0x7ea564 与 0x7e36d4 两个 vtable 的 +0xc 槽值是否等于 0x429270 与 0x429360」。实测 0x7e36d4 的 slot0 = 0x429360、slot3(+0xc) = 0x429420。r127b 的产物写 slot_index 0 与 3，它对；卡面是我写错的。审计员若照卡面核 +0xc 会得到 0x429420 并对不上 —— 这不是它的错。

S-174：E6 第一版取 bcd+16 当 ncb，那是 vdisp（全 0）；MSVC x86 BC 布局是 +0 sig / +4 numContainedBases / +8 mdisp / +12 pdisp / +16 vdisp，ncb 在 +4。

S-175：E4 第二版的简单寄存器跟踪在 16 个站点追到 0 处。真实代码先把 ppv 槽值经 setl/dec/and 合成再解引用（0x42ca82 mov edx,[esp+0x4c] -> 0x42ca8c and ebx,edx -> 0x42caad mov eax,[ebx] -> 0x42cab5 call [eax+0xc]）。故 E4 不构成对 r127a「槽只到 +0xc」的独立复核，如实记方法无解。

### 七 · 跨家族（规则 D，两次派发）

第一次派 deepseek（task 256）：status failed，error = error_max_turns，61 回合 / 15.17 分钟，派发预算 5.0 分钟 —— **OVERTIME**，如实记。result 为空，未落任何报告，所以那一次的外部复核输入为零，不能写「已审计」。

第二次派 hy4（task 257）：succeeded，39 回合 / 3.15 分钟，预算 4.0 分钟，无 OVERTIME。报告 273 行 / 11111 字节、零反引号，收进 _r127/audit/r127_audit_hy4.md。四条主张全判 PASS，未发现推翻性证据。

复算由 r127h（14 项）按审计卡口径逐条重算：IAT 两个槽、四组 IID 字节与 GUID 文本、0x820270 的 8 个站点与 8 对命中地址、0x818858 的 16 个站点与 0 命中、三个 vtable 槽值、0x7f4108 的 COL 五个字段与三条基类四列、三处宿主槽位、两个 IID 的 5 处与 2 处出现位置。全部与它逐个相同，无一条分歧。

一条要如实说：我第一次读到的是它**中途**落盘的 7215 字节版本，那一版第 6 条报 ValueError、三处宿主全判 unknown，我据此写了「裁决分歧」两条。随后回收最终版（273 行），它自己已改对，结论与我一致 —— 「分歧」这个前提是我读早了造成的，不虚构分歧（S-178）。

它给的一条证据我原来漏了，采纳并复算：存在两个「固定参数包装器」直接 call QI 体。0x4f6930 是 push ecx / lea eax,[esp] / push eax / push 0x7e36c0 / push 0x89a29c / call 0x429360 / ret 4；0x429550 是 mov eax,[esp+8] / push eax / push 0x7e9b20 / push 0xb0c110 / call 0x6cf430 / ret 8。IID 与对象都写死、只留出参，比 vtable 槽更直接。反控：同一判据对 0x429480（IClassFactory::CreateInstance 的包装器）给否。

### 八 · 收口

r127a 15 + r127b 9 + r127c 9 + r127d 5 + r127e 8 + r127h 14 = 60 项断言全 PASS。全程 disasm_lite 流式扫描与单点窗口 disasm，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0，GATE_VER 仍 R126（本轮不改门禁）。看板 107 行未到 260 行阈值，本轮不归档。

### 九 · 未取得（不粉饰）

① IPersist 的拼写仍靠外部 GUID 约定，字节只给出「更窄那个多一个 slot 3」。② 0x7ea6e8 未定名（接受值不是 this，mdisp 判据无效）。③ 0x429270 是转交型（把 pUnkOuter 交给内层对象的 QI、不写自己的 ppv），如实分两类记，不当失败。④ 010C 站点的 ppv 槽值经 setl/dec/and 合成后解引用，简单寄存器跟踪追不到，「槽只到 +0xc」仍只由 r127a 的符号执行承担。⑤ 若 QI 结果被存进堆结构体后再取用，本轮所有判据都看不见。⑥ 35 个静态容器运行期元素值与计数。⑦ 共用模板展开的充分证明。⑧ 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    assert '`' not in SEC_BOARD, 'SEC_BOARD 含反引号'
    old = io.open(BRD, 'rb').read()
    dst = os.path.join(BK, 'r127_STATUS_BOARD.%s.bak' % TS)
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    assert sha16(old) == EXPECT_SHA, '旧 sha %s != %s' % (sha16(old), EXPECT_SHA)
    assert old.count(b'\r') == EXPECT_CR, '旧 CR %d != %d' % (old.count(b'\r'), EXPECT_CR)
    n_before = len(old.decode('utf-8').split('\n'))
    assert n_before == EXPECT_LINES, '旧行数 %d != %d' % (n_before, EXPECT_LINES)

    new = old.decode('utf-8').rstrip('\n') + '\n' + SEC_BOARD
    nb = new.encode('utf-8')
    n_after = len(new.split('\n'))
    assert n_after <= 300, '追加后 %d 行超过 300' % n_after
    with io.open(BRD, 'wb') as f:
        f.write(nb)
    rb = io.open(BRD, 'rb').read()
    assert rb == nb, '回读不一致'
    assert rb.count(b'\r') == 0, '新 CR %d != 0' % rb.count(b'\r')
    assert 'R17 第 127 轮' in rb.decode('utf-8'), '回读未见第 127 轮段'
    print('  WROTE BOARD  sha %s -> %s  CR=%d  lines %d -> %d  bytes %d -> %d'
          % (sha16(old), sha16(rb), rb.count(b'\r'), n_before, n_after,
             len(old), len(rb)))


if __name__ == '__main__':
    main()
