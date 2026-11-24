# -*- coding: utf-8 -*-
import io

rows = [
    ("0071CDA0", "S06", "PASS",
     "vt=007F522C slot5@007F5240=entry;COL=0080C3E0 pTD=00842D48 .?AVTerrainClass@@;vt[0]=00410260",
     "3b2",
     "ctor install 0071BBFF mov[esi],7F522C in_func=0071BB90 (5 callers; caller 0071CB6E preceded by push 0xe0 + call 7C8E17 operator new)",
     "no",
     "0071CDA0 398B:call 005F5E80@0071CE79/mov edi,eax@0071CE7E/test@0071CE80/jl 0x71CF23@0071CE82(0f8c9b000000) eax=edi 原样负码;成功路装4表@0071CE98..AC+成员容器slot4@0071CEB6+登记全局表0xB0E840,收尾 mov eax,edi@0071CF23;被调005F5E80 125B 内 call 00410380@005F5E8B+jl 005F5EF9 保负码 xor eax,eax@005F5EF7 返0;00410380 空流 E_POINTER@00410389 且正路 call[eax+0xc]=IStream::Read 读方向;㉓全枚举4写点:0071B7BC属非删除析构器0071B7B0、0071CE98在本行体内不可自证、atexit写点0;④锚0071BBFF行外真构造器且堆对象"),
    ("00432050", "S03", "PASS",
     "vt=007E1668 slot12@007E1698=entry;COL=007FA4D8 pTD=00815E38 .?AVCDFileClass@@;同entry亦在007E3A2C slot12(.?AVBufferIOFileClass@@ 基类未覆写)",
     "3b4",
     "ctor install 0047A9E3 mov[esi],7E1668 in_func=0047A9D0 (call 0x431B20 base ctor before, 13 callers) + direct call 00473B07 e8 44e5fbff",
     "no",
     "00432050 584B 完整缓冲I/O循环:回边0043224C 0f8567feffff jne 0x4320B9,循环体[4320B9,43224C];边界004320C1 2bfa sub edi,edx + 004320C3 3bdf cmp ebx,edi + 004320C5 7d02 jge 取 min(请求,[esi+34]-[esi+38]);循环体内I/O 00432175 call 7CA090 memcpy / 0043210B ff5228 / 0043211A ff5224 / 004321CF call 431DD0;循环体内非栈写 0043214C mov[esi+38],0 / 004321AE 894638 / 004321C0 894e4c 等(esi=this,均在本函数循环体内);方向 src=arg1+偏移 0043216D add ecx,eax,dest=[esi+30]+位置 00432171 add edx,[esi+30] ⇒ 用户数据写进内部缓冲(非读),与第4列一致;㉓全枚举222写点:187+4栈模板/29对象写/2删除析构器(00401953@00401950、004019BA@004019A0)已排除/atexit 0/本行体内0;④锚0047A9E3行外构造器"),
]

with io.open("verdict.tsv", "a", encoding="utf-8", newline="\n") as f:
    for r in rows:
        f.write("\t".join(r) + "\n")
print("appended", len(rows))
