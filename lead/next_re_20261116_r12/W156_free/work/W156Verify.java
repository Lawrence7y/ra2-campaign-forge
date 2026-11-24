// W156: BuildingClass vtable slots 0-3 + predicate 0x5F5850 + refs to 0x43BCF0.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
public class W156Verify extends GhidraScript {
    AddressFactory af; FunctionManager fm; ReferenceManager rm; DecompInterface di;
    public void run() throws Exception {
        af=currentProgram.getAddressFactory(); fm=currentProgram.getFunctionManager();
        rm=currentProgram.getReferenceManager(); di=new DecompInterface(); di.openProgram(currentProgram);
        long[] vts={0x007E3EBCL,0x007E3EA0L,0x007E3E98L,0x007E3E90L};
        for(long vt:vts){
            Address a=af.getDefaultAddressSpace().getAddress(vt);
            println("=== VT " + Long.toHexString(vt) + " ===");
            for(int i=0;i<4;i++){
                long v=currentProgram.getMemory().getInt(a.add(i*4L))&0xffffffffL;
                println("  ["+i+"] = "+String.format("%08x",v));
            }
        }
        Address t=af.getDefaultAddressSpace().getAddress(0x0043BCF0L);
        println("=== REFS to 0x43BCF0 (dtor) ===");
        ReferenceIterator it=rm.getReferencesTo(t); int n=0;
        while(it.hasNext()){Reference r=it.next(); Function f=fm.getFunctionContaining(r.getFromAddress());
            println("  "+r.getReferenceType()+" @" + r.getFromAddress() + " in " + (f==null?"NOFUNC":f.getEntryPoint())); n++;}
        println("  total="+n);
        // predicate
        Address pa=af.getDefaultAddressSpace().getAddress(0x005F5850L);
        Function pf=fm.getFunctionAt(pa);
        println("=== PREDICATE 0x5F5850 size="+(pf==null?-1:pf.getBody().getNumAddresses())+" ===");
        if(pf!=null){DecompileResults r=di.decompileFunction(pf,90,monitor);
            if(r!=null&&r.decompileCompleted()) println(r.getDecompiledFunction().getC()); else println("FAILED");}
        println("W156Verify DONE");
    }
}
