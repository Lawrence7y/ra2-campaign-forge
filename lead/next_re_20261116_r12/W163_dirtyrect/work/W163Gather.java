// W163: decompile key dirty-rect / G_INGAME functions + xrefs to container fields.
// @category W163
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W163Gather extends GhidraScript {
    static String hx(long v){ return String.format("%08X", v); }
    Address addr(long t){ return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t); }

    public void run() throws Exception {
        println("W163_GATHER_BEGIN");
        println("imageBase="+currentProgram.getImageBase());

        // 1) xrefs to container fields (Ghidra reference model channel)
        long[] xs = { 0x00B0CE78L, 0x00B0CE7CL, 0x00B0CE80L, 0x00B0CE84L,
                      0x00B0CE85L, 0x00B0CE88L, 0x00B0CE8CL, 0x00A8E9A0L };
        for (long t : xs) {
            Address a=addr(t);
            ReferenceIterator ri=currentProgram.getReferenceManager().getReferencesTo(a);
            int n=0;
            LinkedHashSet<String> fns=new LinkedHashSet<String>();
            while (ri.hasNext() && n<300) { Reference r=ri.next();
                Address fr=r.getFromAddress();
                Function cf=currentProgram.getFunctionManager().getFunctionContaining(fr);
                println("XREF_TO "+hx(t)+" <- "+fr+" type="+r.getReferenceType()+" src="+r.getSource()
                        +" fn="+(cf==null?"NONE":cf.getEntryPoint().toString()));
                if (cf!=null) fns.add(cf.getEntryPoint().toString());
                n++;
            }
            println("XREF_TO_SUM "+hx(t)+" n="+n+" funcs="+fns.size());
        }

        // 2) decompile key functions
        DecompInterface di=new DecompInterface(); di.openProgram(currentProgram);
        long[] ds = { 0x006D1810L, 0x006D2790L, 0x006D2B60L, 0x006D3D10L, 0x006DA980L,
                      0x00421EA0L, 0x005F4EC0L, 0x004F4480L, 0x006D8DB0L,
                      0x00466560L, 0x0055D360L, 0x0052D9A0L, 0x0055FC80L,
                      0x00445A40L, 0x006D1F10L };
        for (long t : ds) {
            Function f=currentProgram.getFunctionManager().getFunctionContaining(addr(t));
            if (f==null){ println("DECOMP "+hx(t)+" NO_FUNC"); continue; }
            println("=== DECOMP "+hx(t)+" -> "+f.getEntryPoint()+" size="+f.getBody().getNumAddresses()+" ===");
            DecompileResults r=di.decompileFunction(f,90,monitor);
            if (r==null || !r.decompileCompleted()){ println("DECOMP_FAIL"); continue; }
            println(r.getDecompiledFunction().getC());
        }
        println("W163_GATHER_END");
    }
}
