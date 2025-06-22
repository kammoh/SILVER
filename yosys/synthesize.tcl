if {![info exists ::env(SV_SOURCES)]} {
    puts "ERROR: SV_SOURCES not set"
    exit 1
}
set sv_sources $::env(SV_SOURCES)

if {[info exists ::env(TOP_MODULE)]} {
    set top $::env(TOP_MODULE)
} else {
    set top ""
}
if {[info exists ::env(NETLIST_FILE)]} {
    set netlist_file $::env(NETLIST_FILE)
} else {
    set netlist_file "${top}_netlist.json"
}

set cell_library yosys/LIB/custom_cells.lib
set verilog_library yosys/LIB/custom_cells.v

yosys -import

read_verilog -sv $sv_sources

setattr -set SILVER "\"clock\"" i:clk
setattr -set SILVER "\"clock\"" i:clock*
setattr -set SILVER "\"control\"" i:reset*
setattr -set SILVER "\"refresh\"" i:io_rand*
# setattr -set SILVER "\"\[11:0\]_0\"" i:io_a_0
# setattr -set SILVER "\"\[11:0\]_1\"" i:io_a_1
# setattr -set SILVER "\"\[23:12\]_0\"" i:io_b_0
# setattr -set SILVER "\"\[23:12\]_1\"" i:io_b_1
# setattr -set SILVER "\"\[12:0\]_0\"" o:io_sum_0
# setattr -set SILVER "\"\[12:0\]_1\"" o:io_sum_1
setattr -set SILVER "\"\[12:0\]_0\"" i:io_x_0
setattr -set SILVER "\"\[12:0\]_1\"" i:io_x_1
setattr -set SILVER "\"0_0\"" o:io_b_0
setattr -set SILVER "\"0_1\"" o:io_b_1
# setattr -set SILVER "\"\[12:0\]_0\"" o:io_sum_0
# setattr -set SILVER "\"\[12:0\]_1\"" o:io_sum_1

if {[string trim $top] eq ""} {
    set top_arg "-auto-top"
} else {
    set top_arg "-top $top"
}
hierarchy -check
prep {*}$top_arg
opt_clean -purge
check -noinit -initdrv
write_json  ${top}_netlist.json

read_verilog -lib $verilog_library
setattr -set keep_hierarchy 1;
# set synth_args "-run :coarse"
set synth_args "-noabc -noshare"
synth {*}$synth_args {*}$top_arg
opt_clean -purge

memory_map
opt_clean -purge


dfflibmap -liberty $cell_library
opt_clean -purge
abc -liberty $cell_library
# opt -full -purge -fine
opt_clean -purge

splitnets -format __
splitcells -format __
opt_clean -purge
#renames -src "w:\\*_"
#renames -hide "w:\\*_*_"
# hierarchy -check

stat -liberty $cell_library

setattr -set keep_hierarchy 0;
setattr -unset keep_hierarchy
flatten
select $top
opt_clean -purge
insbuf -buf BUF A Y
# clean -purge

setattr -mod -unset top
setattr -unset src a:src
setattr -mod -unset src
setattr -unset keep_hierarchy a:keep_hierarchy
setattr -mod -unset keep_hierarchy
setattr -unset keep a:keep
setattr -mod -unset keep
puts "Checking netlist..."
check -assert -noinit -initdrv -mapped
puts "Writing netlist to ${netlist_file}"
write_verilog -selected -simple-lhs -noexpr ${netlist_file}