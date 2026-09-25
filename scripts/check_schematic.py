"""Check exported schematic connectivity: python3 scripts/check_schematic.py NETLIST.xml."""
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
components = {c.get('ref'): c for c in root.findall('./components/comp')}
nets = {(p.get('ref'), p.get('pin')): n.get('name')
        for n in root.findall('./nets/net') for p in n.findall('node')}
checks = 0

def net(ref, pin):
    return nets[ref, str(pin)]

def same(*pins):
    global checks
    assert len({net(*p) for p in pins}) == 1, pins
    checks += 1

def different(*pins):
    global checks
    assert len({net(*p) for p in pins}) == len(pins), pins
    checks += 1

def value(ref, expected):
    global checks
    assert components[ref].findtext('value') == expected, ref
    checks += 1

same(('J2', 'A5'), ('R38', 1), ('U4', 28))
same(('J2', 'B5'), ('R39', 1), ('U4', 1))
same(('R38', 2), ('R39', 2), ('U4', 29))
for r in ['R38', 'R39']: value(r, '5.1kR')
for pins in [(1, 2, 5, 13), (16, 24, 27, 28)]:
    same(*(('U16', p) for p in pins))
same(('U16', 1), ('U3', 5))
same(('U16', 28), ('U5', 5))
different(('U16', 1), ('U16', 28), ('U16', 3), ('U16', 17))
same(('U24', 1), ('U24', 2), ('U24', 4), ('F2', 2), ('C53', 1))
same(('U24', 7), ('U24', 8), ('U5', 1), ('U5', 3))
different(('U24', 1), ('U24', 7), ('U5', 5))
same(('U24', 3), ('R40', 2), ('C54', 1))
same(('U24', 6), ('C52', 1))
same(('U4', 21), ('U7', 18))
same(('U4', 22), ('U7', 17))
same(('U4', 5), ('U7', 21), ('R17', 1))
same(('U4', 6), ('U7', 22))
assert net('U4', 4).startswith('unconnected-')
assert net('J3', 3).startswith('unconnected-')
value('R17', '6.8kR')
for i,(ch,j,mux,esd,fuse,cin,cout,command) in enumerate([
    ('U8','J5','U20','U10','F3','C30','C31',13),
    ('U9','J7','U21','U13','F4','C32','C35',15),
    ('U11','J9','U22','U14','F5','C36','C38',16),
    ('U12','J11','U23','U15','F6','C39','C41',14),
]):
    value(f'R{5+i}','100kR')
    i = [0, 2, 1, 3][i]
    cc,gate=f'U{25+i}',f'U{29+i}'
    same((cc,1),(j,'A5'))
    same((cc,2),(j,'B5'))
    different((cc,1),(cc,2))
    same((cc,9),(gate,1),(f'R{41+i}',2))
    same((gate,2),('U4',command))
    same((gate,4),(ch,4),(mux,6),(f'R{53+i}',2))
    different((gate,1),(gate,2),(gate,4))
    same((cc,3),(cc,12),(gate,5),('U5',5))
    same((cc,10),(cc,11),(gate,3),('U4',29))
    assert net(cc,5).startswith('unconnected-')
    same((ch,6),(cin,1),('U24',8),(f'R{53+i}',1))
    same((ch,1),(fuse,2))
    same((fuse,1),(j,'A4'),(cc,4),(cout,1),(esd,5))
    different((ch,6),(ch,1),(fuse,1))
    # Layout pin swap: the mux and ESD channels are used crossed (D+ on D-/D1- and I/O1)
    # so every hub pair reaches the connector without a polarity twist.
    same((j,'A6'),(j,'B6'),(mux,2),(esd,1),(esd,6))
    same((j,'A7'),(j,'B7'),(mux,1),(esd,3),(esd,4))
    assert net(mux,7).endswith('/D+') and net(mux,8).endswith('/D-'), (net(mux,7), net(mux,8))
    value(cin,'22uF')
    value(cout,'47uF')
assert not any(r.startswith('FB') for r in components)
assert not any(f'R{n}' in components for n in range(9,17))
print(f'PASS: {checks} connectivity/value checks; {len(components)} components, '
      f'{len(root.findall("./nets/net"))} nets. Software I2C and isolation preserved.')
