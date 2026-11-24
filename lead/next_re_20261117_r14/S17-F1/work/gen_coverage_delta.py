"""Generate coverage_delta.tsv for S17-F1 (card must NOT edit COVERAGE/coverage.tsv)."""
rows = []

def add(entry, name, sem, grade, ev):
    rows.append(f"{entry:08x}\tS17\t{name}\t{sem}\t{grade}\t{ev}")

EV = "lead/next_re_20261117_r14/S17-F1/EVIDENCE"
# top-level save chain
add(0x67CEF0, "Game_Save_Outer", "Save file constructor: SAVING GAME log, StgCreateDocfile, 15 metadata streams, CONTENTS, calls Save_Core", "[已证]", f"{EV}/analysis_main.txt;{EV}/verify_bytes.txt")
add(0x67D300, "Game_Save_Core", "COM/OLE save serializer: 35 template blocks + 28 inline vectors + scalars via IStream::Write/OleSaveToStream", "[已证]", f"{EV}/analysis_boundary_iat.txt;{EV}/analysis_main.txt")
add(0x67F7E0, "Save_Scalar_S1", "Scalar block S-1 writer: CurrentFrame 0xA8ED84 + Tag vector 0x8B40C8", "[已证]", f"{EV}/analysis_deep.txt;{EV}/verify_bytes.txt")
add(0x67F9C0, "Load_Scalar_S1", "Scalar block S-1 reader: CurrentFrame/Tag read back in Load_Core", "[已证]", f"{EV}/analysis_deep.txt;{EV}/verify_bytes.txt")
add(0x67E440, "Game_Load_Core", "Load core: StgOpenStorage, GameMode restore, OpenStream(CONTENTS), OleLoadFromStream, 15 IStream::Read", "[已证]", f"{EV}/analysis_deep.txt;{EV}/verify_bytes.txt")
add(0x4C6340, "Save_RawBlock_0x44", "Writes raw 0x44-byte block at ecx=0x8A38E0 via IStream::Write", "[已证]", f"{EV}/verify_bytes.txt")
add(0x689310, "Save_PreHelper", "Pre-save helper: scene/global metadata (SAVING GAME log cluster)", "[已证]", f"{EV}/verify_bytes.txt")
add(0x674730, "Save_Rules_Block", "RulesClass block writer (ecx=RulesClass::Instance 0x8871E0)", "[已证]", f"{EV}/verify_bytes.txt")
add(0x69B560, "Write_Skirmish_Session_Options", "Skirmish-only (GameMode==5) Session.Options writer", "[已证]", f"{EV}/verify_bytes.txt;{EV}/analysis_boundary_iat.txt")
# 35 byte-identical template block functions (0x67FDF0 + 0x80*i); #17 = Save_Sides
for i in range(35):
    va = 0x67FDF0 + 0x80*i
    if i == 16:
        add(va, "Save_Sides", "Template block #17 = Save_Sides, DynamicVector<SideClass*> @0x8B4120 (YRpp symbol)", "[已证]", f"{EV}/analysis_deep2.txt;{EV}/analysis_main.txt")
    else:
        add(va, f"Save_VectorBlock_{i+1:02d}", f"Template block #{i+1}: Serialize(IStream* ecx, DynamicVector<T*> edx) Write(Count)+OleSaveToStream; class name unproven (arg .bss obj)", "[已证]", f"{EV}/analysis_main.txt;{EV}/analysis_deep2.txt")
# Swizzle manager
add(0x6CF240, "SwizzleManager_Here_I_Am", "Here_I_Am (slot4): register {orig_ptr,&field} 8B entry into Swizzles_Old, zero field at 0x6CF2A8", "[已证]", f"{EV}/analysis_deep.txt;{EV}/verify_bytes.txt")
add(0x6CF2C0, "SwizzleManager_Here_I_Am3", "Here_I_Am 3-arg (slot6): register into Swizzles_New (+0x1C)", "[已证]", f"{EV}/analysis_deep.txt")
add(0x6CF230, "SwizzleManager_Reset_Thunk", "Reset wrapper (slot3): mov ecx,[esp+4]; call 0x6CF350", "[已证]", f"{EV}/analysis_deep.txt")
add(0x6CF350, "SwizzleManager_Reset", "Restore pass: qsort both swizzle tables, match orig value, write back new ptr at 0x6CF3BA, clear tables", "[已证]", f"{EV}/analysis_deep2.txt")
add(0x6CF320, "SwizzleManager_Compare", "qsort comparator for swizzle entries (compare orig pointer value)", "[静态推断]", f"{EV}/analysis_deep2.txt")
add(0x681080, "Save_VersionDescriptor_Setter", "Setter: mov eax,[esp+4]; mov [ecx],eax; ret 4 (fills Internal Version descriptor, not a compare)", "[已证]", f"{EV}/verify_bytes.txt")

with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\coverage_delta.tsv", 'w', encoding='utf-8', newline='\n') as f:
    f.write("\n".join(rows) + "\n")
print(f"wrote {len(rows)} rows")
