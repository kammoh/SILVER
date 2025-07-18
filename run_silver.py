#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
silver_root = SCRIPT_DIR

argparser = argparse.ArgumentParser(description="Run Silver")
argparser.add_argument("input_files", nargs="+", type=Path, help="Source files")
argparser.add_argument("--attrs-json", type=Path, required=True, help="Source files")
argparser.add_argument("-t", "--top-module", "--top", help="Top module")
argparser.add_argument("-f", "--force-synth", help="Force synthesis.", action="store_true")
argparser.add_argument("-d", "--debug", help="Run in debug mode", action="store_true")
argparser.add_argument("--silver-verbose", help="Run silver in verbose", type=bool, default=True)
argparser.add_argument("-v", "--verbose", help="Run in verbose", action="store_true")

args = argparser.parse_args()
top_module = args.top_module
assert top_module, "Top module must be specified"
# yosys_tcl = silver_root / "yosys" / "synthesize.tcl"

silver_run_dir = Path.cwd() / f"silver_run_{top_module}"

silver_run_dir.mkdir(parents=True, exist_ok=True)

yosys_run_dir = silver_run_dir

yosys_bin = "yosys"


IN_OUT_PATTERN = re.compile(
    r"\s*(input|output|inout)\s+((wire|reg)\s+)?(\[\s*\d+\s*:\s*\d+\s*\]\s*)?(\S+)\s*;"
)


def fix_yosys_netlist(input_file, output_file=None):
    if not output_file:
        output_file = input_file
    # Read the input file
    with open(input_file, "r") as f:
        content = f.read()
    # If a line in content matches the pattern: "input  ..." or "output ..." and is followed by a line that matches the pattern "wire  <same_name>", then remove the second line
    lines = content.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        m = IN_OUT_PATTERN.match(line)
        if m:
            print(f"Found {m.group(1)} {m.group(5)}")
            if i + 1 >= len(lines):
                break
            next_line = lines[i + 1]

            arr = (
                m.group(4).strip().replace("[", r"\[").replace("]", r"\]") + r"\s*"
                if m.group(4)
                else ""
            )

            # print(f"{next_line} -> {m.group(4)} {m.group(5)}")
            if re.match(
                r"\s*(wire|reg)\s*" + arr + m.group(5).strip() + r"\s*;",
                next_line,
            ):
                # print(f">>  Found wire {m.group(5)}")
                i += 2
                continue
        i += 1
    # Write the output file
    with open(output_file, "w") as f:
        f.write("\n".join(new_lines))


