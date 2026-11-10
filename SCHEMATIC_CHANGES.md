BOM and fabrication review, revision B-pcb — 2026-09-25

Every placed part now has an LCSC, MPN and Manufacturer field, checked against the JLCPCB catalogue on 2026-09-25. `scripts/apply_bom.py` writes them into the schematics. `scripts/sync_pcb_fields.py` copies them onto the footprints as text edits, because a pcbnew Python save drops the placement rule areas and a track segment. The netlist is unchanged apart from the F3–F6 values and the removal of H5. KiCad 10.0.6 results:
- ERC: 0 violations.
- DRC: 0 unconnected items and 0 parity issues. Two silk text warnings remain (below).
- `scripts/check_schematic.py`: 92 checks pass.

| Change | Detail |
| --- | --- |
| Wrong LCSC codes | C13585 (10uF/50V) was on the 22uF parts. C52923 (1uF) was on the 4.7uF and 30pF parts. C25905 (5.1kR) was on the 1kR parts. C22374900 (4A hold) was on the "500mA" fuses. All are replaced. |
| Capacitors | 4.7uF: Murata GRM188Z71C475KE21D, 16V X7R (≥2uF at 1.8V). 22uF CH217 VIN: GRM31CZ71C226ME15L, 16V X7R (about 13uF at 5V). 47uF port bulk: GRM31CR61E476ME44L, 25V **X5R**; no 1206 47uF X7R exists. C52 CT: GRM1555C1H103JE01D C0G. The other 10nF parts are 50V X7R. The Voltage/Dielectric fields match the parts. |
| F3–F6 | 500mA → **750mA** hold (Bourns MF-MSMF075/24-2, 1.5A trip, R1max 450mΩ). A 500mA-hold PTC under a 500mA port load runs at its hold limit and derates below it when warm. Its 1Ω R1max would also drop up to 0.5V of VBUS. The CH217 at about 600mA remains the primary limit. |
| F1, F2 | F1: LUTE 0805L100/16AR, 1A hold. F2: LUTE 0805L300SL12ARGW, 3A hold, 12V. The previous F2 was a 2.6A part with 13 in stock. |
| LEDs | XINGLIGHT XL-1608SYGC-06, 575nm, Vf 2.2V. An InGaN green at Vf ≈3V would barely light from 3.3V through 1kR. This part gives about 1mA. |
| Crystal | YXC X322525MMB4SI, 25MHz, 10pF load, matching the symbol value. |
| H5 | Removed. The reroute left it at (2.175, 2.175), about 125mm off the board, as a plated 2.2mm hole in the drill file and every copper layer. H1–H4 remain. |

Stackup as routed: F, In1, In2 and B carry the host GND pours. GND2 is on all six layers, and a VBUS_ISO pour is on In2. There are no 3V3 planes. In3 and In4 are empty in the host region. Host-side B.Cu carries power only, and the host USB pair is on F.Cu over solid In1 GND. Outer pairs are 0.15/0.15mm over 0.1mm prepreg (Er 4.5): IPC-2141 gives about 89Ω differential, or about 86Ω with mask. Order a 6-layer stackup with about 0.1mm outer prepreg, or recheck the impedance against the fab's stackup.

Before ordering
- **U7 CH338F (C42387425) has 0 JLCPCB stock.** Consign it or pre-order it; everything else is stocked.
- The JLCPCB BOM also lists JP1–4, TP10–16, H1–4 and J3 without LCSC codes (the preset includes excluded-from-BOM parts). Leave them unmatched.
- `-> power input` and `<- to computer` use TrueType Berkeley Mono. Some glyph strokes fall below the 0.08mm silk minimum, so `kicad-build` still reports failure. Switch them to the KiCad font or enlarge them if crisp legends matter.
- JP1–JP4 use the Bridged12 footprint (EQ strapped to ground by copper), but their value still reads `Jumper_3_Open`.
- U25–U28 (WUSB3801) have no 3D model. The U24 model path points to a KiCad library model that is not installed here.
- Mounting holes are floating plated rings. The copper gap is 1.8mm from H2 to host GND and 2.9mm from H1 to GND2. A metal chassis across H1–H4 therefore cuts the effective isolation creepage to about 4.7mm. Use insulating standoffs if the 6.25mm board spacing is the requirement.
- Check the JLC placement preview for rotation offsets on the easyeda2kicad and fcc footprints (U16, U20–U28).

PCB layout, revision B-pcb — 2026-09-23

