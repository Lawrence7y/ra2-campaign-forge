import pathlib,pefile,sys
root=pathlib.Path(r'D:\Project\ra2-campaign-forge');pe=pefile.PE(str(root/'ra2youli/gamemd.exe'));IB=pe.OPTIONAL_HEADER.ImageBase
for s in sys.argv[1:]:
    va=int(s,16);b=pe.get_data(va-IB,120)
    out=b.split(b'\0')[0]
    print('%08X %r'%(va,out[:120]))
