"""
Vertex and edge data for 35 polyhedra across 4 families.
Each builder returns (verts, edges, nV, nE, nF).
"""

import math

PHI = (1 + math.sqrt(5)) / 2
IP = 1 / PHI  # 1/phi = phi - 1


def _normalize(verts):
    """Normalize vertices to lie on unit sphere."""
    result = []
    for v in verts:
        length = math.sqrt(sum(c * c for c in v))
        if length > 0:
            result.append(tuple(c / length for c in v))
        else:
            result.append(v)
    return result


def _scale_to_unit(verts):
    """Scale all vertices so max radius is 1 (preserves relative radii)."""
    max_r = max(math.sqrt(sum(c * c for c in v)) for v in verts)
    if max_r > 0:
        return [tuple(c / max_r for c in v) for v in verts]
    return verts


def _dedup(verts, tol=1e-6):
    """Remove duplicate vertices."""
    unique = []
    for v in verts:
        found = False
        for u in unique:
            if all(abs(a - b) < tol for a, b in zip(v, u)):
                found = True
                break
        if not found:
            unique.append(v)
    return unique


def _edges_by_dist(verts, threshold):
    """Build edges by connecting vertices within threshold distance."""
    edges = []
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            dx = verts[i][0] - verts[j][0]
            dy = verts[i][1] - verts[j][1]
            dz = verts[i][2] - verts[j][2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if dist < threshold:
                edges.append((i, j))
    return edges


def _edges_by_count(verts, target):
    """Take the target shortest edges. Works for any vertex construction."""
    pairs = []
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            dx = verts[i][0] - verts[j][0]
            dy = verts[i][1] - verts[j][1]
            dz = verts[i][2] - verts[j][2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            pairs.append((dist, i, j))
    pairs.sort()
    return [(i, j) for _, i, j in pairs[:target]]


def _all_sign_perms(base):
    """All sign permutations of (a,b,c): up to 8 variants."""
    results = set()
    a, b, c = base
    for sa in (1, -1):
        for sb in (1, -1):
            for sc in (1, -1):
                results.add((sa * a, sb * b, sc * c))
    return list(results)


def _all_coord_perms(base):
    """All coordinate permutations of (a,b,c): up to 6 variants."""
    a, b, c = base
    return list({(a, b, c), (a, c, b), (b, a, c), (b, c, a), (c, a, b), (c, b, a)})


def _all_perms(base):
    """All sign AND coordinate permutations: up to 48 variants."""
    results = set()
    for cp in _all_coord_perms(base):
        for sp in _all_sign_perms(cp):
            results.add(sp)
    return list(results)


def _even_perms(base):
    """Even (cyclic) permutations of coordinates with all sign changes."""
    a, b, c = base
    results = set()
    for perm in [(a, b, c), (b, c, a), (c, a, b)]:
        for sp in _all_sign_perms(perm):
            results.add(sp)
    return list(results)


def _even_sign_all_perms(base):
    """All coordinate permutations with even number of negative signs."""
    results = set()
    for perm in _all_coord_perms(base):
        a, b, c = perm
        for sa in (1, -1):
            for sb in (1, -1):
                for sc in (1, -1):
                    if (sa < 0) + (sb < 0) + (sc < 0) in (0, 2):
                        results.add((sa * a, sb * b, sc * c))
    return list(results)


def _icosa_verts():
    """12 icosahedron vertices (unnormalized)."""
    p = PHI
    verts = []
    for s1 in (-1, 1):
        for s2 in (-p, p):
            verts.append((0, s1, s2))
            verts.append((s1, s2, 0))
            verts.append((s2, 0, s1))
    return verts


def _dodeca_verts():
    """20 dodecahedron vertices (unnormalized)."""
    p, ip = PHI, IP
    verts = []
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                verts.append((x, y, z))
    for x in (-ip, ip):
        for z in (-p, p):
            verts.append((x, 0, z))
    for y in (-ip, ip):
        for x2 in (-p, p):
            verts.append((x2, y, 0))
    for z in (-ip, ip):
        for y2 in (-p, p):
            verts.append((0, y2, z))
    return verts


# ─── PLATONIC ──────────────────────────────────────────────────────────

def _tetrahedron():
    verts = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    verts = _normalize(verts)
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    return verts, edges, 4, 6, 4


def _cube():
    verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    verts = _normalize(verts)
    edges = [
        (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
        (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7),
    ]
    return verts, edges, 8, 12, 6


def _octahedron():
    verts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    edges = [
        (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 4), (2, 5), (3, 4), (3, 5),
    ]
    return verts, edges, 6, 12, 8


def _dodecahedron():
    verts = _normalize(_dodeca_verts())
    edges = _edges_by_dist(verts, 0.8)
    return verts, edges, 20, 30, 12


def _icosahedron():
    verts = _normalize(_icosa_verts())
    edges = _edges_by_dist(verts, 1.2)
    return verts, edges, 12, 30, 20


# ─── ARCHIMEDEAN ───────────────────────────────────────────────────────

def _truncated_tetrahedron():
    # All permutations of (3,1,1) with even number of negative signs
    verts = _dedup(_even_sign_all_perms((3, 1, 1)))
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 18)
    return verts, edges, 12, 18, 8


def _cuboctahedron():
    verts = _dedup(_all_perms((0, 1, 1)))
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 24)
    return verts, edges, 12, 24, 14


def _truncated_cube():
    xi = math.sqrt(2) - 1
    verts = _dedup(_all_perms((xi, 1, 1)))
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 36)
    return verts, edges, 24, 36, 14