The PCB is synchronized with the schematic, fully placed and routed. KiCad 10.0.6 DRC with schematic parity: 0 errors, 0 unconnected items, 0 parity issues. Five warnings remain: library-footprint mismatches on U16/U20 (pre-existing) and U7/U8 (rotation rounding in graphics only), and the logo's TrueType stroke width.

| Change | Detail |
| --- | --- |
| Solder jumpers | JP1–JP4 (ISOUSB211 EQ straps) had no footprint. They now use `Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm`. |
| USB channel swap | In `sch/USB_Output.kicad_sch`, hub D+ enters TS3USB221 pin 7 and leaves on pin 2, then uses USBLC6 I/O1. D- uses pin 8, pin 1 and I/O2. The switch and ESD channels are identical, so the signal path is unchanged. Every hub pair then reaches its connector without a polarity twist. `scripts/check_schematic.py` asserts the new mapping. |
| Stackup | *Superseded by the reroute, see the 2026-09-25 entry.* F: signals and GND pour. In1/In4: solid GND (host) and GND2 (isolated) planes. In2: inner signals and GND2 fill. In3: +3V3_ISO/+3V3 planes plus a VBUS_ISO pour from the TPS22975 output down the CH217 input column. B: USB pairs and GND pour. |
| USB routing | 90 ohm pairs (0.15/0.15 mm) on outer layers over solid ground, with paired via transitions. USB-C D+/D- orientation links sit behind the pad row. USBLC6 devices are routed flow-through. The CH32X035 full-speed pair is routed as two single-ended traces. |
| Isolation | At least 6.25 mm copper-to-copper between the host and isolated domains on every layer. No copper crosses the slot or the bridges. |
| Placement | J5/J9 port groups swapped physical slots so the hub's port pairs don't cross; connector-to-sheet mapping is unchanged. The H5 exposed-mask ring shrank from r3.5 to r3.0 mm. The logo text moved to the back silkscreen, clear of the J3 Tag-Connect holes. Reference designators that can't fit legibly are on the Fab layers. |
| Rules | Default clearance 0.15 mm, signal width 0.127 mm, Power net class for VBUS nets, vias 0.45/0.2 mm (signals) and 0.6/0.3 mm (power). |

Before ordering, check the USB pair impedance against the fab's actual stackup and review the soldermask/silk renders. The layout scripts are in `build/layout/tools/` (not tracked by Git).

Layout update — 2026-09-05

Reorganized the root into functional blocks, rewired local bypass and strap connections for readability, separated status indicators, corrected field placement, and renamed the local CC labels to AUX_CC1/2 and PORT_CC1/2. All 159 net memberships, component UUIDs, and symbol pin number/name pairs are preserved. ERC remains at zero violations and the 92 connectivity checks pass. Latest [schematic PDF](build/schematic-layout/schematic.pdf), [validation](build/schematic-layout/layout-validation.txt), and [renders](build/schematic-layout/).

Schematic fixes, revision B-sch — 2026-09-05

The root schematic and all four instances of `sch/USB_Output.kicad_sch` have been updated. Software I²C on PB10/PB11 is deliberate and retained. The PCB has not been synchronized or routed for these changes.

| Change | Implementation |
| --- | --- |
| Auxiliary USB-C input | R38/R39: independent 5.1kR, 1% CC pulldowns. J2 remains a 5 V sink. |
| Isolator supply | U16 VBUS, V3P3V and VCC pins use the corresponding external 3.3 V rail; internal and external 3.3 V regulators are no longer paralleled. |
| Isolator bypass | Each physical 1.8 V pin (4, 11, 18, 25) gets 4.7uF + 100nF + 10nF. Select the 4.7uF parts for at least 2uF effective capacitance at 1.8 V and place each bank at its pin. |
| Output attachment | Four WUSB3801Q-12/TR controllers, 1.6 × 1.6 mm, in source/pin-control mode with default-current advertisement. Their internal CC terminations replace R9–R16. These are attachment detectors, not USB-PD controllers. |
| Output gating | SN74LVC1G32DBVR combines active-low attachment and MCU enable. Either condition going high disables both CH217 power and TS3USB221 data. A 100kR pullup to 5 V keeps the disable net high before 3.3 V starts; the selected gate supports partial-power-down isolation. |
| Port supply | R5–R8 become 100kR, 1%, approximately 600mA nominal limiting for 500mA loads. Each CH217 gets 22uF/16V X7R at VIN, selected for at least 10uF effective at 5 V. The 47uF output cap is after the fuse. FB1–FB4 are removed. |
| Input startup | U24 TPS22975DSGR, 2 × 2 mm, supplies all isolated electronics and bulk through a controlled ramp. CT=10nF/50V C0G gives about 17ms nominal rise; 100kR/100nF delays ON. Only the small raw-input bypass remains ahead of it. |
| Host-side input | C1 reduced to 1uF; C5 remains 1uF. |
| MCU/debug | Removed the false reset connection from J3.3 to QFN28 PC3. WCH DIO/DCK remain connected. |
| Hub | R17=6.8kR improves the reset-time PD-disable strap margin. U7 PWREN_N reaches PA0; PA1 reaches OVCUR for firmware-driven open-drain reporting. |
| Libraries/ERC | Corrected power and open-drain pin metadata, refreshed cached capacitor symbols, removed stale ERC exclusions, and added local support-part symbols and footprints. Imported symbol pin numbers/names were preserved. |

