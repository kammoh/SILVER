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
argparser.add_argument("-t", "--top-module", help="Top module")
argparser.add_argument("-f", "--force-synth", help="Force synthesis.", action="store_true")
argparser.add_argument("-d", "--debug", help="Run in debug mode", action="store_true")
argparser.add_argument("--silver-verbose", help="Run silver in verbose", type=bool, default=True)
argparser.add_argument("-v", "--verbose", help="Run in verbose", action="store_true")

args = argparser.parse_args()
top_module = args.top_module
assert top_module, "Top module must be specified"
yosys_tcl = silver_root / "yosys" / "synthesize.tcl"

yosys_run_dir = silver_root

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


def synthesize(yosys_bin, yosys_run_dir, source_files: list[str | Path], top_module, netlist_file):
    env = {
        **os.environ,
        "SV_SOURCES": " ".join(str(Path(s).resolve()) for s in source_files),
        "NETLIST_FILE": netlist_file,
    }
    if top_module:
        env["TOP_MODULE"] = top_module
    subprocess.run(
        [yosys_bin, "-c", yosys_tcl],
        cwd=yosys_run_dir,
        env=env,
        check=True,
    )
    fix_yosys_netlist(netlist_file)
    return netlist_file


def run_silver(
    silver_bin_path: str | Path,
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
    ]

    if args.silver_verbose or args.verbose:
        silver_cmd += [
            "--verbose",
            "1",
        ]
    silver_cmd = [str(arg) for arg in silver_cmd]
    print("Running:", " ".join(silver_cmd))

    subprocess.run(
        silver_cmd,
        cwd=silver_root,
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
if run_synth:
    netlist_file = synthesize(yosys_bin, yosys_run_dir, args.input_files, top_module, netlist_file)


silver_bin_path = (
    silver_root / "bin_debug" / "verify_debug" if args.debug else silver_root / "bin" / "verify"
)

run_silver(silver_bin_path, netlist_file, top_module)
