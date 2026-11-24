// W157: cross-checks for LEAD_AUDIT.
// (1) which function contains 0x67CC30 (W151 mislabeled it as 67CEF0?)
// (2) IAT symbol names for the imports used by 67CEF0/67D300
// (3) vtable slot index of 0x5F6250 at its 8 DATA xref sites
// @category W157
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W157Verify extends GhidraScript {
    Address addr(long v){ return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    public void run() throws Exception {
        println("### IMAGEBASE="+currentProgram.getImageBase());
        FunctionManager fm=currentProgram.getFunctionManager();
        // (1)
        long probe=0x67CC30L;
        Function f=fm.getFunctionContaining(addr(probe));
        println("### 0x67CC30 containing fn = "+(f==null?"NULL":(f.getName()+" @"+f.getEntryPoint()+" size="+f.getBody().getNumAddresses())));
        // confirm 0x67CEF0 exact bounds
        Function g=fm.getFunctionAt(addr(0x67CEF0L));
        println("### 0x67CEF0 exact="+(g!=null)+" range="+(g==null?"-":(g.getEntryPoint()+".."+g.getBody().getMaxAddress())));
        // (2) IAT symbols
        long[] iats={0x7e11c4L,0x7e15c8L,0x7e15e8L,0x7e15fcL,0x7e1600L,0x7e15f4L,0x7e9540L};
        for(long ia:iats){
            Address a=addr(ia);
            Symbol sym=getSymbolAt(a);
            ReferenceIterator ri=currentProgram.getReferenceManager().getReferencesTo(a);
            String ext="";
            while(ri.hasNext()){Reference r=ri.next(); Address t=r.getToAddress();
                if(t!=null && t.getAddressSpace().getName().equals("EXTERNAL")){ ext=" -> "+t+" ("+t.toString()+")"; break; }}
            println(String.format("### IAT %08x sym=%s%s", ia, sym==null?"-":sym.getName(), ext));
        }
        // (3) vtable slot: dump dwords around each xref site, mark which index holds 0x5f6250
        long[] sites={0x7e4718L,0x7ec28cL,0x7ef094L,0x7ef408L,0x7ef988L,0x7f3330L,0x7f66dcL,0x7f6c28L};
        for(long s:sites){
            // scan backwards up to 0x100 bytes to find vtable start (first dword that is a code address among a run)
            StringBuilder sb=new StringBuilder();
            sb.append(String.format("### VTABLE site %08x: holds=%08x ; dwords[-0x40..+0x8]:", s,
                    currentProgram.getMemory().getInt(addr(s))&0xffffffffL));
            for(int d=-0x40; d<=8; d+=4){
                long v=currentProgram.getMemory().getInt(addr(s+d))&0xffffffffL;
                sb.append(String.format(" %x:%08x", s+d, v));
            }
            println(sb.toString());
        }
        println("### DONE");
    }
}
