"""Original, dependency-free schematic document and linear SPICE-like transient solver.

Not an NI file parser or a replacement for a production SPICE engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
import json
import math
from pathlib import Path

GRID = 20
PINS = {
    'NJF':[(20,-40),(-40,0),(20,40)], 'PJF':[(20,-40),(-40,0),(20,40)],
    'NMOS':[(20,-40),(-40,0),(20,40),(40,0)], 'PMOS':[(20,-40),(-40,0),(20,40),(40,0)],
    'IGBT':[(20,-40),(-40,0),(20,40)],
    'SCR':[(0,-40),(-40,20),(0,40)], 'TRIAC':[(0,-40),(-40,20),(0,40)],
    'IPROBE':[(-40,0),(40,0)],'DIAC':[(-40,0),(40,0)], 'I':[(0,-40),(0,40)], 'POT':[(-40,0),(40,0),(0,40)],
    'NPN':[(20,-40),(-40,0),(20,40)], 'PNP':[(20,-40),(-40,0),(20,40)],
    'OPAMP':[(-60,-20),(-60,20),(0,-60),(0,60),(60,0)],
    'R': [(-40, 0), (40, 0)], 'C': [(-40, 0), (40, 0)],
    'L': [(-40, 0), (40, 0)], 'V': [(0, -40), (0, 40)],
    'NET':[(0,0)], 'GND': [(0, -20)], 'D': [(-40, 0), (40, 0)],
    'LED': [(-40, 0), (40, 0)], 'SW': [(-40, 0), (40, 0)],
}
PIN_LABELS={'NPN':'C / B / E','PNP':'C / B / E','NJF':'D / G / S','PJF':'D / G / S',
    'NMOS':'D / G / S / B','PMOS':'D / G / S / B','IGBT':'C / G / E','SCR':'A / G / K','TRIAC':'MT2 / G / MT1',
    'DIAC':'MT2 / MT1','OPAMP':'+ / − / VCC / VEE / OUT','POT':'A / B / Wiper','I':'+ / −','GND':'Reference'}
DEFAULTS = {'IPROBE':('Current probe',''),'NET':('net1',''),'NJF':('Course_NJF',''),'PJF':('Course_PJF',''),'NMOS':('Course_NMOS',''),'PMOS':('Course_PMOS',''),
            'IGBT':('Course_IGBT',''),'SCR':('2N1595',''),'DIAC':('DB3',''),'TRIAC':('L6008L6',''),
            'I':('1m','A'),'POT':('10k:0.5',''),'NPN':('BC547B',''), 'PNP':('BC557B',''), 'OPAMP':('LM358',''),'R': ('1k', 'Ω'), 'C': ('1u', 'F'), 'L': ('10m', 'H'),
            'V': ('5', 'V'), 'GND': ('', ''), 'D': ('1N4148', ''),
            'LED': ('Red', ''), 'SW': ('Open', '')}
PREFIX = {'f':1e-15, 'a':1e-18, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6,
          'm': 1e-3, 'k': 1e3, 'K': 1e3, 'M': 1e6, 'G': 1e9}

def numeric(value: str) -> float:
    s = str(value).strip().replace('Ω', '').replace('ohm', '').replace('Ohm', '')
    if not s: raise ValueError('Missing numeric value')
    try: return float(s)
    except ValueError: pass
    for suffix in ('meg', 'MEG'):
        if s.endswith(suffix): return float(s[:-len(suffix)]) * 1e6
    if s[-1] in PREFIX: return float(s[:-1]) * PREFIX[s[-1]]
    raise ValueError(f'Invalid engineering value: {value}')

def snap(v): return round(v / GRID) * GRID

@dataclass
class Part:
    id: str
    kind: str
    x: float
    y: float
    value: str
    rotation: int = 0

    def pins(self):
        angle = self.rotation % 360
        result = []
        for x, y in PINS[self.kind]:
            if angle == 90: x, y = -y, x
            elif angle == 180: x, y = -x, -y
            elif angle == 270: x, y = y, -x
            result.append((self.x + x, self.y + y))
        return result

@dataclass
class Wire:
    a: tuple[float, float]
    b: tuple[float, float]

    def points(self):
        return [tuple(self.a), tuple(self.b)]

@dataclass
class Document:
    title: str = 'Design1'
    parts: list[Part] = field(default_factory=list)
    wires: list[Wire] = field(default_factory=list)

    def next_name(self, kind):
        taken = {p.id for p in self.parts}
        prefix = {'IPROBE':'PR','NET':'N','GND': 'GND', 'V': 'V', 'R': 'R', 'C': 'C', 'L': 'L',
                  'I':'I','POT':'RP','NJF':'J','PJF':'J','NMOS':'M','PMOS':'M','IGBT':'U','SCR':'U','TRIAC':'U','DIAC':'U',
                  'D': 'D', 'LED': 'LED', 'SW': 'S', 'NPN':'Q', 'PNP':'Q', 'OPAMP':'U'}[kind]
        i = 1
        while f'{prefix}{i}' in taken: i += 1
        return f'{prefix}{i}'

    def add(self, kind, x, y, value=None):
        if kind not in PINS: raise ValueError(f'Unknown part type: {kind}')
        part = Part(self.next_name(kind), kind, snap(x), snap(y),
                    DEFAULTS[kind][0] if value is None else value)
        self.parts.append(part)
        return part

    def add_wire(self, a, b):
        a, b = (snap(a[0]), snap(a[1])), (snap(b[0]), snap(b[1]))
        if a == b: return None
        if any((w.a == a and w.b == b) or (w.a == b and w.b == a) for w in self.wires):
            return None
        wire = Wire(a, b)
        self.wires.append(wire)
        return wire

    def to_dict(self):
        return {'format': 'open-circuit-workbench', 'version': 1,
                'title': self.title, 'parts': [asdict(p) for p in self.parts],
                'wires': [asdict(w) for w in self.wires]}

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding='utf-8')

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('format') != 'open-circuit-workbench' or data.get('version') != 1:
            raise ValueError('Unsupported project format')
        parts = []
        for p in data.get('parts', []):
            if p['kind'] not in PINS or int(p['rotation']) % 90:
                raise ValueError('Invalid component')
            if p['kind']=='NET':
                import re
                if not re.fullmatch(r'(?:[A-Za-z_][A-Za-z0-9_]*|0)',p['value']):raise ValueError('Invalid net alias')
            parts.append(Part(**p))
        wires = []
        for w in data.get('wires', []):
            if len(w['a']) != 2 or len(w['b']) != 2: raise ValueError('Invalid wire')
            wires.append(Wire(tuple(w['a']), tuple(w['b'])))
        if len({p.id for p in parts}) != len(parts): raise ValueError('Duplicate part IDs')
        return cls(str(data.get('title', 'Design1')), parts, wires)

    def netlist(self):
        """Generate a basic ngspice circuit for linear components only.

        All component pins must connect to a named network through wires.
        """
        nets = self.networks()
        if not any(p.kind == 'GND' for p in self.parts):
            raise ValueError('Place a ground reference before exporting the netlist.')
        out = ['* Open Circuit Workbench - generated linear circuit', self.title]
        # The SPICE first line is a title: use only the first line above as title.
        out = ['Open Circuit Workbench: ' + self.title]
        for p in self.parts:
            if p.kind == 'GND': continue
            if p.kind not in ('R', 'C', 'L', 'V'):
                raise ValueError(f'Netlist export for {p.kind} is not supported yet')
            a, b = [nets[(p.id, i)] for i in (0, 1)]
            if a == b: raise ValueError(f'Shorted component {p.id}')
            value = numeric(p.value)
            if p.kind in ('R', 'C', 'L') and value <= 0:
                raise ValueError(f'{p.id} requires a positive value')
            out.append(f'{p.id} {a} {b} ' + (f'DC {value:g}' if p.kind == 'V' else f'{value:g}'))
        out.extend(['.tran 10u 20m', '.end'])
        return '\n'.join(out) + '\n'

    def networks(self):
        """Union pins and wire endpoints with geometrical connectivity.

        Orthogonal wire segments join at common endpoints, at pins lying on a
        segment, and at T-junctions where at least one segment ends. Mere
        wire crossings do not connect unless one of the segments ends there.
        """
        parent = {}
        def find(x):
            parent.setdefault(x, x)
            if parent[x] != x: parent[x] = find(parent[x])
            return parent[x]
        def union(a, b):
            aa, bb = find(a), find(b)
            if aa != bb: parent[bb] = aa
        coords = {}
        for part in self.parts:
            for i, xy in enumerate(part.pins()):
                key = (part.id, i)
                coords[key] = xy
                union(key, ('xy', *xy))
        # Same-name net aliases join electrically across the worksheet.
        import re
        for part in self.parts:
            if part.kind=='NET':
                if not re.fullmatch(r'(?:[A-Za-z_][A-Za-z0-9_]*|0)',part.value):raise ValueError('Net alias must be a name or 0')
                union((part.id,0),('net',part.value))
            elif part.kind=='GND':union((part.id,0),('net','0'))
        segs = []
        for wi, wire in enumerate(self.wires):
            a, b = wire.a, wire.b
            # UI creates right-angle elbows for non-axis-aligned endpoints.
            route = [a, (b[0], a[1]), b] if a[0] != b[0] and a[1] != b[1] else [a, b]
            for j in range(len(route)-1):
                a, b = route[j], route[j+1]
                if a == b: continue
                segs.append((a, b))
                union(('xy', *a), ('xy', *b))
        def on_segment(pt, a, b):
            return ((a[0] == b[0] == pt[0] and min(a[1],b[1]) <= pt[1] <= max(a[1],b[1])) or
                    (a[1] == b[1] == pt[1] and min(a[0],b[0]) <= pt[0] <= max(a[0],b[0])))
        # Pins/segment endpoints sitting anywhere on a segment are connections.
        contact_points = list(coords.values()) + [point for pair in segs for point in pair]
        for pt in contact_points:
            for a,b in segs:
                if on_segment(pt,a,b): union(('xy', *pt), ('xy', *a))
        # Coordinate indexing for stable numbered networks.
        grounded = {find((p.id, 0)) for p in self.parts if p.kind == 'GND'}
        mapping, count = {}, 1
        networks = {}
        for part in self.parts:
            for i in range(len(part.pins())):
                root = find((part.id, i))
                if root in grounded: network = '0'
                else:
                    if root not in mapping:
                        mapping[root] = str(count); count += 1
                    network = mapping[root]
                networks[(part.id, i)] = network
        return networks


def solve_linear_system(matrix, vector):
    """Gaussian elimination with partial pivoting, no optional dependencies."""
    n = len(vector)
    if n == 0: return []
    a = [list(row) + [vector[i]] for i,row in enumerate(matrix)]
    for col in range(n):
        k = max(range(col,n), key=lambda r: abs(a[r][col]))
        if abs(a[k][col]) < 1e-14:
            raise ValueError('Circuit has a floating node or a singular network. Check wires and ground.')
        a[k],a[col] = a[col],a[k]
        pivot = a[col][col]
        for j in range(col,n+1): a[col][j] /= pivot
        for i in range(n):
            if i == col: continue
            f = a[i][col]
            if f:
                for j in range(col,n+1): a[i][j] -= f*a[col][j]
    return [a[i][n] for i in range(n)]


def simulate(doc: Document, duration=.012, steps=240):
    """Backward-Euler transient for independent DC sources + R, C, L.

    Designed for educational small circuits. For robust nonlinear/large
    circuits, choose the existing Qucs-S/ngspice backend instead.
    """
    if not 1 <= steps <= 5000 or duration <= 0: raise ValueError('Invalid simulation range')
    if not any(p.kind == 'GND' for p in doc.parts):
        raise ValueError('A ground component is required.')
    if any(p.kind not in ('GND','R','C','V','L') for p in doc.parts):
        raise ValueError('Transient simulation currently supports R, C, L and DC voltage sources.')
    nets = doc.networks()
    nodes = sorted({v for v in nets.values() if v != '0'}, key=int)
    ix = {node:i for i,node in enumerate(nodes)}
    sources = [p for p in doc.parts if p.kind == 'V']
    capacitors = [p for p in doc.parts if p.kind == 'C']
    n, total = len(nodes), len(nodes)+len(sources)
    if not sources: raise ValueError('Add a DC voltage source.')
    def idx(pin): return ix.get(pin)
    def stamp_g(mat,a,b,g):
        ai,bi = idx(a),idx(b)
        if ai is not None: mat[ai][ai] += g
        if bi is not None: mat[bi][bi] += g
        if ai is not None and bi is not None:
            mat[ai][bi] -= g; mat[bi][ai] -= g
    def inject(rhs,a,b,value):
        ai,bi = idx(a),idx(b)
        if ai is not None: rhs[ai] += value
        if bi is not None: rhs[bi] -= value
    times, history = [], {'0': []} | {node: [] for node in nodes}
    previous = {node:0.0 for node in nodes} | {'0':0.0}
    dt = duration/steps
    for step in range(steps+1):
        mat = [[0.0]*total for _ in range(total)]
        rhs = [0.0]*total
        for p in doc.parts:
            if p.kind == 'GND': continue
            a,b = nets[(p.id,0)], nets[(p.id,1)]
            if a == b: raise ValueError(f'{p.id} has both pins on the same node')
            if p.kind == 'R':
                v = numeric(p.value)
                if v <= 0: raise ValueError('Resistance must be positive')
                stamp_g(mat,a,b,1/v)
            elif p.kind == 'L':
                # DC approximation only; inductor transient is not implemented.
                raise ValueError('Inductor transient is not available. Use Qucs-S/ngspice.')
            elif p.kind == 'C':
                v = numeric(p.value)
                if v <= 0: raise ValueError('Capacitance must be positive')
                g = v/dt
                stamp_g(mat,a,b,g)
                inject(rhs,a,b,g*(previous.get(a,0)-previous.get(b,0)))
        for k,p in enumerate(sources):
            a,b = nets[(p.id,0)], nets[(p.id,1)]
            ai,bi = idx(a),idx(b)
            slot = n+k
            if ai is not None: mat[ai][slot] += 1; mat[slot][ai] += 1
            if bi is not None: mat[bi][slot] -= 1; mat[slot][bi] -= 1
            rhs[slot] = numeric(p.value)
        solved = solve_linear_system(mat,rhs)
        previous = {'0':0.0} | {node:solved[ix[node]] for node in nodes}
        times.append(step*dt)
        for node in history: history[node].append(previous[node])
    return times, history, nets