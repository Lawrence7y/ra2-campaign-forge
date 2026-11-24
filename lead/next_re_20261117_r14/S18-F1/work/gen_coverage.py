"""S18-F1: generate coverage_delta.tsv (no direct edit of COVERAGE\coverage.tsv).
entry(hex8) TAB subsystem(S18) TAB name TAB one_line_semantics TAB grade TAB evidence_path
"""
import os

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\coverage_delta.tsv'
EV = r'EVIDENCE'

# (entry, name, semantics, grade, evidence_file)
rows = [
    ('4C6CB0','NetworkEvent::Execute','thiscall 事件分派器：dec Kind,cmp 0x2D,jmp [eax*4+0x4C8114] 46项','[已证]','eventtype_names.txt'),
    ('4C6CF0','Handler_POWERON','Kind1 电力开：NetID 解包建筑→置电力','[已证]','explore0.txt'),
    ('4C6D4D','Handler_POWEROFF','Kind2 电力关','[已证]','explore0.txt'),
    ('4C6DEE','Handler_ALLY','Kind3 结盟：改 HouseClass 关系','[静态推断]','eventtype_names.txt'),
    ('4C71CA','Handler_MEGAMISSION','Kind4/5 编队任务（也走二级缓冲 0xA83EDC）','[静态推断]','eventtype_names.txt'),
    ('4C74CB','Handler_IDLE','Kind6 待机','[静态推断]','eventtype_names.txt'),
    ('4C7859','Handler_SCATTER','Kind7 散开','[静态推断]','eventtype_names.txt'),
    ('4C7BDF','Handler_DESTRUCT','Kind8 摧毁','[静态推断]','eventtype_names.txt'),
    ('4C76BC','Handler_DEPLOY','Kind9 部署','[静态推断]','eventtype_names.txt'),
    ('4C7823','Handler_DETONATE','Kind0xA 引爆','[静态推断]','eventtype_names.txt'),
    ('4C70E1','Handler_PLACE','Kind0xB 放置：读 [esi+0x13] cell 字','[已证]','eventtype_names.txt'),
    ('4C7929','Handler_OPTIONS','Kind0xC 选项','[静态推断]','eventtype_names.txt'),
    ('4C794B','Handler_GAMESPEED','Kind0xD 游戏速度','[静态推断]','eventtype_names.txt'),
    ('4C711B','Handler_PRODUCE','Kind0xE 生产：读 [esi+0xF]','[已证]','eventtype_names.txt'),
    ('4C7140','Handler_SUSPEND','Kind0xF 暂停生产','[已证]','eventtype_names.txt'),
    ('4C7163','Handler_ABANDON','Kind0x10 放弃生产','[已证]','eventtype_names.txt'),
    ('4C718C','Handler_PRIMARY','Kind0x11 主生产','[静态推断]','eventtype_names.txt'),
    ('4C78D6','Handler_SPECIAL_PLACE','Kind0x12 超武放置：读 [esi+0xB] 字','[已证]','eventtype_names.txt'),
    ('4C7903','Handler_EXIT','Kind0x13 退出/踢人：写 House+0x248=1','[已证]','eventtype_names.txt'),
    ('4C6FDE','Handler_ANIMATION','Kind0x14 动画：读 [esi+0x13]','[已证]','eventtype_names.txt'),
    ('4C6ED2','Handler_REPAIR','Kind0x15 修理','[静态推断]','eventtype_names.txt'),
    ('4C6F12','Handler_SELL','Kind0x16 出售','[静态推断]','eventtype_names.txt'),
    ('4C6FB3','Handler_SELLCELL','Kind0x17 出售格：读 [esi+9] 字','[已证]','eventtype_names.txt'),
    ('4C6E48','Handler_SPECIAL','Kind0x18 超武','[静态推断]','eventtype_names.txt'),
    ('4C8109','Handler_noop','Kind0x19/1A/1C/25/26 no-op（pop..ret 收尾）','[已证]','eventtype_names.txt'),
    ('4C79FF','Handler_RESPONSE_TIME','Kind0x1B 响应时间','[静态推断]','eventtype_names.txt'),
    ('4C7A14','Handler_SAVEGAME','Kind0x1D 存档命令','[静态推断]','eventtype_names.txt'),
    ('4C6DAA','Handler_ARCHIVE','Kind0x1E NetID→Techno 归档','[静态推断]','eventtype_names.txt'),
    ('4C7B4D','Handler_ADDPLAYER','Kind0x1F 加入玩家','[静态推断]','eventtype_names.txt'),
    ('4C7B73','Handler_REMOVEPLAYER','Kind0x23 移除玩家','[静态推断]','eventtype_names.txt'),
    ('4C800C','Handler_TIMING','Kind0x20 计时','[静态推断]','eventtype_names.txt'),
    ('4C80B1','Handler_PROCESS_TIME','Kind0x21 处理时间','[静态推断]','eventtype_names.txt'),
    ('4C80F6','Handler_PAGEUSER','Kind0x22 寻呼用户','[静态推断]','eventtype_names.txt'),
    ('4C7F35','Handler_LATENCYFUDGE','Kind0x24 延迟微调','[静态推断]','enqueue_add.txt'),
    ('4C7CF5','Handler_ABOUTTOEXIT','Kind0x27 即将退出','[静态推断]','eventtype_names.txt'),
    ('4C7BF1','Handler_FALLBACKHOST','Kind0x28 回退主机','[静态推断]','eventtype_names.txt'),
    ('4C7C12','Handler_ADDRESSCHANGE','Kind0x29 地址变更','[静态推断]','eventtype_names.txt'),
    ('4C6CDE','Handler_PLAN_*','Kind0x2A/2B/2C 计划模式（同目标）','[已证]','eventtype_names.txt'),
    ('4C6E2E','Handler_ALLCHEER','Kind0x2D 全欢呼（表现）','[静态推断]','eventtype_names.txt'),
    ('4C7188','Handler_ABANDON_ALL','Kind0x2E 全部放弃','[静态推断]','eventtype_names.txt'),
    ('4C6650','FillEvent_SellCell','thiscall 填充出售格事件到 111B 栈缓冲','[已证]','field_layout.txt'),
    ('4C66C0','FillEvent_Noopt','填充 no-op 事件（UI 泵 10 调用者）','[已证]','field_layout.txt'),
    ('4C6720','FillEvent_PlayerBased','填充 playerbased 事件（Options/Ally/GameSpeed）','[已证]','field_layout.txt'),
    ('4C6780','FillEvent_Waypoints','填充路径点事件','[已证]','field_layout.txt'),
    ('4C6800','FillEvent_Animation','填充动画事件（硬编码 Kind=0x14）','[已证]','field_layout.txt'),
    ('4C6970','FillEvent_ProduceAbandonSuspend','填充生产族事件（3 体变体）','[已证]','field_layout.txt'),
    ('4C6AE0','FillEvent_Place','填充放置事件','[已证]','field_layout.txt'),
    ('4C6B60','FillEvent_SWPlace','填充超武放置事件（2 体变体）','[已证]','field_layout.txt'),
    ('6CF240','SwizzleManager::Here_I_Am','存档指针重定位登记（全镜像 476 调用点）','[已证]','field_layout.txt'),
    ('71F8C0','TEventClass::ctor','触发器事件构造器：vptr×4 + +0x28/+0x30/+0x54 三 Swizzle 字段','[已证]','rtti_dump.txt'),
    ('64C380','Queue_ValidateExecute','队列消费：收包/到期判定(Ts<=CF)/CRC比对/desync/执行','[已证]','crc_frame.txt'),
    ('64DAB0','Compute_Frame_CRC','帧 CRC：6 对象集合+1 RNG，acc*2+sign+term→0xAC51FC','[已证]','crc_detail.txt'),
    ('647260','NetFrameSync','联机同步驱动（MainLogicFrame 唯一调用）','[已证]','final_verify.txt'),
    ('649CA0','Build_FrameInfo','构造 FrameInfo(Kind=0x1C)：Checksum=CRC,Delay,Timestamp 对齐','[已证]','enqueue_add.txt'),
    ('64A0C0','Receive_Packet','网络收包解压入 Queue ring','[静态推断]','callers.txt'),
    ('64BDD0','Build_SendPacket','组包发送（QueuedEvents→网络）','[静态推断]','callers.txt'),
    ('64DEA0','SyncReport','写 SYNC*.TXT 报告','[静态推断]','final_verify.txt'),
    ('6516F0','SyncDump','ExtraSyncInfo 多份 SYNC 报告','[静态推断]','final_verify.txt'),
    ('4C93D0','FrameCRC_quant_helper','CRC 坐标/朝向量化取值（obj+0x388/0x3A0）','[静态推断]','crc_detail.txt'),
    ('65C780','Randomizer::Random','局内 RNG（帧 CRC 每帧吃 1 次）','[已证]','crc_detail.txt'),
    ('55D360','MainLogicFrame','每逻辑帧：世界更新+同步驱动+CurrentFrame++','[已证]','crc_frame.txt'),
    ('48C8B0','UI_CommandPump','本地 UI→FillEvent 入队（帧逻辑之后）','[已证]','final_verify.txt'),
    ('410410','AbstractClass::CalculateChecksum','对象级 CRC v[13]：折 +0x10 dword/+0x20 byte','[已证]','crc_detail.txt'),
    ('4A1C10','Checksummer::Add_bulk','对象 CRC 累加原语（CRC-32 簇）','[静态推断]','crc_detail.txt'),
    ('6CF350','SwizzleManager::Reset','存档读回指针重定位（本卡引用 S17-F1）','[静态推断]','rtti_scan.txt'),
]

def main():
    with open(OUT,'w',encoding='utf-8',newline='\n') as f:
        for e,name,sem,grade,ev in rows:
            f.write(f"{e}\tS18\t{name}\t{sem}\t{grade}\t{EV}\\{ev}\n")
    print(f"wrote {len(rows)} rows -> {OUT}")

if __name__=='__main__':
    main()
