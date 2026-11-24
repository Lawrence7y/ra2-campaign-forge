# D-19 独立事实核证底稿

日期：2026-11-05。核证员：事实核证员，magpie/codex/gpt-6.1-sol。

本次亲读 W3 Q3 全文（含189–254全文与紧邻声明）、Q1_C1全文、D-17裁决全文、W2三条红线原文、dirty_rect_l4相关正文与注释、Harness统计产出代码；独立读取原始PE字节并反汇编，读取指定三窗原始JSON并复算。未修改被核证文件。只写本底稿。没有启动游戏、读取活进程、实现采样器或执行动态性能测试。

路径说明：下文相对路径均以 `D:/Project/ra2-campaign-forge/` 为根。二进制均指 `ra2youli/gamemd.exe`，本次计算 SHA256=`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。原文行号为本次Read所见。

## 逐项结果

以下每项均保留要求的三个字段。supportsOption为支持的具体命题，不臆造D-19未提供的A/B选项含义。

```json
[
  {
    "supportsOption": "W3：确有两档设计；不能转述为只给1Hz",
    "detail": "亲读 lead/re_line_20261105/W3_COSTBOUND/sections/Q3_SAMPLE_PLAN.md:189-254 全文。:224原文为「【 基线档：1Hz 宏观归因流 】」「【 进阶档：~30Hz 帧沿事件流 】」。:225逐字为「- 采样时钟：1.0 秒定时触发」「- 采样时钟：由 CurrentFrame 递增驱动」；:226为「- 采集内容：4 个 VA + 视口坐标」「- 采集内容：4 个 VA + 当前帧微秒时间戳」。:231-234逐字为「1. **基线档（1Hz 宏观归因流 · 推荐默认）**：」「- 依附于现有的 1Hz `_rpm_counters` 架构（`harness8_v4.py:3979`）；」「- 每次采样仅需追加 4 次 32 位读，单次读取总带宽仅 16 字节；」「- 耗时 $< 2\\ \\mu\\text{s}$/秒，对目标进程零扰动；足以产出全量 87 窗的四大成本中心判定矩阵。」:235-238逐字为「2. **进阶档（帧推进边沿触发流 Frame-Edge Triggered · 可选增强）**：」「- 当外部 500Hz 探测器检测到逻辑帧号 `0x00A8ED84`（`CurrentFrame`）发生步进的瞬间，触发单次 16 字节连读快照；」「- 采样频次自适应于游戏真实帧率（慢窗 6Hz，快窗 31.25Hz）；」「- 该方案能够精准绘制『单帧毫秒数 vs 单帧寻路次数 vs 单帧索敌次数』的微观相平面散点图，实现微秒级回归分析。」结论：确有定时基线与帧沿触发增强；~30Hz不是慢窗也固定30Hz。这些是方案原文，耗时、零扰动、微秒级回归和充分性并未因此获得本次实测认证。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "W3：:145与:195不构成所指的直接自相矛盾；充分性仍须另证",
    "detail": "Q3_SAMPLE_PLAN.md:138-145的数学对象是外部帧时单一标量，:145逐字为「纯宏观时间序列在信息论上缺少至少 3 个维度的独立信息，因此在物理上永远无法定谳具体谁是主犯」。:149-151立即转入新增微观状态观测量，:195为「对于科学归因定谳，1Hz 采样已经完全充分」，:200-204明确以GenerationStamp与GreatestThreatCallCount累积计数为依据，:224-238列出新增VA流。因此前者限制纯宏观帧时，后者声称新增微观计数可充分，两者观测集合不同。不能仅因频率都是外部采样便判文字矛盾；也不能由不矛盾推出1Hz科学定谳已经成立。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D-17的谨慎边界：数百次/闲置≤10次缺少可复核阈值依据",
    "detail": "当前Q3_SAMPLE_PLAN.md:198是『全量22个慢窗』形态描述；用户所指的两个数字实际在:203，并先见于:17、:51-52。:275自述阈值『系基于 Q1 指令上界与物理动力学的严格推导，其实测数值分布需待获得 D-13 授权后在真机运行期实测核对』。因此作者将其标为推导，绝非已实测。亲读被引 Q1_C1_PATHFIND.md全文：:141-159给假设CPU/IPC与单次理论耗时、假想同帧60或300单位模型；:215明说无法验证每帧实际调用次数；没有推导『C1为主凶必≥300–1500次/秒』或『闲置必≤10次/秒』的公式、数据或独立出处。:148的2.80ms来自假设800指令/节点×10000节点的模型，不能作为Q3:52所称实测单次耗时。已执行阈值定向rg检查，结果见附录C。结论：作者自称推演，但这两个阈值的可复核定量依据为『无依据』（限已读Q3及其指定Q1来源；不声称穷尽全仓所有文档）。另外300/10=30，区间下沿也不支持:203『100倍以上』的统一说法。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "反驳W3：帧内冻结及83次读取严格零信息增益未成立",
    "detail": "已进入0x42A5B0完整读取到ret 0x42A68D：0x42A5FB=8b4128、0x42A5FE=40、0x42A5FF=894128，读取/自增/写回this+0x28；回绕时0x42A67F..0x42A685还会再次自增跳过0。直接rel32调用扫描命中0x42C90D、0x42CC80、0x42D17D。独立从0x42C900入口解码至0x42CCD0：入口0x42C90D调用重置；0x42CC02调用SearchCore；0x42CC72=47递增重试轮次；0x42CC80=e82bd9ffff再次调用重置；0x42CC91比较轮限，0x42CC9B=0f8404ffffff可回到0x42CBA5重试。它在搜索入口/同步重试层递增，非只在每帧边沿统一写一次。0x42D17D属于另一个0x42D170入口，也不是Q3:46声称全属于0x42C900。0x4CBC2C=b9b8e88700设置this单例，0x4CBC31=e8ca0cf6ff调用0x42C900，确认目标戳地址。0x55DE73..0x55DE81另显示CurrentFrame在帧尾自增写回；计数器有独立的业务写点。至少在同步寻路重试路径中可多次改变，不能保证一个帧号区间内始终不变。故Q3:209-211『所有计数器完全冻结』『82次数值完全不变』『信息熵增益严格为0』没有静态依据且其冻结前提已被反证。500×0.1668≈83.4的算术只说明轮询机会数。未采集活进程83快照，不声称实际83次必变，也不据此断言500Hz必要或最优。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "W3地址真实性部分成立；四项均不能按所列强判据直接换算成本",
    "detail": "四地址本次PE检查均映射.data，见附录A。①0x0087E8E0=0x0087E8B8+0x28，0x4CBC2C/31设置this并调用搜索，0x42A5FB..FF操作该偏移，工作区代际戳语义成立；不等同一搜一次、成功次数、实际展开量或耗时，见第4项重试与回绕。②0x00A8EC34：0x6F8DF3=8b1534eca800读取，0x6F8E04=42递增，0x6F8E09=891534eca800写回，确认0x6F8DF0入口调用累计代理。扫描.text中该4字节绝对地址仅命中操作数字段0x6F8DF5与0x6F8E0B；此检查不穷尽间接别名写、加载/进程重启，因此不背书跨生命周期无条件单调。③0x00B0CE88确实存在，是0x00B0CE78脏矩形向量当前条目数：0x6D1A60..0x6D1A9C初始化Items/容量/Count；0x6D2A94..0x6D2AB8取Count、递增回写、按20字节复制条目；0x6D2983..0x6D29BE删除/搬移，0x6DA980..0x6DA9BD也递减并搬移。与亲读docs/re/dirty_rect_l4.md:179-218的结构/合并去重注释相符，故『别处从没出现过』不属实，至少该文:19、:189、:513明确已有。它是瞬时队列长度，不是可见单位数、单位调用次数或耗时。Q3:100-102抄录有误：真实0x6D3DF0=a188ceb000；0x6D3DF5=756e是jne 0x6D3E65；test eax,eax实际在0x6D3DFF=85c0，随后的0x6D3E01=7566才jne 0x6D3E69。Render还检查其他标志和视口位移，因此少量/零队列不自动证明全部光栅化短路，更不证明<0.05ms。④0x00A8ED50确实是BulletClass对象向量Count：RTTI经0x7E46E0→0x7FC7B0→0x81AF70得到.?AVBulletClass@@，该虚表+0x5C槽0x7E4740=0x4666E0；0x466425=c706e4467e00装入同虚表；0x4664A2..0x4664B7把Count递增并向Items[旧Count]插对象；0x466623..0x46664E删除对象并递减/搬移；0x55B93F=a150eda800读取Count，0x55B94B=8b0d44eda800读取Items，再检查对象+0x98活跃标志后于0x55B960=ff525c调更新。因循环另有活跃标志门控，更精确名称是注册Bullet对象数，而非无条件等于本帧实际活跃更新数。该地址亦已有本次亲读Q1_C3C4_PHYS_TARGET.md:189-233记载。Count不会直接提供动画/伤害耗时或推出≤60就<0.1ms。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D-17：1Hz只是起点、不保证分解是原文明说，没有被转述加重",
    "detail": "亲读lead/re_line_20261105/D17D18_RULING/RULING_D17_D18.md §1。:44原文为『1 Hz只是待申请起点，不能保证捕获帧内峰值，更不能承诺解开全部三条红线。』:51原文为『需静态补字段与计数语义、用户分项授权和未来扰动验收；稀疏采样有混叠与跨帧聚合限制，可能只能增强区分能力，仍无法得到时间归因。当前无执行授权（F17-5、F17-6、F17-8）。』附带:185待粘贴块亦写『1Hz只是申请起点，不保证三类成本可分解』。所以该转述忠于原文，不是额外加重。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "双方有观测对象交集；D-17的不保证完整分解仍有事实依据",
    "detail": "亲读D-17:18、:44、:59及原始W2_FRAMETIME_ATTRIB.md:298-326，三条按名称是视口/可见对象、寻路、索敌（不同文档C编号不同）。W3的0x87E8E0对应寻路尝试/代际代理，0xA8EC34对应索敌入口调用代理，0xB0CE88对应渲染脏队列，确有三类交集；0xA8ED50是额外的物理对象数量。D-17:44、:59、:148所说索敌计数尚未定位是D-17当时文书状态，现可补充确认0xA8EC34入口自增，不能继续笼统说不存在有效候选计数地址。但交集不等于解开红线：代际戳有重试/失败与回绕口径；索敌计数不含每次扫描单元数/耗时；脏矩形可合并、删除，Count不等于真实视口坐标、可见单位数或绘制耗时；额外Bullet Count不直接分解上述三项。Q3:175-178直接假设y_i=alpha_i*T_i并据此宣布满秩，文件没有给经校准固定alpha_i或实际测得各成本时间。故不能由四个地址存在推得科学归因『完全解耦并绝对定谳』；D-17限制的是分解保证，不是宣称未来新增观测永远无效。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "既有数据：指定同趟三窗50.5→33.1→32.4ms属实（按一位小数）",
    "detail": "先亲读统计产出代码lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4730-4818及紧邻注释：stats.frame_ms_p50按CurrentFrame相邻首次观测沿差分、仅df==1入样求50%分位；df>1丢弃。随后执行附录B命令读取out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w{0,1,2}.json。实际stored依次50.47639999247622、33.11079999548383、32.422699994640425ms，故一位小数50.5、33.1、32.4成立。从frame_edges独立复算中位数50.47699999704491、33.11049999319948、32.422000003862195ms，入样数463、710、767，同样支持该一位小数结论。细小差异不能虚报为完全逐位一致；产出代码:5270-5282及:5326-5329显示stats用原精度计算，落盘沿时间round(t,6)，与亚微秒级中位数差相符。本次验证三窗值，不以此单独证明根因、同进程完整生命周期或全部87窗统计。",
    "provenance": "我亲验"
  }
]
```

## 关键原文字面补录

为避免JSON转义影响逐字核对，W3两档的关键读法按原文再录（Q3_SAMPLE_PLAN.md:231–238）：

> 1. **基线档（1Hz 宏观归因流 · 推荐默认）**：  
>    - 依附于现有的 1Hz `_rpm_counters` 架构（`harness8_v4.py:3979`）；  
>    - 每次采样仅需追加 4 次 32 位读，单次读取总带宽仅 16 字节；  
>    - 耗时 $< 2\ \mu\text{s}$/秒，对目标进程零扰动；足以产出全量 87 窗的四大成本中心判定矩阵。  
> 2. **进阶档（帧推进边沿触发流 Frame-Edge Triggered · 可选增强）**：  
>    - 当外部 500Hz 探测器检测到逻辑帧号 `0x00A8ED84`（`CurrentFrame`）发生步进的瞬间，触发单次 16 字节连读快照；  
>    - 采样频次自适应于游戏真实帧率（慢窗 6Hz，快窗 31.25Hz）；  
>    - 该方案能够精准绘制「单帧毫秒数 vs 单帧寻路次数 vs 单帧索敌次数」的微观相平面散点图，实现微秒级回归分析。

原文:225触发条件是「采样时钟：1.0 秒定时触发」和「采样时钟：由 CurrentFrame 递增驱动」。:226采集内容是「4 个 VA + 视口坐标」和「4 个 VA + 当前帧微秒时间戳」。这里的“逐字”指文字内容，引用缩进和行尾换行仅用于排版。四VA分散于不同位置，引用中的“16字节连读”不能被当成单次连续地址读取已可实现的证明。视口坐标是四VA之外的附加读。

## 附录A：本次原始PE核查

本次执行的地址映射、哈希、RTTI检查完整命令：

```bash
python -I -c 'import pefile,hashlib; p=pefile.PE("D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"); print("SHA256",hashlib.sha256(p.__data__).hexdigest())
for v in [0x87e8e0,0xa8ec34,0xb0ce88,0xa8ed50]:
 s=p.get_section_by_rva(v-0x400000); print(hex(v),s.Name.rstrip(b"\0").decode(),"mapped",s.Misc_VirtualSize>=v-0x400000-s.VirtualAddress+4)