Firmware interface (firmware is not present or implemented in this repository)

- Keep all port enable commands high during initialization and whenever power is unavailable. A low command permits power only while the CC detector also reports an attached sink. Detach disables the output independently of firmware.
- Read J2 CC1/CC2 on U4 pins 28/1 to determine the available Type-C input current. Reserve the hub, MCU, isolator and controller consumption before allocating port loads. Do not assume four 500mA ports are available with a default-current source.
- PB0/pin13 controls port 1 (J5); PB1/pin16 controls port 2 (J9); PB3/pin14 controls port 3 (J11); PB4/pin15 controls port 4 (J7). High disables. Faults are PB6–PB9/pins17–20 respectively, active low.
- PA0/pin5 reads the hub's active-low ganged power request. PA1/pin6 must be open drain: pull low to report overcurrent and release otherwise. Coordinate host requests, port faults, and the current budget. Verify hub descriptors and ganged-power behavior on hardware.
- PB10/pin21 is software SCL; PB11/pin22 is software SDA. Preserve open-drain operation. PB5/pin12 remains hub reset. MCU recovery uses WCH-Link DIO/DCK and the appropriate power-cycle procedure; J3 pin 3 is unused.

Validation

KiCad 10.0.6 ERC: **0 errors, 0 warnings**, with all severities enabled and no exclusions. The exported netlist has 167 components and 159 nets. `scripts/check_schematic.py` passes 92 connectivity/value checks covering input termination, isolated supplies, controller straps, all four output gates, data wiring, fuse/bypass placement, and MCU signals.

Rendered sheets were inspected and revised repeatedly. Evidence: [PDF](build/schematic-fixes/schematic.pdf), [ERC](build/schematic-fixes/erc.json), [netlist](build/schematic-fixes/netlist.xml), [connectivity result](build/schematic-fixes/connectivity.txt), and SVG/PNG renders under `build/schematic-fixes/`. Build outputs are ignored by Git.

The WUSB footprint uses the manufacturer's page-16 land pattern: 0.4mm pitch, four 0.8 × 0.2mm side pads, eight 0.2 × 0.6mm top/bottom pads, 2.2mm overall copper span. An imported drilled-pad defect was removed. The TPS footprint uses KiCad's standard DSG0008A copper and segmented exposed-pad paste. KLC checks remain advisory: small reference text, shared standard 3D-model naming, and segmented-paste checks are not electrical validation; WUSB has no supplied 3D model.

Before fabrication, synchronize and route the PCB, verify local bypass placement, isolation clearance and USB impedance, and select exact capacitors/fuses against effective capacitance, hold/trip current and temperature. Bench-check startup/inrush, both cable orientations, attach/detach and VBUS discharge, 500mA load margin across temperature, short-circuit recovery, and host-visible power/fault handling. The CH217 nominal current formula does not guarantee a precise 500mA cutoff, and the generic 500mA fuse labels are not procurement qualification.

Design references: [TI ISOUSB211](https://www.ti.com/lit/ds/symlink/isousb211.pdf), [WUSB3801](https://www.visvie.com/static/upload/file/20220929/1664435923629881.pdf), [TI TPS22975](https://www.ti.com/lit/ds/symlink/tps22975.pdf), [TI SN74LVC1G32](https://www.ti.com/lit/ds/symlink/sn74lvc1g32.pdf), [WCH CH217 v1.3](https://atta.szlcsc.com/upload/public/pdf/source/20260518/11202443994CC8E8AD111F5D5C5E697B.pdf), [WCH CH338 v1.2](https://atta.szlcsc.com/upload/public/pdf/source/20250604/33B7EB63DA58DDDA601A5A5911A2B220.pdf).
