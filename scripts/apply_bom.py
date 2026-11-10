#!/usr/bin/env python3
"""Write resolved sourcing fields (LCSC, MPN, Manufacturer) into the schematics.

Parts were resolved against the JLCPCB/LCSC catalogue on 2026-09-25. Rules are
keyed on (reference prefix, Value, footprint size); REF_OVERRIDES handles parts
that share a value but not a part number. Re-running is idempotent.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEETS = [ROOT / "fast-computer-condom.kicad_sch", ROOT / "sch" / "USB_Output.kicad_sch"]

UNIROYAL = "UNI-ROYAL(Uniroyal Elec)"
SAMSUNG = "Samsung Electro-Mechanics"
TI = "Texas Instruments"
WCH = "WCH(Jiangsu Qin Heng)"
HRO = "Korean Hroparts Elec"

# (prefix, value, footprint substring) -> fields
RULES = [
    ("C", "1uF", "0402", dict(LCSC="C52923", MPN="CL05A105KA5NQNC", Manufacturer=SAMSUNG, Voltage="25V", Dielectric="X5R")),
    ("C", "4.7uF", "0603", dict(LCSC="C389010", MPN="GRM188Z71C475KE21D", Manufacturer="Murata Electronics", Voltage="16V", Dielectric="X7R")),
    ("C", "22uF", "1206", dict(LCSC="C909845", MPN="GRM31CZ71C226ME15L", Manufacturer="Murata Electronics", Voltage="16V", Dielectric="X7R")),
    ("C", "47uF", "1206", dict(LCSC="C403725", MPN="GRM31CR61E476ME44L", Manufacturer="Murata Electronics", Voltage="25V", Dielectric="X5R")),
    ("C", "30pF", "0402", dict(LCSC="C1570", MPN="0402CG300J500NT", Manufacturer="FH (Guangdong Fenghua Advanced Tech)", Voltage="50V", Dielectric="C0G")),
    ("C", "100nF", "0402", dict(LCSC="C1525", MPN="CL05B104KO5NNNC", Manufacturer=SAMSUNG, Voltage="16V", Dielectric="X7R")),
    ("C", "10nF", "0402", dict(LCSC="C15195", MPN="CL05B103KB5NNNC", Manufacturer=SAMSUNG, Voltage="50V", Dielectric="X7R")),
    ("R", "1kR", "0402", dict(LCSC="C11702", MPN="0402WGF1001TCE", Manufacturer=UNIROYAL)),
    ("R", "5.1kR", "0402", dict(LCSC="C25905", MPN="0402WGF5101TCE", Manufacturer=UNIROYAL)),
    ("R", "6.8kR", "0402", dict(LCSC="C25917", MPN="0402WGF6801TCE", Manufacturer=UNIROYAL)),
    ("R", "9.1kR", "0402", dict(LCSC="C25926", MPN="0402WGF9101TCE", Manufacturer=UNIROYAL)),
    ("R", "10kR", "0402", dict(LCSC="C25744", MPN="0402WGF1002TCE", Manufacturer=UNIROYAL)),
    ("R", "51kR", "0402", dict(LCSC="C25794", MPN="0402WGF5102TCE", Manufacturer=UNIROYAL)),
    ("R", "100kR", "0402", dict(LCSC="C25741", MPN="0402WGF1003TCE", Manufacturer=UNIROYAL)),
    ("R", "4.7MR", "0402", dict(LCSC="C474132", MPN="0402WGF4704TCE", Manufacturer=UNIROYAL)),
    # 575 nm, Vf 2.2 V: stays visible from 3.3 V through 1 kR (an InGaN green at Vf ~3 V would barely light).
    ("D", "GREEN", "0603", dict(LCSC="C965805", MPN="XL-1608SYGC-06", Manufacturer="XINGLIGHT")),
    ("F", "1A", "0805", dict(LCSC="C22363531", MPN="0805L100/16AR", Manufacturer="LUTE")),
    ("F", "3A", "0805", dict(LCSC="C55471900", MPN="0805L300SL12ARGW", Manufacturer="LUTE")),
    ("F", "750mA", "1812", dict(LCSC="C208467", MPN="MF-MSMF075/24-2", Manufacturer="Bourns")),
    ("Y", "25M, 10pF", "3225", dict(LCSC="C70582", MPN="X322525MMB4SI", Manufacturer="YXC Crystal Oscillators")),
    ("U", "AP2112K-3.3", "SOT-23-5", dict(LCSC="C51118", MPN="AP2112K-3.3TRG1", Manufacturer="Diodes Incorporated")),
    ("U", "CH217A", "SOT-23-6", dict(LCSC="C54973763", MPN="CH217A", Manufacturer=WCH)),
    ("U", "CH338F", "QFN-32", dict(LCSC="C42387425", MPN="CH338F", Manufacturer=WCH)),
    ("U", "CH32X035G8U6", "QFN-28", dict(LCSC="C7437027", MPN="CH32X035G8U6", Manufacturer=WCH)),
    ("U", "ISOUSB211DPR", "SSOP-28", dict(LCSC="C5772877", MPN="ISOUSB211DPR", Manufacturer=TI)),
    ("U", "TS3USB221ERSER", "UQFN-10", dict(LCSC="C129313", MPN="TS3USB221ERSER", Manufacturer=TI)),
    ("U", "TPS22975DSGR", "WSON-8", dict(LCSC="C524777", MPN="TPS22975DSGR", Manufacturer=TI)),
    ("U", "WUSB3801Q-12/TR", "QFN-12", dict(LCSC="C2931342", MPN="WUSB3801Q-12/TR", Manufacturer="WILLSEMI(Will Semicon)")),
    ("U", "SN74LVC1G32DBVR", "SOT-23-5", dict(LCSC="C10096", MPN="SN74LVC1G32DBVR", Manufacturer=TI)),
    ("U", "USBLC6-2SC6", "SOT-23-6", dict(LCSC="C7519", MPN="USBLC6-2SC6", Manufacturer="STMicroelectronics")),
    ("J", "USB-C / HOST", "TYPE-C-31-M-12", dict(LCSC="C165948", MPN="TYPE-C-31-M-12", Manufacturer=HRO)),
    ("J", "USB-C / USB 2.0", "TYPE-C-31-M-12", dict(LCSC="C165948", MPN="TYPE-C-31-M-12", Manufacturer=HRO)),
    ("J", "USB-C / AUX POWER", "TYPE-C-31-M-17", dict(LCSC="C283540", MPN="TYPE-C-31-M-17", Manufacturer=HRO)),
]

REF_OVERRIDES = {
    # TPS22975 CT ramp capacitor: C0G so the startup slew does not move with bias/temperature.
    "C52": dict(LCSC="C22400107", MPN="GRM1555C1H103JE01D", Manufacturer="Murata Electronics", Voltage="50V", Dielectric="C0G"),
}

# Old per-part ordering fields superseded by LCSC.
DROP = {"LCSC Part"}

# Value corrections applied before rule matching.
# F3-F6: a 500 mA-hold PTC under a 500 mA port load sits at its hold limit (and derates below it
# when warm) and drops up to 0.5 V (R1max 1 ohm). CH217 R5-R8 already limit ~600 mA; the PTC is a
# backup, so 750 mA hold / 1.5 A trip / 450 mohm R1max is used.
VALUE_FIXES = {("F", "500mA"): "750mA"}


def prop_re(name):
    return re.compile(r'^(\t\t\(property "%s" )"((?:[^"\\]|\\.)*)"' % re.escape(name), re.M)


def get_prop(block, name):
    m = prop_re(name).search(block)
    return m.group(2) if m else None


def set_prop(block, name, value):
    m = prop_re(name).search(block)
    if m:
        return block[: m.start(2)] + value + block[m.end(2):]
    # Insert a hidden property modelled on the Datasheet property's placement.
    anchor = re.search(r'^\t\t\(property "Datasheet" .*?\n\t\t\)\n', block, re.M | re.S)
    at = re.search(r"\(at [^)]*\)", anchor.group(0)).group(0)
    new = (
        f'\t\t(property "{name}" "{value}"\n\t\t\t{at}\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n'
        "\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
        "\t\t\t\t)\n\t\t\t)\n\t\t)\n"
    )
    return block[: anchor.end()] + new + block[anchor.end():]


def drop_prop(block, name):
    return re.sub(r'^\t\t\(property "%s" .*?\n\t\t\)\n' % re.escape(name), "", block, flags=re.M | re.S)


def refs_of(block):
    refs = set(re.findall(r'\(reference "([^"]+)"\)', block))
    ref = get_prop(block, "Reference")
    if ref:
        refs.add(ref)
    return refs


def process(text, log):
    out, pos = [], 0
    for m in re.finditer(r"^\t\(symbol\n.*?^\t\)\n", text, re.M | re.S):
        out.append(text[pos: m.start()])
        block = m.group(0)
        pos = m.end()
        refs = refs_of(block)
        ref = sorted(refs)[0] if refs else ""
        if ref.startswith("#") or "(in_bom no)" in block:
            out.append(block)
            continue
        prefix = re.match(r"[A-Z]+", ref).group(0)
        value = get_prop(block, "Value")
        fp = get_prop(block, "Footprint") or ""
        fixed = VALUE_FIXES.get((prefix, value))
        if fixed:
            block = set_prop(block, "Value", fixed)
            log.append(f"{','.join(sorted(refs))}: Value {value} -> {fixed}")
            value = fixed
        fields = None
        overrides = [REF_OVERRIDES[r] for r in refs if r in REF_OVERRIDES]
        if overrides:
            fields = overrides[0]
        else:
            for p, v, f, flds in RULES:
                if p == prefix and v == value and f in fp:
                    fields = flds
                    break
        if fields is None:
            log.append(f"UNRESOLVED {','.join(sorted(refs))} {value} {fp}")
            out.append(block)
            continue
        for name in DROP:
            block = drop_prop(block, name)
        for name, val in fields.items():
            block = set_prop(block, name, val)
        out.append(block)
    out.append(text[pos:])
    return "".join(out)


def main():
    log = []
    for path in SHEETS:
        text = path.read_text()
        new = process(text, log)
        if new != text:
            path.write_text(new)
            log.append(f"wrote {path.relative_to(ROOT)}")
    print("\n".join(log))
    return 1 if any(l.startswith("UNRESOLVED") for l in log) else 0


if __name__ == "__main__":
    sys.exit(main())