def u(v): return int.from_bytes(p.get_data(v-0x400000,4),"little")
col=u(0x7e46e0); td=u(col+12); print("RTTI",hex(col),hex(td),p.get_data(td+8-0x400000,32).split(b"\0")[0]); print("UPDATE_SLOT",hex(u(0x7e4740)))'
```

完整输出，退出码0：

```text
SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
0x87e8e0 .data mapped True
0xa8ec34 .data mapped True
0xb0ce88 .data mapped True
0xa8ed50 .data mapped True
RTTI 0x7fc7b0 0x81af70 b'.?AVBulletClass@@'
UPDATE_SLOT 0x4666e0
```

本次进入重置函数、搜索函数及关键读取点的实际命令如下；该命令退出码0。下面只节录与结论直接有关的实际输出，其余指令不冒称不存在。

```bash
python -I -c 'import pefile,capstone,hashlib; p=pefile.PE("D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"); print("SHA256",hashlib.sha256(p.__data__).hexdigest()); m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for a,z in [(0x42a5b0,0x42a689),(0x42c900,0x42ccd0),(0x42d170,0x42d1b0),(0x6f8df0,0x6f8e20),(0x6d3d10,0x6d3e80),(0x55b8d0,0x55b9a0),(0x4666e0,0x466740)]:
 print("RANGE",hex(a),hex(z))
 for i in m.disasm(p.get_data(a-0x400000,z-a),a):
  if a in [0x42a5b0,0x42d170,0x6f8df0,0x55b8d0,0x4666e0] or i.mnemonic in ["call","ret"] or 0x42cc60<=i.address<0x42cca0 or 0x6d3de0<=i.address<0x6d3e80: print(hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str)