def synthesize(
    yosys_bin,
    yosys_run_dir,
    source_files: list[Path],
    top_module,
    liberty_lib,
    verilog_netlist,
    silver_attrs,
    json_netlist=None,
    parameters=None,
    defines=None,
    opt_flatten=True,
    opt_full=False,
    quiet=False,
):
    # env = {
    #     **os.environ,
    #     "SV_SOURCES": " ".join(str(Path(s).resolve()) for s in source_files),
    #     "NETLIST_FILE": netlist_file,
    # }
    # if top_module:
    #     env["TOP_MODULE"] = top_module
    verilog_netlist = Path(verilog_netlist)

    yosys_script = []

    vhdl_files = []
    ghdl_args = ["--std=08"]

    if defines is None:
        defines = {}

    read_verilog_args = [
        "-noautowire",
        "-defer",
        "-noassert",
        "-noassume",
        "-nolatches",
    ]

    define_args = [f"-D{k}" if v is None else f"-D{k}={v}" for k, v in defines.items()]
    read_verilog_args += define_args
    slang_args = ["--extern-modules", "--best-effort-hierarchy"]
    slang_args += define_args

    sv_slang = True
    has_sv_files = any(f.suffix == ".sv" for f in source_files)

    for src in source_files:
        src = Path(src)
        if src.suffix == ".sv":
            if sv_slang:
                yosys_script.append(f"read_slang {' '.join(slang_args + [str(src)])}")
            else:
                yosys_script.append(
                    f"read_verilog {' '.join(read_verilog_args + ['-sv', str(src)])}"
                )
        elif src.suffix == ".v":
            yosys_script.append(f"read_verilog {' '.join(read_verilog_args + [str(src)])}")
        elif src.suffix in (".vhd", ".vhdl"):
            vhdl_files.append(src)
        else:
            raise ValueError(f"Unsupported file type: {src}")
    if vhdl_files:
        yosys_script += [
            f"ghdl {' '.join(ghdl_args)} {' '.join(map(str, vhdl_files))} -e",
        ]

    prep_args = []
    if top_module:
        prep_args += ["-top", top_module]
    else:
        prep_args.append("-auto-top")

    if parameters is not None:
        for k, v in parameters.items():
            prep_args += ["-chparam", k, str(v)]

    yosys_script += [
        f"read_liberty -lib {liberty_lib}",
        # "hierarchy " + " ".join(hierarchy_args),
        # "proc",
        "prep " + " ".join(prep_args),
        "async2sync",
        "memory_map",
        "opt_clean -purge",
        "check -assert",
    ]

    for select, value in silver_attrs.items():
        yosys_script.append(f"setattr -set SILVER {value} {select}")

    if opt_flatten:
        yosys_script.append("flatten")
        yosys_script.append("opt_clean -purge")

    rtl_dump = netlist_dir / "yosys_rtl.v"

    yosys_script += [
        # f"write_verilog -noattr {rtl_dump}",
        # f"log -stdout *** Elaborated RTL dumped to {rtl_dump}",
        # f"write_json {netlist_dir / 'yosys_rtl.json'}",
    ]
    yosys_script += []
    synth_args = [
        "-noabc",
        "-noshare",
        # "-booth",
        # "-nordff",
    ]
    # if opt_flatten:
    #     synth_args.append("-flatten")
    # post_synth_netlist = rtl_dump.with_stem("post_synth")
    yosys_script += [
        # "setattr -set keep_hierarchy 1",
        # f"read_verilog -lib {verilog_lib}",
        "log -stdout *** Starting synthesis",
        # "async2sync -nolower",
        f"synth {' '.join(synth_args)}",
        "opt_clean -purge",
        f"log -stdout *** Synthesis completed.",
        # f"write_verilog -noattr {post_synth_netlist}",
        # "opt_clean -purge",
    ]
    # if opt_full:
    #     yosys_script.append("opt -full -purge")
    # else:
    #     yosys_script.append("opt_clean -purge")

    yosys_script += ["splitnets -driver", "opt_clean -purge"]

    # yosys_script += ["splitnets", "opt_clean -purge"]

    abc_flags = [f"-liberty {liberty_lib}"]

    # if opt_full:
    #     abc_flags += ["-dff"]
    # else:
    #     abc_flags += ["-keepff", "-fast"]
    # abc_flags += ["-dff"]
    # abc_flags += ["-dress"]
    abc_flags += [
        "-script",
        "+strash;&get -n; &fraig -x; &put; scorr; dc2; strash; &get -n; &dch -f; &nf; &put".replace(
            " ", ","
        ),
    ]
    # abc_flags += [
    #     "-script",
    #     "+strash;map,{D}",
    # ]

    yosys_script += [
        "opt_clean -purge",
        # "write_verilog pre_abc_dump.v",
        # f"dfflibmap -prepare -liberty {liberty_lib}",
        "log -stdout *** Running DFF library mapping",
        f"dfflibmap -liberty {liberty_lib}",
        "opt_clean -purge",
        "log -stdout *** Running ABC",
        f"abc " + " ".join(str(e) for e in abc_flags),
        "opt_clean -purge",
        # "log -stdout *** Running DFF library mapping",
        # f"dfflibmap -liberty {liberty_lib}",
        "opt_clean -purge",
        "check -mapped -assert",
    ]

    yosys_script += ["insbuf"]

    if opt_full:
        yosys_script += [
            "opt -full -purge",
            "opt -full -fine -purge",
            "opt -full -fine -sat -purge",
            "opt -full -purge",
        ]

    yosys_script += [
        "setundef -zero",
        "opt -full -purge" if opt_full else "opt_clean -purge",
        # "setattr -set keep_hierarchy 0",
        "opt -purge",
        "flatten",
        "opt -purge",
        "check -assert -noinit -mapped",
    ]

    yosys_script += [
        "setattr -mod -unset top",
        "setattr -unset top",
        "setattr -mod -unset src",
        "setattr -unset src",
        "setattr -mod -unset keep_hierarchy",
        "setattr -unset keep_hierarchy",
        "setattr -mod -unset keep",
        "setattr -unset dont_touch",
        "setattr -mod -unset dont_touch",
        "setattr -unset keep",
    ]

    if opt_full:
        yosys_script += [
            "opt -full -purge",
            "opt -full -fine -purge",
            "opt -full -fine -sat -purge",
            "opt -full -purge",
        ]
    else:
        yosys_script.append("opt_clean -purge")

    # yosys_script += ["rename -src"]
    split_nets = True
    if split_nets:
        # yosys_script += ["splitnets -driver -format ___"]
        yosys_script += ["splitnets -driver"]

    # if top_module:
    #     yosys_script.append(f"select {top_module}")

    if opt_full:
        yosys_script.append("opt -full -purge")
    else:
        yosys_script.append("opt_clean -purge")

    write_verilog_args = [
        "-noexpr",
        "-nodec",
        "-simple-lhs",
    ]
    write_verilog_args.append(str(verilog_netlist))
    if not json_netlist:
        json_netlist = verilog_netlist.with_suffix(".json")

    yosys_script += [
        f"write_json {json_netlist}",
        # "check -assert -noinit -initdrv",
        f"stat -liberty {liberty_lib}",
        # "check -mapped -noinit -initdrv",
        "check -assert -mapped -noinit -initdrv",
        f"write_verilog {' '.join(write_verilog_args)}",
    ]
    yosys_cmd = [yosys_bin, "-Q", "-T"]
    if quiet:
        yosys_cmd.append("-q")
        yosys_cmd += ["-l", "yosys.log"]
    # else:
    #     yosys_cmd.append("-g")
    if vhdl_files:
        yosys_cmd += ["-m", "ghdl"]
    if sv_slang and has_sv_files:
        yosys_cmd += ["-m", "slang"]

    # write yosys_script to file
    yosys_script_file = yosys_run_dir / "yosys_script.ys"
    with open(yosys_script_file, "w") as f:
        f.write("\n".join(yosys_script))
    # yosys_cmd += ["-p", "; ".join(yosys_script)]
    yosys_cmd += ["-s", yosys_script_file.relative_to(yosys_run_dir)]

    print("\n" + "=" * 20 + " YOSYS SYNTHESIS " + "=" * 20)
    yosys_cmd = [str(c) for c in yosys_cmd]
    print(f"** Running {' '.join(yosys_cmd)}\n")
    subprocess.run(
        yosys_cmd,
        cwd=yosys_run_dir,
        check=True,
    )
    assert verilog_netlist.exists(), f"Failed to generate netlist {verilog_netlist}"
    assert json_netlist.exists(), f"Failed to generate json netlist {json_netlist}"
    print(f"** Generated netlist: {verilog_netlist}\n")
    print("" + "=" * 56 + "\n")
    fix_yosys_netlist(verilog_netlist)
    return verilog_netlist