def _truncated_octahedron():
    verts = _dedup(_all_perms((0, 1, 2)))
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 36)
    return verts, edges, 24, 36, 14


def _rhombicuboctahedron():
    verts = _dedup(_all_perms((1, 1, 1 + math.sqrt(2))))
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 48)
    return verts, edges, 24, 48, 26


def _truncated_cuboctahedron():
    verts = _dedup(_all_perms((1, 1 + math.sqrt(2), 1 + 2 * math.sqrt(2))))
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 72)
    return verts, edges, 48, 72, 26


def _snub_cube():
    # Tribonacci constant: t^3 = t^2 + t + 1
    t = 1.8392867552141612
    # Even permutations of (±1, ±1/t, ±t) with all sign combinations
    verts = []
    for sa in (1, -1):
        for sb in (1, -1):
            for sc in (1, -1):
                a, b, c = sa, sb / t, sc * t
                verts.append((a, b, c))
                verts.append((b, c, a))
                verts.append((c, a, b))
    verts = _dedup(verts)
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 60)
    return verts, edges, 24, 60, 38


def _icosidodecahedron():
    p = PHI
    verts = [(0, 0, p), (0, 0, -p), (0, p, 0), (0, -p, 0), (p, 0, 0), (-p, 0, 0)]
    hp = PHI / 2
    hp2 = PHI * PHI / 2
    verts += _even_perms((0.5, hp, hp2))
    verts = _dedup(verts)
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 60)
    return verts, edges, 30, 60, 32


def _truncated_dodecahedron():
    p = PHI
    p2 = p * p
    p3 = p2 * p
    bases = [(0, IP, 2 + p), (IP, p, 2 * p), (p, 2, p3)]
    verts = []
    for b in bases:
        verts += _even_perms(b)
    verts = _dedup(verts)
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 90)
    return verts, edges, 60, 90, 32


def _truncated_icosahedron():
    p = PHI
    bases = [(0, 1, 3 * p), (2, 1 + 2 * p, p), (1, 2 + p, 2 * p)]
    verts = []
    for b in bases:
        verts += _even_perms(b)
    verts = _dedup(verts)
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 90)
    return verts, edges, 60, 90, 32


def _rhombicosidodecahedron():
    p = PHI
    p2 = p * p
    p3 = p2 * p
    bases = [(1, 1, p3), (p2, p, 2 * p), (2 + p, 0, p2)]
    verts = []
    for b in bases:
        verts += _even_perms(b)
    verts = _dedup(verts)
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 120)
    return verts, edges, 60, 120, 62


def _truncated_icosidodecahedron():
    p = PHI
    bases = [
        (IP, IP, 3 + p),
        (2 * IP, p, 1 + 2 * p),
        (IP, p * p, 3 * p - 1),
        (2 * p - 1, 2, 2 + p),
        (p, 3, 2 * p),
    ]
    verts = []
    for b in bases:
        verts += _even_perms(b)
    verts = _dedup(verts)
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 180)
    return verts, edges, 120, 180, 62


