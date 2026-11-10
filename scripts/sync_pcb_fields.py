#!/usr/bin/env python3
"""Copy sourcing fields and values from a schematic netlist onto PCB footprints.

Headless stand-in for the field part of "Update PCB from Schematic". Pure text
edits: tracks, zones and rule areas are left byte-for-byte untouched (a pcbnew
Python save drops KiCad 10 placement rule areas). New properties are cloned from
the footprint's own hidden Datasheet property so side and mirroring stay right.

usage: sync_pcb_fields.py netlist.xml [board.kicad_pcb]
"""

import re
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

SYNC = ("LCSC", "MPN", "Manufacturer", "Voltage", "Dielectric")
DROP = ("LCSC Part",)


def prop_block_re(name):
    return re.compile(r'^\t\t\(property "%s" .*?^\t\t\)\n' % re.escape(name), re.M | re.S)


def prop_value_re(name):
    return re.compile(r'^(\t\t\(property "%s" )"((?:[^"\\]|\\.)*)"' % re.escape(name), re.M)


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main():
    netlist = sys.argv[1]
    board = Path(sys.argv[2] if len(sys.argv) > 2 else "fast-computer-condom.kicad_pcb")
    comps = {}
    for c in ET.parse(netlist).iter("comp"):
        fields = {f.get("name"): f.text or "" for f in c.iter("field")}
        fields["Value"] = c.findtext("value")
        comps[c.get("ref")] = fields

    text = board.read_text()
    out, pos, changes = [], 0, []
    for m in re.finditer(r"^\t\(footprint .*?^\t\)\n", text, re.M | re.S):
        out.append(text[pos: m.start()])
        pos = m.end()
        fp = m.group(0)
        ref = prop_value_re("Reference").search(fp).group(2)
        fields = comps.get(ref)
        if fields is None:
            out.append(fp)
            continue
        for name in DROP:
            if prop_block_re(name).search(fp):
                fp = prop_block_re(name).sub("", fp)
                changes.append(f"{ref}: drop {name}")
        for name in ("Value",) + SYNC:
            if name not in fields:
                continue
            want = esc(fields[name])
            vm = prop_value_re(name).search(fp)
            if vm:
                if vm.group(2) != want:
                    changes.append(f"{ref}: {name} {vm.group(2)!r} -> {want!r}")
                    fp = fp[: vm.start(2)] + want + fp[vm.end(2):]
                continue
            template = prop_block_re("Datasheet").search(fp).group(0)
            new = prop_value_re("Datasheet").sub(lambda _: f'\t\t(property "{name}" "{want}"', template, count=1)
            new = re.sub(r'\(uuid "[^"]+"\)', f'(uuid "{uuid.uuid4()}")', new, count=1)
            # Insert after the last existing property.
            last = list(re.finditer(r"^\t\t\(property \".*?^\t\t\)\n", fp, re.M | re.S))[-1]
            fp = fp[: last.end()] + new + fp[last.end():]
            changes.append(f"{ref}: add {name}={want!r}")
        out.append(fp)
    out.append(text[pos:])
    new_text = "".join(out)
    if new_text != text:
        board.write_text(new_text)
    print("\n".join(changes))
    print(f"{len(changes)} changes")


if __name__ == "__main__":
    main()