def run_silver(
    silver_bin_path: Path,
    netlist_file: str | Path,
    top_module: str,
    insfile: str | Path | None = None,
):
    if insfile is None:
        insfile = Path(netlist_file).parent / f"{top_module}.nl"
    silver_cmd = [
        silver_bin_path,
        "--verilog",
        "1",
        "--verilog-design_file",
        netlist_file,
        "--verilog-module_name",
        top_module,
        "--insfile",
        insfile,
        "--verilog-libfile",
        silver_root / "cell/Library.txt",
    ]

    if args.silver_verbose or args.verbose:
        silver_cmd += [
            "--verbose",
            "1",
        ]
    silver_cmd = [str(arg) for arg in silver_cmd]
    print("Running:", " ".join(str(c) for c in silver_cmd))

    subprocess.run(
        silver_cmd,
        cwd=silver_run_dir,
        shell=False,
        check=True,
    )


netlist_dir = yosys_run_dir
netlist_file = netlist_dir / f"{top_module}_netlist.v"

run_synth = args.force_synth
if run_synth is None:
    # Check if the netlist file exists
    if not netlist_file or not netlist_file.exists():
        run_synth = True
    else:
        # check if modification time of the netlist file is older than the source files
        netlist_mtime = netlist_file.stat().st_mtime
        if any(netlist_mtime < Path(f).stat().st_mtime for f in args.input_files):
            run_synth = True


netlist_file = netlist_dir / (f"{top_module}_netlist.v" if top_module else "netlist.v")

liberty_lib = silver_root / "yosys/LIB/custom_cells.lib"
if not liberty_lib.exists():
    raise FileNotFoundError(f"Liberty library not found: {liberty_lib}")
if run_synth:

    args.input_files = [
        Path(p) if os.path.isabs(p) else Path(p).resolve() for p in args.input_files
    ]

    assert Path(args.attrs_json).exists(), f"Attributes JSON file not found: {args.attrs_json}"

    with open(args.attrs_json, "r") as f:
        import json

        silver_attrs = json.load(f)

    netlist_file = synthesize(
        yosys_bin,
        yosys_run_dir,
        args.input_files,
        liberty_lib=liberty_lib,
        top_module=top_module,
        verilog_netlist=netlist_file,
        silver_attrs=silver_attrs,
    )


silver_bin_path = (
    silver_root / "bin_debug" / "verify_debug" if args.debug else silver_root / "bin" / "verify"
)

run_silver(silver_bin_path, netlist_file, top_module)
