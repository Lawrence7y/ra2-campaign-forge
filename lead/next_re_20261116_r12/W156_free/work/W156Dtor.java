// W156: decompile 0x43BCF0 (candidate Building destructor) and the AbsArray clear region.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
public class W156Dtor extends GhidraScript {
    DecompInterface di;
    void d(long addr) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(addr);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        println("=== " + a + " size=" + (f==null?-1:f.getBody().getNumAddresses()) + " ===");
        if (f==null) return;
        DecompileResults r = di.decompileFunction(f,90,monitor);
        if(r==null||!r.decompileCompleted()){println("FAILED");return;}
        println(r.getDecompiledFunction().getC());
    }
    public void run() throws Exception {
        di=new DecompInterface(); di.openProgram(currentProgram);
        d(0x0043BCF0L);
        println("W156Dtor DONE");
    }
}
