# S10-K8 PROGRESS（≤60 行）
现场读盘时点 2026-11-18T04:34:48+08；成稿 04:38+08。gamemd.exe SHA-256 73201CC0...F67476、size 4825360，只读；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；无 Ghidra；写域仅 S10_K8。
基线复算：coverage.tsv SHA C4805489...CAF43、size 3652533、mtime 2026-11-18T04:05:20.480290+08；统一大小写、只读第 5 列：S10 528 行、∩atlas 526、表外 2；[已证] 92/526=17.4905%，named(S) 52，门槛 263，差 171。
delta 固定列序（无表头）：entry / subsystem / name / one_line_semantics / grade / evidence_path / n_sources / conflict / name_kind。name_kind 仅 symbolic/behavioral/placeholder；行为复述名一律 behavioral，不冒充真方法名。
交付 10 行：S10 7 行新证 + S22 3 行（2 新证、1 仅改名）；004DFA70、00521760、006B7F10 不动。

## 审计意见落实
- Lead-1 / R14-R17：004DFA70/00521760 的环②=被调 QueueMission 字段写与环④同源，退 [静态推断]，不进本卡 delta；不重复计证。
- Lead-2：004E0E80 按 D-37 裁决前不动归属，暂留 S10，delta conflict=1 且语义明写“归属待 D-37”。
- Lead-3：K6 带偏移名去偏移并改 behavioral；队列 6 行均 behavioral；RTTI 类+ctor 角色名标 symbolic。
- K6 审计：004DFB70/004DFCB0/004DFE00 有单 id、自带字段写、[v+0x1E8]、[v+0x480]、ret 1，原拒绝理由不成立，抓回。
- K7 审计：006B6FA0 “无 RTTI 类名”为伪；006B6EA0/006B6FA0 补 [已证]，006B6C90 从 sub_ 改为 ctor 名；006B7F10 排除正确。

## 同族函数的可证判据（ctor/dtor/QueueMission 包装体统一口径）
同时满足 1-3 且通过 4 的同族一致性审查，可判 [已证]；5 是正负例。
1. 类锚：RTTI vptr/COL/TD 名或独立虚表组作类名；slot 号只定位，不作语义。
2. 角色锚：ctor/dtor 须有 ecx=this 或明确构造目标、基类/成员初始化、返回形态；QueueMission 须有 push target,id + ecx=this + [v+0x1E8] 且 body 自身字段写。
3. 链闭合：虚调用按该类真槽目标追到 override/基类字节；同一被调字段写既当环②又当环④只算一条，禁止双计。
4. 同族一致：同形行不得因“零字段写被选、有字段写被弃”反向剔除；死代码仅削弱 caller 通道，不否定 RTTI+角色双通道。
5. 例证：006B7F10 是 slot5、构造 arg1(ebx) 而非 ecx=this，角色锚失败；006B6FA0 写完整 4-vptr 组→TD 00840120、call 004101C0、成员初始化同 006B6EA0、ret 4，虽无 caller 仍过 1/2/4。

## 三行环③④补证（其余三行误杀同链）
 AircraftClass 主虚表 007E22A4：+0x1E8=0041BA90（override）、+0x1EC=0041B870；InfantryClass 007EB058 才直指 005B35E0/005B3570。
 0041BA90：cur∈{4,26,27,30,31} ∧ [this+0x294]==0 时 →0041BADE 吞请求；否则 →0041BAD3→005B35E0。
 005B35E0 早退：cur==0x13；cur==0x1C 且 id==5；id==-1；cur==id 且 queued!=-1。仅否则写 [this+0xB4]=id、清 [this+0xB8]；target=1 且 [v+0x200] 为真再经 0041B870→005B3570（cur=30 跳过清 +0x6D2）。
 004DF320：id=2/1；004DF3A0：id=1；006F4960：id=15。语义栏已写明吞请求前置条件和 cur==id 早退；故三行保 [已证]，name_kind=behavioral。

## 结算与校验
 S10 模拟：proved 92→99/526=18.8198%，named(S) 52→59，门槛剩差 164；004E0E80 若 D-37 改归 S22，S10 应回退为 98。
 S22 按盘上归属不动：proved 54→56/4851=1.1544%，named 4→7；006B6C90 仅改名不增 proved。
 校验：10 行/9 列、entry 与 name 唯一、name 无 +0x 偏移、证据路径全存在、0 placeholder；EVIDENCE/DELTA_VALIDATE.txt。
 证据：EVIDENCE/BASELINE_RECOMPUTE_K8.txt、QUEUE_DISPATCH_AND_FALSE_KILLS.txt、SPAWNMANAGER_CTORS.txt、OWNERSHIP_004E0E80.txt、S22_BASELINE_K8.txt；复算脚本见 work/。