print("REL32_XREFS_42A5B0")
for s in p.sections:
 if s.Name.startswith(b".text"):
  d=s.get_data(); base=0x400000+s.VirtualAddress
  for j in range(len(d)-4):
   if d[j]==232 and base+j+5+int.from_bytes(d[j+1:j+5],"little",signed=True)==0x42a5b0: print(hex(base+j),d[j:j+5].hex())'
```

实际输出节录：

```text
0x42a5fb 8b4128 mov eax, dword ptr [ecx + 0x28]
0x42a5fe 40 inc eax
0x42a5ff 894128 mov dword ptr [ecx + 0x28], eax
0x42a602 0f8580000000 jne 0x42a688
0x42a67f 8b4128 mov eax, dword ptr [ecx + 0x28]
0x42a683 40 inc eax
0x42a685 894128 mov dword ptr [ecx + 0x28], eax
0x42c90d e89edcffff call 0x42a5b0
0x42cc02 e889ceffff call 0x429a90
0x42cc72 47 inc edi
0x42cc80 e82bd9ffff call 0x42a5b0
0x42cc91 3bf9 cmp edi, ecx
0x42cc9b 0f8404ffffff je 0x42cba5
0x42d17d e82ed4ffff call 0x42a5b0
0x6f8df3 8b1534eca800 mov edx, dword ptr [0xa8ec34]
0x6f8e04 42 inc edx
0x6f8e09 891534eca800 mov dword ptr [0xa8ec34], edx
0x6d3df0 a188ceb000 mov eax, dword ptr [0xb0ce88]
0x6d3df5 756e jne 0x6d3e65
0x6d3dff 85c0 test eax, eax
0x6d3e01 7566 jne 0x6d3e69
0x55b93f a150eda800 mov eax, dword ptr [0xa8ed50]
0x55b94b 8b0d44eda800 mov ecx, dword ptr [0xa8ed44]
0x55b951 8b0cb1 mov ecx, dword ptr [ecx + esi*4]
0x55b954 8a8198000000 mov al, byte ptr [ecx + 0x98]
0x55b95a 84c0 test al, al
0x55b95c 7405 je 0x55b963
0x55b960 ff525c call dword ptr [edx + 0x5c]
REL32_XREFS_42A5B0
0x42c90d e89edcffff
0x42cc80 e82bd9ffff
0x42d17d e82ed4ffff
```

补充反汇编实际读取了0x4CBBA0..0x4CBC3B、0x6D2790..0x6D2AD0、0x6DA980..0x6DAA20、0x4664C0..0x466610、0x55D360..0x55DE90等区间，并另从已对齐的0x466468、0x466607、0x6D2983、0x6D1A60、0x42A688核查到对应ret/控制点；第4、5项均给VA+原始字节可直接追溯。首次探读0x55B8D0以及0x4663E0的开头有未对齐垃圾解码，**未使用这些开头作证据**；本底稿采用0x55B8F0已对齐入口之后及0x466468重读后的有效指令。不把任意起点可反汇编当作函数身份；Bullet身份以RTTI和虚表链核实。

## 附录B：指定三窗检查

实际运行命令：

```bash
python -I -X utf8 -c 'import json,pathlib,statistics; b=pathlib.Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c")
for k in range(3):
 p=b/f"measure_w{k}.json"; d=json.loads(p.read_text(encoding="utf-8")); e=d["frame_edges"]; vals=[(tb-ta)*1000 for (fa,ta),(fb,tb) in zip(e,e[1:]) if fb-fa==1]; print(str(p),"stored",d["stats"]["frame_ms_p50"],"recomputed",statistics.median(vals),"n",len(vals))'
