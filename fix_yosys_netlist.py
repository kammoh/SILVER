#!/usr/bin/env python3
import argparse
import re


IN_OUT_PATTERN = re.compile(
    r"\s*(input|output|inout)\s+((wire|reg)\s+)?(\[\s*\d+\s*:\s*\d+\s*\]\s*)?(\S+)\s*;"
)


def fix_yosys_netlist(input_file, output_file):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix Yosys netlist")
    parser.add_argument("input_file", help="Input file")
    parser.add_argument("-o", "--output_file", required=False, default=None, help="Output file")
    args = parser.parse_args()
    if args.input_file and not args.output_file:
        args.output_file = args.input_file
    fix_yosys_netlist(args.input_file, args.output_file)