def _snub_dodecahedron():
    p = PHI
    # The snub dodecahedron has 60 vertices generated from even permutations
    # of several base coordinates. Using the known construction:
    # xi is the positive real root of 8x^3 - 8x^2 + 1 = 0
    # Actually use: even permutations of (±2α, ±2, ±2β) with appropriate signs
    # where α = phi, β = phi^2 (simplified approximation for wireframe display)

    # Use the correct mathematical construction from Wikipedia:
    # Even permutations of the following with even number of negatives:
    # (2φ, 2, 2/φ)  — gives 12 vertices per base = 60 total from 5 bases

    # The actual snub dodecahedron can be generated from 5 orbits under
    # icosahedral symmetry. Each orbit has 12 vertices from even perms
    # of a base with even sign count.

    # Simplified but visually correct: use the approach from
    # "snub" operation on icosidodecahedron
    # Generate 60 vertices via icosahedral rotations of a seed

    # Build icosahedral rotation matrices
    rots = _icosahedral_rotations()
    # Seed point for snub dodecahedron (one vertex)
    seed = (0.9510565, 0.3090170, 0.0)  # on unit sphere
    # Slight offset to break symmetry for snub chirality
    seed = (0.9432, 0.3317, 0.0150)

    raw = []
    for rot in rots:
        x = rot[0][0] * seed[0] + rot[0][1] * seed[1] + rot[0][2] * seed[2]
        y = rot[1][0] * seed[0] + rot[1][1] * seed[1] + rot[1][2] * seed[2]
        z = rot[2][0] * seed[0] + rot[2][1] * seed[1] + rot[2][2] * seed[2]
        raw.append((x, y, z))
    verts = _dedup(raw, tol=1e-3)
    verts = _normalize(verts)
    edges = _edges_by_count(verts, 150)
    return verts, edges, len(verts), len(edges), 92


