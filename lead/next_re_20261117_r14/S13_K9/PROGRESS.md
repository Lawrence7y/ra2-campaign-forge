# S13-K9 PROGRESS · 11 行 exact 绑定裁定（最终）

**结论：exact 绑定确实存在。a-S13-K6 的 11 行成立，S13_K7 的 exact11_entries_with_hit=0 是脚本判据错（漏「mov ecx,<global 地址>」与「vptr 先于 mov ecx 载入」两种写法）。** 双通道一致；exe SHA256 复算 73201CC0…F67476，全程只读。

## 14 入口四环表（①槽值即函数 ②COL+0xC→TD+8 ③exact+vptr写 ④体内合同）

| entry | slot | ①入口 | ②RTTI类 | ③exact(call站点数) | ④语义合同 | 标记 |
|---|---|---|---|---|---|---|
| 0040B880 | 2 | ✅vt 0x7E17CC+8 | DynVec&lt;BombClass*&gt; | ✅ 2 (0x43864A,0x438F37) | SetCapacity(int,int) ret8 | [已证] |
| 0040B930 | 4 | ✅vt 0x7E17CC+10 | DynVec&lt;BombClass*&gt; | ✅ 2 (0x4386AB,0x43942B) | FindItemIndex(T*) ret4 | [已证] |
| 0040F7C0 | 2 | ✅vt 0x7E1E84+8 | DynVec&lt;WarheadTypeClass*&gt; | ✅ 1 (0x75D11C) | SetCapacity(int,int) ret8 | [已证] |
| 0040FD90 | 2 | ✅vt 0x7E1ED4+8 | DynVec&lt;WeaponTypeClass*&gt; | ✅ 1 (0x771ECA) | SetCapacity(int,int) ret8 | [已证] |
| 0040FE40 | 4 | ✅vt 0x7E1ED4+10 | DynVec&lt;WeaponTypeClass*&gt; | ✅ 2 (0x771F99,0x773139) | FindItemIndex(T*) ret4 | [已证] |
| 0046B7E0 | 2 | ✅vt 0x7E4678+8 | DynVec&lt;BulletClass*&gt; | ✅ 2 (0x46649B,0x46B2B7) | SetCapacity(int,int) ret8 | [已证] |
| 0046B890 | 4 | ✅vt 0x7E4678+10 | DynVec&lt;BulletClass*&gt; | ✅ 2 (0x46661B,0x46862A) | FindItemIndex(T*) ret4 | [已证] |
| 0062B250 | 2 | ✅vt 0x7EF824+8 | DynVec&lt;ParasiteClass*&gt; | ✅ 2 (0x62927E,0x629360) | SetCapacity(int,int) ret8 | [已证] |
| 0062B300 | 4 | ✅vt 0x7EF824+10 | DynVec&lt;ParasiteClass*&gt; | ✅ 2 (0x629482,0x62B012) | FindItemIndex(T*) ret4 | [已证] |
| 0065C0D0 | 2 | ✅vt 0x7F07A4+8 | DynVec&lt;RadSiteClass*&gt; | ✅ 1 (0x65B277) | SetCapacity(int,int) ret8 | [已证] |
| 0065C180 | 4 | ✅vt 0x7F07A4+10 | DynVec&lt;RadSiteClass*&gt; | ✅ 1 (0x65B358) | FindItemIndex(T*) ret4 | [已证] |
| 0048AD60 | 6 | ✅vt 0x7E5170+18 | DynVec&lt;DamageGroup*&gt; | ❌ 0 exact | GetItem(int) ret4 | [未证]③ |
| 0054E8E0 | 6 | ✅vt 0x7ECE7C+18 | DynVec&lt;KamikazeControl*&gt; | ❌ 0 exact | GetItem(int) ret4 | [未证]③ |
| 0048AD70 | 1 | ✅vt 0x7E5170+4 | DynVec&lt;DamageGroup*&gt; | ❌ 0 exact | operator== ret4 | [未证]③ |

## 核心数字（审计复算）

1. exact 命中：按 call 站点 **18**（Channel B 原始字节），按入口 **11/14**（11 行全覆盖，3 漏扫 0）。
2. 随机 11 入口基线误命中 **0/11**（seed=1337，非族 16B 对齐 .text 地址，同一判据）=> 有判别力。
3. 四环齐全 **11 行**（即 a-S13-K6 的 11 行）；3 漏扫行 ③ 不成立。
4. 与 a-S13-K6 的 11 行逐行一致 **11/11**，不一致 0。

## 判据 / 复算脚本（全在 work/，互不依赖）

- 通道A `work/channelA3.py`：capstone skipdata 指令边界真 call，558 exact/179 global；容器族站点见 EVIDENCE/VERDICT_EVIDENCE.md。
- 通道B `work/channelB.py`：纯 PE 字节正则（C7 05 建 G→vt，8B15/A1+近邻 B9+FF5x，vt[disp]∈14集），18 站点；EVIDENCE/channelB_raw_byte.json。
- RTTI `work/rtti_vtbase.py`：vt-4=COL→COL+0xC=TD→TD+8 名串，6 类全读出；WARN 早期用槽地址当 vt 得假阴性已纠正。
- 基线/漏扫 `work/baseline_miss.py`；vtable 图 `work/vtmap.py`；合同 `work/rtti_miss_contract.py`。
- 关键字节：0x43856D `C7 05 68 C6 89 00 CC 17 7E 00`（mov [0x89C668],0x7E17CC 活 vtable）；0x438645 B9 68C68900 + 0x43863B 8B1568C68900 + 0x43864A FF5208 → slot2=0x40B880。
- K7 错因：脚本把 `mov ecx,imm32`（B9，地址=this）当 `mov ecx,[global]`(8B0D)，且 vptr 载入常在 mov ecx 之前，故全漏。