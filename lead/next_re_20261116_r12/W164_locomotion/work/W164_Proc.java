// W164: who writes FootClass+0x278 (Locomotor?) — find vtable stores into locomotion objects
// Decompile the Locomotion main-table slot-3 and slot-0x5C functions to identify per-frame Process
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class W164_Proc extends GhidraScript {
    void dec(long t,String label)throws Exception{
        Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        Function f=currentProgram.getFunctionManager().getFunctionContaining(a);
        if(f==null){println("=== "+label+" @"+a+" NO FN ===");return;}
        println("=== "+label+" entry="+f.getEntryPoint()+" size="+f.getBody().getNumAddresses()+" ===");
        DecompInterface di=new DecompInterface();di.openProgram(currentProgram);
        DecompileResults r=di.decompileFunction(f,60,monitor);
        if(r!=null&&r.decompileCompleted()){
            int k=0;for(String ln:r.getDecompiledFunction().getC().split("\n")){println("C| "+ln);if(++k>55){println("C| ...");break;}}
        }
    }
    public void run()throws Exception{
        // main table slot 3 (offset 0xC) functions
        dec(0x004B4830L,"Drive main-slot3 (0x4B4830)");
        dec(0x004B4D00L,"Drive main-slot8 (0x4B4D00)");
        dec(0x0075C640L,"Walk main-slot3 (0x75C640)");
        dec(0x004AF720L,"Drive main-slot0 (0x4AF720)");
        // the common off4 slot23 function already known 0x55A910
    }
}
