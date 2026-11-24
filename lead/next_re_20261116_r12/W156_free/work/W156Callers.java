// W156: enumerate callers of the array-delete primitives, decompile deleting dtor 0x459F20.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;
public class W156Callers extends GhidraScript {
    AddressFactory af; FunctionManager fm; ReferenceManager rm; DecompInterface di;
    void callers(long addr, String label) throws Exception {
        Address a=af.getDefaultAddressSpace().getAddress(addr);
        println("=== CALLERS of "+label+" "+a+" ===");
        ReferenceIterator it=rm.getReferencesTo(a); TreeSet<String> s=new TreeSet<String>(); int n=0;
        while(it.hasNext()){Reference r=it.next(); if(!r.getReferenceType().isCall()) continue;
            Function f=fm.getFunctionContaining(r.getFromAddress());
            s.add("  "+(f==null?"NOFUNC":f.getEntryPoint().toString())+" @"+r.getFromAddress()); n++;}
        println("  total calls="+n);
        for(String x:s) println(x);
    }
    void d(long addr) throws Exception {
        Address a=af.getDefaultAddressSpace().getAddress(addr);
        Function f=fm.getFunctionAt(a);
        println("--- DECOMP "+a+" size="+(f==null?-1:f.getBody().getNumAddresses())+" ---");
        if(f==null)return;
        DecompileResults r=di.decompileFunction(f,90,monitor);
        if(r==null||!r.decompileCompleted()){println("FAILED");return;}
        println(r.getDecompiledFunction().getC());
    }
    public void run() throws Exception {
        af=currentProgram.getAddressFactory(); fm=currentProgram.getFunctionManager();
        rm=currentProgram.getReferenceManager(); di=new DecompInterface(); di.openProgram(currentProgram);
        callers(0x0045AE10L,"ArrayDelete(0x45AE10)");
        callers(0x0045ADD0L,"ArrayDelete2(0x45ADD0)");
        d(0x00459F20L);
        println("W156Callers DONE");
    }
}