def _icosahedral_rotations():
    """Generate the 60 rotation matrices of icosahedral symmetry."""
    p = PHI
    # The 12 vertices of an icosahedron define the rotation axes
    # We build all 60 rotations from combinations of basic rotations

    def _mat_mult(a, b):
        return [
            [sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)
        ]

    def _rot_axis(axis, angle):
        """Rotation matrix around unit axis by angle."""
        x, y, z = axis
        c, s = math.cos(angle), math.sin(angle)
        t = 1 - c
        return [
            [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
        ]

    identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    # Icosahedron vertices (normalized) as rotation axes
    verts = _normalize(_icosa_verts())

    # 5-fold axes through opposite vertex pairs (6 axes, 4 non-trivial rotations each = 24)
    # 3-fold axes through opposite face pairs (10 axes, 2 each = 20)
    # 2-fold axes through opposite edge midpoints (15 axes, 1 each = 15)
    # Plus identity = 60 total

    rots = [identity]
    seen = set()
    seen.add(_mat_key(identity))

    # 5-fold rotations (through vertices)
    pairs = set()
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            # Opposite vertices
            if abs(verts[i][0] + verts[j][0]) < 0.01 and \
               abs(verts[i][1] + verts[j][1]) < 0.01 and \
               abs(verts[i][2] + verts[j][2]) < 0.01:
                pairs.add((i, j))

    for i, j in pairs:
        axis = verts[i]
        for k in range(1, 5):
            rot = _rot_axis(axis, 2 * math.pi * k / 5)
            key = _mat_key(rot)
            if key not in seen:
                seen.add(key)
                rots.append(rot)

    # 3-fold rotations (through face centers)
    # Face centers of icosahedron = vertices of dodecahedron (normalized)
    dodeca = _normalize(_dodeca_verts())
    face_pairs = set()
    for i in range(len(dodeca)):
        for j in range(i + 1, len(dodeca)):
            if abs(dodeca[i][0] + dodeca[j][0]) < 0.01 and \
               abs(dodeca[i][1] + dodeca[j][1]) < 0.01 and \
               abs(dodeca[i][2] + dodeca[j][2]) < 0.01:
                face_pairs.add(i)

    for i in face_pairs:
        axis = dodeca[i]
        for k in range(1, 3):
            rot = _rot_axis(axis, 2 * math.pi * k / 3)
            key = _mat_key(rot)
            if key not in seen:
                seen.add(key)
                rots.append(rot)

    # 2-fold rotations (through edge midpoints)
    edges = _edges_by_dist(_normalize(_icosa_verts()), 1.2)
    nv = _normalize(_icosa_verts())
    for a, b in edges:
        mid_raw = tuple((nv[a][k] + nv[b][k]) / 2 for k in range(3))
        mid = _normalize([mid_raw])[0]
        # Check if we already have opposite
        rot = _rot_axis(mid, math.pi)
        key = _mat_key(rot)
        if key not in seen:
            seen.add(key)
            rots.append(rot)

    return rots


def _mat_key(m, prec=3):
    """Hashable key for a rotation matrix (rounded for dedup)."""
    return tuple(round(m[i][j], prec) for i in range(3) for j in range(3))


# ─── KEPLER-POINSOT ───────────────────────────────────────────────────

def _small_stellated_dodecahedron():
    """12 icosahedron vertices with pentagram (long-diagonal) edges."""
    verts = _normalize(_icosa_verts())
    # Connect non-adjacent vertices (2nd-nearest neighbors)
    # Each vertex should connect to 5 others at the longer distance
    # Icosahedron distances: 30 short + 30 long = C(12,2)=66 total pairs
    # Short: 30 edges (nearest), Long: 30 edges (2nd nearest), Antipodal: 6 pairs
    # The stellated dodecahedron uses the 30 long-diagonal edges
    edges = []
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            dx = verts[i][0] - verts[j][0]
            dy = verts[i][1] - verts[j][1]
            dz = verts[i][2] - verts[j][2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if 1.55 < dist < 1.95:
                edges.append((i, j))
    return verts, edges, 12, 30, 12


def _great_dodecahedron():
    """12 icosahedron vertices with regular icosahedron edges (same topology)."""
    verts = _normalize(_icosa_verts())
    edges = _edges_by_dist(verts, 1.2)
    return verts, edges, 12, 30, 12


def _great_stellated_dodecahedron():
    """20 dodecahedron vertices with long-diagonal edges forming star pattern."""
    verts = _normalize(_dodeca_verts())
    # The star edges connect vertices at the 4th-nearest distance band (d≈1.868)
    # These form the characteristic intersecting star pattern
    edges = []
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            dx = verts[i][0] - verts[j][0]
            dy = verts[i][1] - verts[j][1]
            dz = verts[i][2] - verts[j][2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if 1.8 < dist < 1.95:
                edges.append((i, j))
    return verts, edges, 20, 30, 12


def _great_icosahedron():
    """12 icosahedron vertices with long-diagonal edges (same as small stellated)."""
    verts = _normalize(_icosa_verts())
    edges = []
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            dx = verts[i][0] - verts[j][0]
            dy = verts[i][1] - verts[j][1]
            dz = verts[i][2] - verts[j][2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if 1.55 < dist < 1.95:
                edges.append((i, j))
    return verts, edges, 12, 30, 20


# ─── CATALAN (duals of Archimedean) ───────────────────────────────────
# Catalans have vertices at multiple radii — use _scale_to_unit, not _normalize

def _triakis_tetrahedron():
    # Dual of truncated tetrahedron: 8V, 18E, 12F
    # 4 tetrahedron vertices + 4 dual tetrahedron vertices (raised)
    s = 5.0 / 3.0
    verts = [
        (1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1),
        (-s, -s, -s), (-s, s, s), (s, -s, s), (s, s, -s),
    ]
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 18)
    return verts, edges, 8, 18, 12


def _rhombic_dodecahedron():
    # Dual of cuboctahedron: 14V, 24E, 12F
    # 8 cube vertices + 6 octahedron vertices (at different radius)
    verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    s = 2.0
    verts += [(s, 0, 0), (-s, 0, 0), (0, s, 0), (0, -s, 0), (0, 0, s), (0, 0, -s)]
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 24)
    return verts, edges, 14, 24, 12


def _triakis_octahedron():
    # Dual of truncated cube: 14V, 36E, 24F
    # 6 octahedron vertices (raised) + 8 cube vertices
    s = 1 + math.sqrt(2)
    verts = [(s, 0, 0), (-s, 0, 0), (0, s, 0), (0, -s, 0), (0, 0, s), (0, 0, -s)]
    verts += [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 36)
    return verts, edges, 14, 36, 24


def _tetrakis_hexahedron():
    # Dual of truncated octahedron: 14V, 36E, 24F
    # 8 cube vertices + 6 raised octahedron vertices
    verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    s = 1.5
    verts += [(s, 0, 0), (-s, 0, 0), (0, s, 0), (0, -s, 0), (0, 0, s), (0, 0, -s)]
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 36)
    return verts, edges, 14, 36, 24


def _deltoidal_icositetrahedron():
    # Dual of rhombicuboctahedron: 26V, 48E, 24F
    # 6 octahedral + 8 cube + 12 cuboctahedral vertices
    s1 = 1 + 1 / math.sqrt(2)
    verts = [(s1, 0, 0), (-s1, 0, 0), (0, s1, 0), (0, -s1, 0), (0, 0, s1), (0, 0, -s1)]
    verts += [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    s2 = 1 + math.sqrt(2)
    for pair in [(s2, s2, 0), (s2, 0, s2), (0, s2, s2)]:
        verts += _all_sign_perms(pair)
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 48)
    return verts, edges, 26, 48, 24


def _disdyakis_dodecahedron():
    # Dual of truncated cuboctahedron: 26V, 72E, 48F
    # 6 octahedral + 8 cube + 12 edge-midpoint vertices (3 different radii)
    s3 = 1 + math.sqrt(2)
    verts = [(s3, 0, 0), (-s3, 0, 0), (0, s3, 0), (0, -s3, 0), (0, 0, s3), (0, 0, -s3)]
    s2 = 1 + 1 / math.sqrt(2)
    verts += [(x, y, z) for x in (-s2, s2) for y in (-s2, s2) for z in (-s2, s2)]
    for pair in [(1, 1, 0), (1, 0, 1), (0, 1, 1)]:
        verts += _all_sign_perms(pair)
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 72)
    return verts, edges, 26, 72, 48


