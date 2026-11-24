# -*- coding: utf-8 -*-
"""写 delta.tsv / base_rate.tsv（TAB 分隔，UTF-8 无 BOM）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DES = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S15_B1/EVIDENCE"

ROWS = [
 ("006E3E30", "TActionClass::slot6",
  "TActionClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 ("006E57A0", "TagClass::slot6",
  "TagClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 ("006E6470", "TagTypeClass::slot6",
  "TagTypeClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 ("0071F930", "TEventClass::slot6",
  "TEventClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 ("0071FA80", "TEventClass::slot8",
  "TEventClass 删除析构器（slot8，含 test byte[esp+0xc],1 → call 0x7C8B3D 释放路）：装 4 张 vt 并调基类析构 007258D0 后，对 3 个全局容器做「虚表 +0x10 的 Find → 摘除并前移压缩」；Find 未命中返 -1（004E056F or eax,-1）即跳过，命中则 dec Count 并 [ecx+eax*4-4]=edx 压缩 ⇒ -1 下标哨兵被本行 cmp/je 消费（③b②）。"),
 ("00726860", "TriggerClass::slot5",
  "TriggerClass 流读入并就地构造（slot5）：先经 00410380 读包装读基类部分，空流返回 E_POINTER 0x80004003，本行 test eax,eax + jl 负码跳收尾原样返回；成功则构造基类、装 4 张 vt、逐字段读入，末尾返回 S_OK ⇒ 多值错误码被分支消费（③b②）。"),
 ("007268D0", "TriggerClass::slot6",
  "TriggerClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
 ("00726950", "TriggerClass::slot8",
  "TriggerClass 删除析构器（slot8，含 test byte[esp+0xc],1 → call 0x7C8B3D 释放路）：装 4 张 vt 并调基类析构 007258D0 后，对 3 个全局容器（0xa8eae8 / 0xb0f670 / 0xb0f708）做 Find → 摘除压缩；Find 未命中返 -1（004EA66F 等 or eax,-1）即跳过，命中则 dec Count 并前移压缩 ⇒ -1 下标哨兵被本行 cmp/je 消费（③b②）。"),
 ("00727BF0", "TriggerTypeClass::slot5",
  "TriggerTypeClass 流读入并就地构造（slot5）：先经 00410380 读包装读基类部分，空流返回 E_POINTER 0x80004003，本行 test eax,eax + jl 负码跳收尾原样返回；成功则构造基类、装 4 张 vt、逐字段读入，末尾返回 S_OK ⇒ 多值错误码被分支消费（③b②）。"),
 ("00727C80", "TriggerTypeClass::slot6",
  "TriggerTypeClass 流写出（Save）：三参转交 00410320 写包装，包装对空流入参返回 E_POINTER 0x80004003；本行 test eax,eax + jl 让负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）。"),
]

def w(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

d = ["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
for e, n, s in ROWS:
    assert "\t" not in s and "\t" not in n
    d.append("%s\tS15\t%s\t%s\t[已证]\t%s/ROW_%s.txt" % (e, n, s, DES, e))
w(os.path.join(OUT, "delta.tsv"), d)

b = ["batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate",
     "S15_B1\t10\t10\t10\t10\t10\t1.0000"]
w(os.path.join(OUT, "base_rate.tsv"), b)
print("delta rows =", len(d) - 1)
print(open(os.path.join(OUT, "base_rate.tsv"), encoding="utf-8").read())
