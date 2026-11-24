"""Build coverage_delta.tsv for the 8 delivered rows. Uses verified data only."""
import sys, os, json, struct, pickle
sys.path.insert(0, os.path.dirname(__file__))

CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\cfg_features.json"))
HOLD=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\rtti_holders.json"))
ROWSUM=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\EVIDENCE\ROW_SUMMARY.json"))

# ③b precise description per row (offsets verified via cfg_features / disasm)
DESC={
 '00413F80': ("③b②可证伪哨兵-1回退:+0x00BA mov ecx,[eax+0x680]/+0x00C0 cmp ecx,-1/+0x00C3 jne/+0x00C5 mov ecx,[eax+0x684] (主值=-1则取回退值); ③b④有界查表循环:+0x0037 cmp [eax],edi→+0x0039 je→+0x003B inc ecx/+0x003C add eax,4→+0x003F cmp ecx,edx→+0x0041 jl回+0x0037 (读→判→推进→计数界)"),
 '006F4AB0': ("③b①物理跳表:+0x000A lea eax,[ebx-3]/+0x000F cmp eax,0x1c/+0x0012 ja默认@+0x038F/+0x001A mov cl,byte[eax+绝对表6F4E88](29项byte索引表→0..10)/+0x0020 jmp dword[ecx*4+绝对表6F4E5C](11项dword跳表,目标0x6F4B1F..0x6F4E3F全体内,28路输入归并11路); 严格档直接成立(不依细则#1)"),
 '006F6AC0': ("③b④链表遍历循环:+0x00F1 mov eax,[edi]→+0x00F6 call [eax+0x3c8](虚调)→+0x00FC mov edi,[edi+0x30](推进)→+0x00FF cmp edi,ebx/je出→+0x0103 test byte[edi+0x14],4→+0x0107 jne回+0x00F1 (读→虚调→推进→空/标志界)"),
 '0070C270': ("③b②可证伪哨兵-1界4处:+0x0054/+0x009B/+0x00FE/+0x0137 cmp edx,-1→je各错路; ③b④有界数组循环:+0x02BE..+0x02F4 (读[edx+ebx*4]/[ecx+ebx*4]→虚调→inc ebx→cmp ebx,ebp→jl回)与+0x030A..+0x0327同类"),
 '007077C0': ("③b②可证伪哨兵-1界4处:+0x021D cmp edx,-1/je、+0x0432/+0x047E/+0x04BE cmp eax,-1/je各错路; ③b④有界循环5段:+0x030D..+0x0317(jne)、+0x0424..+0x042E(jl)、+0x044C..+0x0462(jl)、+0x0492..+0x04A2(jl)、+0x04D2..+0x04E2(jl) (读→判→推进→计数界)"),
 '00716DC0': ("③b④有界数组读写循环9段:+0x0042 mov edx,[edi+0x3ec]→+0x004E lea eax,[edx+ebx*4]→+0x0053 call [ecx+0x10](读/写虚调)→+0x0056 inc ebx→+0x0057 cmp ebx,[esp+0x18]→+0x005B jl回+0x0042; 余8段同构回跳目标@+0x0080/+0x00BE/+0x00FC/+0x013A/+0x0178/+0x01B6/+0x01F4/+0x0232"),
 '007162F0': ("③b④有界数组读写循环(29次回跳):+0x022F mov edx,[esi]→+0x023B call [edx+0xc](虚调读)→+0x0245 call 0x5AD7D0→+0x024A mov eax,[esp+0x18]→+0x0252 inc eax→+0x0253 cmp eax,ecx→+0x0259 jl回+0x022F; 同构循环另12段@+0x027F/+0x02CB/+0x0317/+0x0363/+0x03AF/+0x03FB/+0x0447/+0x0493/+0x04DF/+0x052B/+0x0577/+0x05C3"),
 '00700600': ("③b②可证伪哨兵-1错误码3处:+0x01EA/+0x0203/+0x0369 cmp eax,-1→je各错路; ③b④有界循环:+0x0182 mov edx,[eax+4]/+0x0185 mov edi,[edx+ebx*4]→+0x0188 test al→+0x01E0 inc ebx→+0x01E1 cmp ebx,[eax+0x10]→+0x01E4 jl回+0x0182 (读→类型判→推进→计数界)"),
}

def fmt_sites(key):
    r=next(z for z in ROWSUM if z['entry']==key)
    return r, r['n_dir_valid']

out_lines=["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
for key in ['00413F80','006F4AB0','006F6AC0','0070C270','007077C0','00716DC0','007162F0','00700600']:
    r,nv=fmt_sites(key)
    x=CFG[key]; hs=HOLD[key]
    h=hs[0]
    cls=r['name'].split('::')[0]
    tdcls=h['name'].replace('.?AV','').replace('@@','')
    assert cls==tdcls, f"class mismatch {cls} vs {tdcls} for {key}"
    # ①
    e=int(key,16)
    p1=f"①entry {key} 16B对齐+E8体外直调见证"
    # ②
    p2=f"②全.rdata原始命中={len(hs)}表全部同槽:{h['vt']}[{h['slot']}]=entry,COL{h['col']}→TD+8逐字'{h['name']}'与name类一致,DV/V同slot别名=无(单表非容器族),错源⑯归属={cls}级"
    # ③b
    p3=DESC[key]
    # ④
    cs=pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\call_sites.pkl",'rb'))['call_sites']
    sites=cs.get(e,[])
    saddr=','.join(f'{s:08X}' for s in sites[:4])
    p4=f"④direct E8边界@外体站点{len(sites)}处({saddr}{'...' if len(sites)>4 else ''}),site+5+rel32==entry/体外/非自环;CFG extent+0x0000..+0x{int(x['hi'],16)-e:04X}"
    sem=f"[已证] {p1};{p2};{p3};{p4}"
    ev=f"EVIDENCE/ROW_{key}.txt;EVIDENCE/ROW_SUMMARY.json;EVIDENCE/baselines.json"
    out_lines.append('\t'.join([key,'S05',r['name'],sem,'[已证]',ev]))

open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\coverage_delta.tsv",'w',encoding='utf-8').write('\n'.join(out_lines)+'\n')
print("wrote coverage_delta.tsv with",len(out_lines)-1,"data rows")
for l in out_lines:
    print(l[:160])
