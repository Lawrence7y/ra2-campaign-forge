# SEMFIX-SLOTS3 DISAGREE（与卡面不符 / 审计订正记录）

本卡只搬已审计结论并给 grade，不重做逆向。下列为「核锚时与来源卡面标注不符、已按审计订正后写入语义栏」的清单。核锚手段：对 gamemd.exe（只读，SHA-256 73201CC0...F67476）用 capstone 5.0.7(skipdata)+pefile 现场反汇编，见 work/anchor_verify_result.json 与 EVIDENCE/ROW_*.txt。

## 与卡面不符（3 处引证 + 2 处 S09 偏移/措辞，均按审计订正）
1. **006F3330 +0x0BD**：来源卡面 delta 写「cmp [eax+0xd50],-1 / +0x0C4 je 错误路(无效索引→错路)」。核锚实测 +0x0BD `cmp dword ptr[eax+0xd50],-1` / +0x0C4 `je 0x6f3410` 落点 +0x0E0 为 `mov cl,[edi+0x14]/and cl,1/neg/sbb/and ecx,edi/mov ebp,ecx`——是**候选对象选择续行，非错误路**（a-S05-KPROVED3 VERDICT §3.1）。语义栏已改称「候选对象回退续行」。③b② 的真正硬证据在 +0x478 cmp eax,-1 / +0x47D xor eax,eax（-1归零返回），核锚逐字命中。
2. **006FFEC0 +0x3D3**：来源卡面 delta 写「cmp edx,-1 / +0x3D6 je 错误路(无效索引-1→错路)」。核锚实测 +0x3D3 `cmp edx,-1` / +0x3D6 `je 0x7002a6` 落点 +0x3E6 为 `test eax,eax / +0x3E8 jne / +0x3EA xor bl,bl`（setne bl 谓词），且 +0x3D8 `mov ecx,[0xa8ed84]`（CurrentFrame）/ +0x3DE `sub ecx,edx`——是**未初始化时间戳哨兵→setne bl 谓词，非无效索引**（VERDICT §3.1）。语义栏已按审计更正。
3. **006F8DF0 +0x50B/+0x552**：来源卡面 delta 把两处 `add eax,ecx` 记为「推进」。核锚实测二者是虚拟扩容调用 `call [edx+8]` 前的**尺寸计算**；真实推进/写是 +0x522 `mov [edi+0x10],ecx`（计数写）/ +0x525 `mov [edx+eax*4],ebp`（元素写），界判 +0x57B `cmp eax,ecx`（VERDICT §3.2）。语义栏已改称「扩容尺寸计算(非推进)」并补真实写锚点。
4. **006D04F0 闸2跳转**：来源卡面 delta 写「test [esi+0x5544] → je(+0x0023) 分支A」。核锚实测 +0x0023 是 `mov al,byte ptr[esi+0x5544]`，真正的 `je 0x6d05c3` 在 +0x0029（a-S09-KPROVED5 VERDICT §2 判据5 缺陷）。语义栏已按 +0x0029 订正并注明卡面 +0x0023。
5. **006C6680 拷贝闸**：来源卡面 delta 偏移表 +0x0042 重复、写「test分配结果(+0x003E/+0x0042)」。核锚实测 +0x003C `test eax,eax` / +0x003E `je 0x6c66ca` / +0x0042 `call 0x7ca489`（拷贝）（VERDICT §2）。语义栏已按 +0x003C/+0x003E/+0x0042 订正。

## 按审计订正 name（3 行，地址-名字对应取自 S05 VERDICT §2「命名缺陷」）
- 006F3330 → `TechnoClass::slot185`（来源卡面 delta 为 FootClass::slot185；盘上 coverage.tsv name 列亦为 TechnoClass::slot185，二者一致）
- 006FC0B0 → `TechnoClass::slot240`（来源卡面 delta 为 FootClass::slot240；盘上 name 列 TechnoClass::slot240）
- 00716150 → `TechnoTypeClass::slot42`（来源卡面 delta 为 AircraftTypeClass::slot42；盘上 name 列 TechnoTypeClass::slot42）
说明：语义栏「前半句」按要求保留盘上原文（如 006F3330 仍为「FootClass 虚表槽185...」），仅 name 列按审计订正；这与盘上 name 列现值一致，不引入新的类名改动。

## grade 口径
- 两张审计均把 15 行列入白名单、③b 档成立（S05 7 行白名单；S09 8 行白名单），核锚逐行通过 → 全部 grade=[已证]。
- 文档层弱点 2 行（00716150 栈累加器写口径 DISAGREE D4、0070BF50 非典型 ③b② D6）与 S09 的 004F4320（唯一不达审计 strict 检测器、边缘成立）均不改变「③b 档成立」结论，故不降 grade；已在 PROGRESS 逐行备注。
- 00704350 为 S05 审计黑名单（③b 不成立，回退），本卡按指令排除，未处理。
