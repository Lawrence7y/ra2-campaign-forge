# Findings log — goal2 crash-address analysis
Binary: D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe
sha256[:16]=73201cc021497c95 ; size 4,825,360 B
Cross-check copy _src_L1_sf8_20261020\gamemd.exe: byte-identical (same sha256 full hash).

## Measured PE layout (addr_probe.py stage `pe`)
- image_base = 0x00400000, sect_align=0x1000, file_align=0x1000
- SizeOfImage = 0x00796000, EP = 0x007CD80F, subsystem=2 (GUI)
- DllCharacteristics = 0x0020 (IMAGE_LIBRARY). NX_COMPAT (0x0100) = CLEAR.
- 5 sections:
  [0] .text   VA=0x00401000 VS=0x003DF38D RS=0x003E0000 RAW=0x00001000 char=0x60000020  -RE (R/X, delta 0x00400000)
  [1] .rdata  VA=0x007E1000 VS=0x00030074 RS=0x00031000 RAW=0x003E1000 char=0x40000040  -R- (R/--, delta 0x00400000)
  [2] .data   VA=0x00812000 VS=0x00367BE4 RS=0x0006C000 RAW=0x00412000 char=0xC0000040  WR- (R/W, delta 0x00400000)
  [3] .rsrc   VA=0x00B7A000 VS=0x00018128 RS=0x00019000 RAW=0x0047E000 char=0x40000040  -R- (delta 0x006FC000)
  [4] .detour VA=0x00B93000 VS=0x00002718 RS=0x00003000 RAW=0x00497000 char=0xC0000040  WR- (delta 0x006FC000)

## Locate 0x0084F2BA
- Section .data (0x00812000-0x00B79BE4). intra-section off 0x3D2BA. delta 0x00400000. file off 0x008612BA.
- Page = 0x0084F000, page off 0x02BA. Inside file-backed extent (raw VA end 0x0087E000).
- Header protection for that page = MEM_WRITE(0x80000000) SET + MEM_READ(0x40000000) SET + MEM_EXECUTE CLEAR
  -> mapped PAGE_READWRITE. There is NO static reason a write to it fails.
- 32 bytes at 0x0084F2BA in the FILE = all 00. => float table is runtime-computed, not on disk.

## Alignment forensics (rigorous, grounded in the VA value)
- 0x0084F2BA mod 4 = 2. A 4-byte-aligned float element store from a 4-aligned base can NEVER
  land exactly on 0x...BA. So a genuine `mov [..],reg` 32-bit store whose EA==0x0084F2BA is
  only reachable via a byte/word store, or a base that is itself 2 mod 4, or a misaligned vector store.
- EIP == faulting-target == 0x0084F2BA is the canonical signature of an *instruction-fetch*
  violation (executing a non-executable page): ExceptionAddress == ExceptionInformation[1].
  .data is MEM_EXECUTE-CLEAR, so under a DEP=AlwaysOn/AlwaysOptIn policy executing 0x0084F2BA faults.