```

实际输出，退出码0：

```text
D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_1101v4c\measure_w0.json stored 50.47639999247622 recomputed 50.47699999704491 n 463
D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_1101v4c\measure_w1.json stored 33.11079999548383 recomputed 33.11049999319948 n 710
D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_1101v4c\measure_w2.json stored 32.422699994640425 recomputed 32.422000003862195 n 767
```

首次同类命令未指定UTF-8，`read_text()`按系统GBK读取而退出码1，报`UnicodeDecodeError: 'gbk' codec can't decode byte 0x85 in position 521: illegal multibyte sequence`；随后上述显式UTF-8命令成功。Read直接显示该大JSON还触发单行内容过大限制，所以不编造JSON行号；证据取上述实际解析与输出，定位到JSON键`stats.frame_ms_p50`和`frame_edges`。

## 附录C：阈值出处检查

实际执行，退出码0：

```bash
rg -n '300|1500|1,500|≤ 10|le 10|数百|每秒|次/秒|0\.5.*2\.8' lead/re_line_20261105/W3_COSTBOUND/sections/Q1_C1_PATHFIND.md lead/re_line_20261105/W3_COSTBOUND/sections/Q3_SAMPLE_PLAN.md
```

关键实际输出位置与内容：Q1仅命中:135「500 ~ 1,500 条指令 / 节点」、:159「300 个单位（按 2,000 节点）在同一帧触发寻路」、:211理论耗时段；Q3命中:17、:51、:52、:203的上述阈值，以及:275「系基于 Q1 指令上界与物理动力学的严格推导，其实测数值分布需待获得 D-13 授权后在真机运行期实测核对」。这些命中不能把每帧假想并发单位数转换成已实测每秒代际戳差分。判断“无依据”还依据亲读Q1全文及Q3紧邻解释，未以单次关键词无命中代替阅读。

本次不核准W3所援引的全87窗/22慢窗形态普遍断言，不核准采样开销/零扰动百分比、不核准实际三类成本分解，也未跑测试套件或构建；本次已完成的是指定三窗原始数值检查、双方原文核对和上述静态地址/写入机制核证。