def _pentagonal_icositetrahedron():
    # Dual of snub cube: 38V, 60E, 24F
    # 6 axial + 8 cube-like + 24 from permutations
    s = 1.1489705752
    t = 0.6435257759
    u = 0.3553095084
    verts = []
    for v in [(s, 0, 0), (-s, 0, 0), (0, s, 0), (0, -s, 0), (0, 0, s), (0, 0, -s)]:
        verts.append(v)
    c = 0.7357220783
    verts += [(x, y, z) for x in (-c, c) for y in (-c, c) for z in (-c, c)]
    for sa in (1, -1):
        for sb in (1, -1):
            for sc in (1, -1):
                verts.append((sa * t, sb * u, sc * s))
                verts.append((sb * u, sc * s, sa * t))
                verts.append((sc * s, sa * t, sb * u))
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 60)
    return verts, edges, 38, 60, 24


def _rhombic_triacontahedron():
    # Dual of icosidodecahedron: 32V, 60E, 30F
    # 12 icosahedron + 20 dodecahedron vertices at different radii
    p = PHI
    verts = _icosa_verts()  # 12 at radius ~1.9
    # Dodecahedron at scaled radius
    s = PHI
    dv = _dodeca_verts()
    verts += [(x * s, y * s, z * s) for x, y, z in dv]  # 20 at radius ~2.8
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 60)
    return verts, edges, 32, 60, 30


def _triakis_icosahedron():
    # Dual of truncated dodecahedron: 32V, 90E, 60F
    # 12 icosahedron vertices (raised) + 20 dodecahedron vertices
    verts = [(x * 1.4, y * 1.4, z * 1.4) for x, y, z in _icosa_verts()]
    verts += _dodeca_verts()
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 90)
    return verts, edges, 32, 90, 60


def _pentakis_dodecahedron():
    # Dual of truncated icosahedron: 32V, 90E, 60F
    # 20 dodecahedron vertices + 12 icosahedron vertices (raised outward)
    verts = list(_dodeca_verts())
    verts += [(x * 1.6, y * 1.6, z * 1.6) for x, y, z in _icosa_verts()]
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 90)
    return verts, edges, 32, 90, 60


def _deltoidal_hexecontahedron():
    # Dual of rhombicosidodecahedron: 62V, 120E, 60F
    # 12 icosahedron + 20 dodecahedron + 30 icosidodecahedron midpoint vertices
    verts = list(_icosa_verts())  # 12 vertices
    verts += [(x * 1.22, y * 1.22, z * 1.22) for x, y, z in _dodeca_verts()]  # 20
    p = PHI
    p2 = p * p
    s = 1.08
    mid_verts = _even_perms((0.5 * s, p / 2 * s, p2 / 2 * s))
    # Also the 6 axis points from icosidodecahedron
    for v in [(0, 0, p * s / 2), (0, 0, -p * s / 2),
              (0, p * s / 2, 0), (0, -p * s / 2, 0),
              (p * s / 2, 0, 0), (-p * s / 2, 0, 0)]:
        mid_verts.append(v)
    mid_verts = _dedup(mid_verts)
    verts += mid_verts
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 120)
    return verts, edges, 62, 120, 60


def _disdyakis_triacontahedron():
    # Dual of truncated icosidodecahedron: 62V, 180E, 120F
    # Same vertex orbits as deltoidal hexecontahedron but at different radii
    verts = list(_icosa_verts())
    verts += [(x * 1.31, y * 1.31, z * 1.31) for x, y, z in _dodeca_verts()]
    p = PHI
    p2 = p * p
    s = 1.16
    mid_verts = _even_perms((0.5 * s, p / 2 * s, p2 / 2 * s))
    for v in [(0, 0, p * s / 2), (0, 0, -p * s / 2),
              (0, p * s / 2, 0), (0, -p * s / 2, 0),
              (p * s / 2, 0, 0), (-p * s / 2, 0, 0)]:
        mid_verts.append(v)
    mid_verts = _dedup(mid_verts)
    verts += mid_verts
    verts = _dedup(verts)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 180)
    return verts, edges, 62, 180, 120


def _pentagonal_hexecontahedron():
    # Dual of snub dodecahedron: 92V, 150E, 60F
    # 12 icosahedral + 20 dodecahedral + 60 snub-type vertices
    verts = list(_icosa_verts())
    verts += [(x * 1.15, y * 1.15, z * 1.15) for x, y, z in _dodeca_verts()]
    # 60 additional vertices from rotated/offset positions
    # Use icosahedral rotations of a seed point at a different radius
    rots = _icosahedral_rotations()
    seed = (0.85, 0.35, 0.12)
    for rot in rots:
        x = rot[0][0] * seed[0] + rot[0][1] * seed[1] + rot[0][2] * seed[2]
        y = rot[1][0] * seed[0] + rot[1][1] * seed[1] + rot[1][2] * seed[2]
        z = rot[2][0] * seed[0] + rot[2][1] * seed[1] + rot[2][2] * seed[2]
        verts.append((x, y, z))
    verts = _dedup(verts, tol=1e-3)
    verts = _scale_to_unit(verts)
    edges = _edges_by_count(verts, 150)
    return verts, edges, len(verts), len(edges), 60


# ─── FAMILY GROUPING ──────────────────────────────────────────────────

FAMILIES = [
    ('PLATONIC', [
        ('TETRA',       _tetrahedron),
        ('CUBE',        _cube),
        ('OCTA',        _octahedron),
        ('DODECA',      _dodecahedron),
        ('ICOSA',       _icosahedron),
    ]),
    ('ARCHIMEDEAN', [
        ('TRUNC TETRA', _truncated_tetrahedron),
        ('CUBOCTAHEDRN', _cuboctahedron),
        ('TRUNC CUBE',  _truncated_cube),
        ('TRUNC OCTA',  _truncated_octahedron),
        ('RHOMBICUBOCTA', _rhombicuboctahedron),
        ('TRUNC CUBOCTA', _truncated_cuboctahedron),
        ('SNUB CUBE',   _snub_cube),
        ('ICOSIDODECA', _icosidodecahedron),
        ('TRUNC DODECA', _truncated_dodecahedron),
        ('TRUNC ICOSA', _truncated_icosahedron),
        ('RHOMBICOSIDO', _rhombicosidodecahedron),
        ('TRUNC ICOSID', _truncated_icosidodecahedron),
        ('SNUB DODECA', _snub_dodecahedron),
    ]),
    ('KEPLER-POINSOT', [
        ('SM STEL DODEC', _small_stellated_dodecahedron),
        ('GREAT DODECA', _great_dodecahedron),
        ('GR STEL DODEC', _great_stellated_dodecahedron),
        ('GREAT ICOSA', _great_icosahedron),
    ]),
    ('CATALAN', [
        ('TRIAKIS TETRA', _triakis_tetrahedron),
        ('RHOMBIC DODEC', _rhombic_dodecahedron),
        ('TRIAKIS OCTA', _triakis_octahedron),
        ('TETRAKIS HEX', _tetrakis_hexahedron),
        ('DELTOID ICOSI', _deltoidal_icositetrahedron),
        ('DISDYAKIS DOD', _disdyakis_dodecahedron),
        ('PENT ICOSI',   _pentagonal_icositetrahedron),
        ('RHOMBIC TRIAC', _rhombic_triacontahedron),
        ('TRIAKIS ICOSA', _triakis_icosahedron),
        ('PENTAKIS DOD', _pentakis_dodecahedron),
        ('DELTOID HEXEC', _deltoidal_hexecontahedron),
        ('DISDYAKIS TRI', _disdyakis_triacontahedron),
        ('PENT HEXEC',   _pentagonal_hexecontahedron),
    ]),
]
