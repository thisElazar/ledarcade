"""
Proteins - 3D Protein Backbone Visualization
=============================================
Rotating 3D ribbon-style backbone traces of protein structures.
Color-coded by secondary structure: helix (red), sheet (yellow), coil (gray).
Real Cα coordinates from RCSB Protein Data Bank.

Controls:
  Joystick   - Rotate protein in 3D (pauses auto-cycle to let you explore)
  Z/X        - Cycle through proteins (resumes auto-cycle)

Auto-rotates around Z-axis. Manual rotation pauses cycling until you move on.
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


# Secondary structure colors (classic ribbon diagram scheme)
SS_COLORS = {
    'H': (255, 80, 80),    # Alpha helix - red/salmon
    'G': (255, 120, 100),  # 3-10 helix - lighter red
    'I': (255, 60, 120),   # Pi helix - pink-red
    'E': (255, 255, 80),   # Beta sheet - yellow
    'B': (220, 200, 80),   # Beta bridge - darker yellow
    'T': (100, 200, 180),  # Turn - cyan
    'S': (140, 140, 140),  # Bend - gray
    'C': (180, 180, 180),  # Coil/loop - light gray
}

# =============================================================================
# PROTEIN DATA - Real Cα coordinates from RCSB Protein Data Bank
# Generated with tools/pdb_parser.py
# =============================================================================

# Ubiquitin (PDB: 1UBQ) - 76 residues
# The "kiss of death" protein - tags proteins for destruction
# Nobel Prize connection: Ubiquitin system, 2004
UBIQUITIN = {
    'name': 'UBIQUITIN',
    'pdb': '1UBQ',
    'description': 'Protein degradation tag',
    'residues': 76,
    'categories': ['enzymes', 'ancient', 'nobel'],
    'backbone': [
        ( 26.266,  25.413,   2.842, 'E'),  # MET 1
        ( 26.850,  29.021,   3.898, 'E'),  # GLN 2
        ( 26.235,  30.058,   7.497, 'E'),  # ILE 3
        ( 26.772,  33.436,   9.197, 'E'),  # PHE 4
        ( 28.605,  33.965,  12.503, 'E'),  # VAL 5
        ( 27.691,  37.315,  14.143, 'E'),  # LYS 6
        ( 30.225,  38.643,  16.662, 'E'),  # THR 7
        ( 29.607,  41.180,  19.467, 'C'),  # LEU 8
        ( 31.422,  43.940,  17.553, 'C'),  # THR 9
        ( 28.978,  43.960,  14.678, 'E'),  # GLY 10
        ( 31.191,  42.012,  12.331, 'E'),  # LYS 11
        ( 29.542,  39.020,  10.653, 'E'),  # THR 12
        ( 31.720,  36.289,   9.176, 'E'),  # ILE 13
        ( 30.505,  33.884,   6.512, 'E'),  # THR 14
        ( 31.677,  30.275,   6.639, 'E'),  # LEU 15
        ( 31.220,  27.341,   4.275, 'E'),  # GLU 16
        ( 30.288,  24.245,   6.193, 'E'),  # VAL 17
        ( 28.468,  20.940,   5.980, 'C'),  # GLU 18
        ( 25.829,  19.825,   8.494, 'C'),  # PRO 19
        ( 28.054,  16.835,   9.210, 'C'),  # SER 20
        ( 30.796,  19.083,  10.566, 'C'),  # ASP 21
        ( 31.398,  19.064,  14.286, 'C'),  # THR 22
        ( 31.288,  22.201,  16.417, 'H'),  # ILE 23
        ( 35.031,  21.722,  17.069, 'H'),  # GLU 24
        ( 35.590,  21.945,  13.302, 'H'),  # ASN 25
        ( 33.533,  25.097,  12.978, 'H'),  # VAL 26
        ( 35.596,  26.715,  15.736, 'H'),  # LYS 27
        ( 38.794,  25.761,  13.880, 'H'),  # ALA 28
        ( 37.471,  27.391,  10.668, 'H'),  # LYS 29
        ( 36.731,  30.570,  12.645, 'H'),  # ILE 30
        ( 40.269,  30.508,  14.115, 'H'),  # GLN 31
        ( 41.718,  30.022,  10.643, 'H'),  # ASP 32
        ( 39.808,  32.994,   9.233, 'H'),  # LYS 33
        ( 39.676,  35.547,  12.072, 'H'),  # GLU 34
        ( 42.345,  34.269,  14.431, 'C'),  # GLY 35
        ( 40.226,  33.716,  17.509, 'C'),  # ILE 36
        ( 41.461,  30.751,  19.594, 'C'),  # PRO 37
        ( 38.817,  28.020,  19.889, 'C'),  # PRO 38
        ( 39.063,  28.063,  23.695, 'C'),  # ASP 39
        ( 37.738,  31.637,  23.712, 'E'),  # GLN 40
        ( 34.738,  30.875,  21.473, 'E'),  # GLN 41
        ( 31.200,  30.329,  22.780, 'E'),  # ARG 42
        ( 28.762,  29.573,  19.906, 'E'),  # LEU 43
        ( 25.034,  30.170,  20.401, 'E'),  # ILE 44
        ( 22.126,  29.062,  18.183, 'E'),  # PHE 45
        ( 18.443,  29.143,  19.083, 'C'),  # ALA 46
        ( 19.399,  29.894,  22.655, 'C'),  # GLY 47
        ( 21.550,  26.796,  23.133, 'E'),  # LYS 48
        ( 25.349,  26.872,  23.643, 'E'),  # GLN 49
        ( 26.826,  24.521,  21.012, 'E'),  # LEU 50
        ( 29.015,  21.657,  22.288, 'C'),  # GLU 51
        ( 32.262,  20.670,  20.514, 'C'),  # ASP 52
        ( 31.568,  16.962,  19.825, 'C'),  # GLY 53
        ( 28.108,  17.439,  18.276, 'C'),  # ARG 54
        ( 27.574,  18.192,  14.563, 'C'),  # THR 55
        ( 25.594,  21.109,  13.072, 'H'),  # LEU 56
        ( 22.924,  18.583,  12.025, 'H'),  # SER 57
        ( 22.418,  17.638,  15.693, 'H'),  # ASP 58
        ( 21.079,  21.149,  16.251, 'H'),  # TYR 59
        ( 19.065,  21.352,  12.999, 'C'),  # ASN 60
        ( 21.184,  24.263,  11.690, 'C'),  # ILE 61
        ( 20.081,  24.773,   8.033, 'C'),  # GLN 62
        ( 21.656,  26.847,   5.240, 'C'),  # LYS 63
        ( 21.907,  30.563,   5.881, 'E'),  # GLU 64
        ( 21.419,  30.253,   9.620, 'E'),  # SER 65
        ( 23.212,  32.762,  11.891, 'E'),  # THR 66
        ( 25.149,  31.609,  14.980, 'E'),  # LEU 67
        ( 26.179,  34.127,  17.650, 'E'),  # HIS 68
        ( 29.801,  34.145,  18.829, 'E'),  # LEU 69
        ( 30.479,  35.369,  22.374, 'E'),  # VAL 70
        ( 34.145,  35.472,  23.481, 'E'),  # LEU 71
        ( 35.161,  34.174,  26.896, 'E'),  # ARG 72
        ( 38.668,  35.502,  27.680, 'C'),  # LEU 73
        ( 40.873,  33.802,  30.253, 'C'),  # ARG 74
        ( 41.845,  36.550,  32.686, 'C'),  # GLY 75
        ( 40.373,  39.813,  33.944, 'C'),  # GLY 76
    ],
}

# Myoglobin (PDB: 1MBO) - 153 residues
# First protein structure ever solved by X-ray crystallography!
# Nobel Prize: Kendrew & Perutz, 1962
MYOGLOBIN = {
    'name': 'MYOGLOBIN',
    'pdb': '1MBO',
    'description': 'Oxygen storage',
    'residues': 153,
    'categories': ['transport', 'nobel', 'ancient'],
    'backbone': [
        ( -3.778,  15.543,  15.643, 'C'),  # VAL 1
        ( -0.551,  13.989,  17.161, 'C'),  # LEU 2
        ( -1.334,  12.314,  20.516, 'H'),  # SER 3
        (  0.526,  13.372,  23.579, 'H'),  # GLU 4
        (  2.461,  10.011,  23.364, 'H'),  # GLY 5
        (  3.548,  10.856,  19.792, 'H'),  # GLU 6
        (  4.662,  14.314,  20.831, 'H'),  # TRP 7
        (  6.743,  12.849,  23.641, 'H'),  # GLN 8
        (  8.532,  10.568,  21.090, 'H'),  # LEU 9
        (  9.321,  13.599,  18.864, 'H'),  # VAL 10
        ( 10.569,  15.786,  21.658, 'H'),  # LEU 11
        ( 12.668,  13.098,  23.228, 'H'),  # HIS 12
        ( 14.655,  12.593,  20.062, 'H'),  # VAL 13
        ( 14.771,  16.373,  19.420, 'H'),  # TRP 14
        ( 16.402,  17.011,  22.885, 'H'),  # ALA 15
        ( 19.198,  14.695,  21.533, 'H'),  # LYS 16
        ( 19.396,  16.851,  18.368, 'H'),  # VAL 17
        ( 19.967,  19.798,  20.613, 'H'),  # GLU 18
        ( 23.159,  18.327,  22.057, 'C'),  # ALA 19
        ( 24.742,  18.968,  18.609, 'H'),  # ASP 20
        ( 22.609,  21.371,  16.567, 'H'),  # VAL 21
        ( 25.375,  22.419,  14.217, 'H'),  # ALA 22
        ( 26.538,  18.922,  13.278, 'H'),  # GLY 23
        ( 22.908,  17.835,  12.696, 'H'),  # HIS 24
        ( 22.291,  20.941,  10.601, 'H'),  # GLY 25
        ( 25.242,  20.209,   8.395, 'H'),  # GLN 26
        ( 24.485,  16.568,   7.799, 'H'),  # ASP 27
        ( 20.761,  17.483,   7.013, 'H'),  # ILE 28
        ( 21.684,  20.268,   4.480, 'H'),  # LEU 29
        ( 24.399,  18.138,   2.829, 'H'),  # ILE 30
        ( 22.016,  15.206,   2.455, 'H'),  # ARG 31
        ( 19.417,  17.536,   0.870, 'H'),  # LEU 32
        ( 21.897,  19.050,  -1.564, 'H'),  # PHE 33
        ( 23.432,  15.773,  -2.591, 'H'),  # LYS 34
        ( 20.115,  13.881,  -2.948, 'H'),  # SER 35
        ( 18.252,  16.814,  -4.658, 'H'),  # HIS 36
        ( 20.740,  19.059,  -6.403, 'H'),  # PRO 37
        ( 18.028,  21.416,  -7.582, 'H'),  # GLU 38
        ( 17.636,  22.578,  -3.958, 'H'),  # THR 39
        ( 21.136,  23.988,  -3.888, 'H'),  # LEU 40
        ( 20.362,  26.317,  -6.708, 'H'),  # GLU 41
        ( 17.817,  28.134,  -4.480, 'H'),  # LYS 42
        ( 20.737,  29.318,  -2.365, 'C'),  # PHE 43
        ( 22.813,  32.143,  -3.813, 'C'),  # ASP 44
        ( 24.831,  31.896,  -0.674, 'C'),  # ARG 45
        ( 25.788,  28.243,  -1.167, 'C'),  # PHE 46
        ( 25.616,  27.570,  -4.932, 'C'),  # LYS 47
        ( 29.386,  27.834,  -5.308, 'C'),  # HIS 48
        ( 29.912,  24.557,  -3.338, 'C'),  # LEU 49
        ( 30.347,  21.580,  -5.555, 'C'),  # LYS 50
        ( 31.767,  18.709,  -3.524, 'H'),  # THR 51
        ( 30.744,  17.144,  -0.264, 'H'),  # GLU 52
        ( 34.155,  18.102,   1.307, 'H'),  # ALA 53
        ( 33.641,  21.706,   0.251, 'H'),  # GLU 54
        ( 30.199,  21.618,   1.860, 'H'),  # MET 55
        ( 31.589,  20.175,   5.087, 'H'),  # LYS 56
        ( 34.314,  22.835,   5.280, 'H'),  # ALA 57
        ( 31.912,  25.807,   4.967, 'H'),  # SER 58
        ( 31.373,  27.614,   8.202, 'H'),  # GLU 59
        ( 28.550,  29.665,   6.679, 'H'),  # ASP 60
        ( 26.658,  26.500,   5.717, 'H'),  # LEU 61
        ( 26.994,  25.225,   9.258, 'H'),  # LYS 62
        ( 25.617,  28.558,  10.478, 'H'),  # LYS 63
        ( 22.528,  28.344,   8.261, 'H'),  # HIS 64
        ( 22.026,  24.725,   9.446, 'H'),  # GLY 65
        ( 21.740,  26.113,  12.986, 'H'),  # VAL 66
        ( 19.213,  28.787,  11.765, 'H'),  # THR 67
        ( 17.053,  26.058,  10.208, 'H'),  # VAL 68
        ( 17.122,  23.647,  13.156, 'H'),  # LEU 69
        ( 16.561,  26.401,  15.713, 'H'),  # THR 70
        ( 13.319,  27.524,  13.913, 'H'),  # ALA 71
        ( 12.223,  23.897,  13.490, 'H'),  # LEU 72
        ( 12.729,  23.180,  17.183, 'H'),  # GLY 73
        ( 10.726,  26.217,  18.228, 'H'),  # ALA 74
        (  7.837,  24.902,  16.083, 'H'),  # ILE 75
        (  8.025,  21.366,  17.417, 'H'),  # LEU 76
        (  7.932,  22.399,  21.075, 'H'),  # LYS 77
        (  4.605,  24.157,  20.444, 'C'),  # LYS 78
        (  3.055,  20.773,  19.885, 'C'),  # LYS 79
        (  0.884,  21.856,  16.914, 'C'),  # GLY 80
        (  0.084,  25.364,  18.327, 'C'),  # HIS 81
        (  2.580,  27.040,  15.977, 'C'),  # HIS 82
        (  0.499,  29.591,  14.125, 'C'),  # GLU 83
        (  2.743,  32.492,  15.046, 'C'),  # ALA 84
        (  6.006,  30.722,  14.276, 'C'),  # GLU 85
        (  4.845,  29.367,  10.944, 'H'),  # LEU 86
        (  3.418,  32.583,   9.510, 'H'),  # LYS 87
        (  6.733,  34.474,   8.914, 'H'),  # PRO 88
        (  8.392,  31.339,   7.647, 'H'),  # LEU 89
        (  5.743,  30.450,   5.036, 'H'),  # ALA 90
        (  5.641,  34.082,   3.996, 'H'),  # GLN 91
        (  9.397,  34.325,   3.212, 'H'),  # SER 92
        (  9.482,  30.829,   1.766, 'H'),  # HIS 93
        (  6.608,  31.444,  -0.570, 'H'),  # ALA 94
        (  7.318,  34.957,  -1.613, 'H'),  # THR 95
        ( 11.039,  35.730,  -1.078, 'C'),  # LYS 96
        ( 12.802,  32.390,  -1.408, 'C'),  # HIS 97
        ( 10.294,  30.627,  -3.632, 'C'),  # LYS 98
        ( 10.521,  27.177,  -2.140, 'C'),  # ILE 99
        (  8.107,  24.624,  -3.490, 'H'),  # PRO 100
        (  6.278,  22.523,  -0.982, 'H'),  # ILE 101
        (  7.913,  19.410,  -2.562, 'H'),  # LYS 102
        ( 11.348,  20.703,  -1.426, 'H'),  # TYR 103
        (  9.975,  20.841,   2.111, 'H'),  # LEU 104
        (  9.100,  17.159,   1.628, 'H'),  # GLU 105
        ( 12.731,  16.563,   0.592, 'H'),  # PHE 106
        ( 14.231,  18.277,   3.694, 'H'),  # ILE 107
        ( 11.737,  16.264,   5.770, 'H'),  # SER 108
        ( 13.167,  13.030,   4.370, 'H'),  # GLU 109
        ( 16.755,  14.307,   5.047, 'H'),  # ALA 110
        ( 15.883,  15.097,   8.723, 'H'),  # ILE 111
        ( 14.464,  11.614,   9.196, 'H'),  # ILE 112
        ( 17.445,   9.959,   7.522, 'H'),  # HIS 113
        ( 19.961,  11.825,   9.752, 'H'),  # VAL 114
        ( 18.023,  11.272,  12.956, 'H'),  # LEU 115
        ( 18.079,   7.530,  12.152, 'H'),  # HIS 116
        ( 21.797,   7.628,  11.492, 'H'),  # SER 117
        ( 22.653,   9.420,  14.723, 'H'),  # ARG 118
        ( 20.104,   8.133,  17.264, 'C'),  # HIS 119
        ( 18.995,   4.589,  16.396, 'C'),  # PRO 120
        ( 18.241,   3.607,  20.023, 'C'),  # GLY 121
        ( 15.778,   6.428,  20.440, 'C'),  # ASP 122
        ( 14.609,   6.460,  16.900, 'C'),  # PHE 123
        ( 12.832,   3.156,  16.524, 'H'),  # GLY 124
        (  9.786,   2.736,  14.225, 'H'),  # ALA 125
        (  7.389,   4.297,  16.637, 'H'),  # ASP 126
        (  9.515,   7.486,  16.976, 'H'),  # ALA 127
        ( 10.012,   7.522,  13.159, 'H'),  # GLN 128
        (  6.259,   7.374,  12.620, 'H'),  # GLY 129
        (  5.701,  10.186,  15.152, 'H'),  # ALA 130
        (  8.374,  12.432,  13.582, 'H'),  # MET 131
        (  6.970,  11.819,  10.125, 'H'),  # ASN 132
        (  3.551,  12.927,  11.442, 'H'),  # LYS 133
        (  4.933,  16.037,  12.959, 'H'),  # ALA 134
        (  6.744,  16.974,   9.736, 'H'),  # LEU 135
        (  3.556,  16.299,   7.737, 'H'),  # GLU 136
        (  1.634,  18.685,  10.046, 'H'),  # LEU 137
        (  4.324,  21.348,   9.443, 'H'),  # PHE 138
        (  3.960,  20.790,   5.668, 'H'),  # ARG 139
        (  0.178,  20.774,   5.660, 'H'),  # LYS 140
        ( -0.073,  24.051,   7.608, 'H'),  # ASP 141
        (  2.592,  25.760,   5.470, 'H'),  # ILE 142
        (  0.793,  24.452,   2.322, 'H'),  # ALA 143
        ( -2.403,  26.208,   3.476, 'H'),  # ALA 144
        ( -0.609,  29.511,   3.779, 'H'),  # LYS 145
        (  1.012,  29.107,   0.347, 'H'),  # TYR 146
        ( -2.467,  28.487,  -1.060, 'H'),  # LYS 147
        ( -3.764,  31.650,   0.411, 'H'),  # GLU 148
        ( -0.868,  33.677,  -1.039, 'H'),  # LEU 149
        ( -1.280,  31.951,  -4.500, 'C'),  # GLY 150
        (  1.969,  29.821,  -4.613, 'C'),  # TYR 151
        (  0.565,  26.440,  -3.380, 'C'),  # GLN 152
        (  3.821,  24.384,  -3.588, 'C'),  # GLY 153
    ],
}

# Lysozyme (PDB: 1LYZ) - 129 residues
# Antibacterial enzyme found in tears, saliva, and egg white
# First enzyme structure solved
LYSOZYME = {
    'name': 'LYSOZYME',
    'pdb': '1LYZ',
    'description': 'Antibacterial enzyme',
    'residues': 129,
    'categories': ['immune', 'enzymes', 'nobel'],
    'backbone': [
        (  2.439,  10.217,   9.791, 'E'),  # LYS 1
        (  2.307,  14.172,   7.580, 'E'),  # VAL 2
        ( -1.187,  15.293,   7.580, 'E'),  # PHE 3
        ( -2.637,  17.468,   4.864, 'C'),  # GLY 4
        ( -3.823,  20.764,   5.685, 'H'),  # ARG 5
        ( -7.581,  20.105,   4.611, 'H'),  # CYS 6
        ( -7.119,  16.414,   6.191, 'H'),  # GLU 7
        ( -5.735,  17.534,   9.475, 'H'),  # LEU 8
        ( -8.372,  19.907,   9.665, 'H'),  # ALA 9
        (-11.206,  17.205,   9.475, 'H'),  # ALA 10
        ( -9.426,  14.963,  11.749, 'H'),  # ALA 11
        ( -9.295,  17.534,  14.529, 'H'),  # MET 12
        (-12.854,  18.062,  14.213, 'H'),  # LYS 13
        (-13.645,  14.502,  14.213, 'H'),  # ARG 14
        (-11.865,  14.898,  17.814, 'H'),  # HIS 15
        (-13.645,  17.996,  19.772, 'C'),  # GLY 16
        (-10.877,  20.764,  18.635, 'C'),  # LEU 17
        (-13.184,  23.071,  16.866, 'C'),  # ASP 18
        (-14.172,  25.708,  19.330, 'C'),  # ASN 19
        (-12.656,  24.258,  21.857, 'C'),  # TYR 20
        (-12.195,  26.697,  24.762, 'C'),  # ARG 21
        (-13.513,  29.136,  22.109, 'C'),  # GLY 22
        (-10.086,  28.609,  19.646, 'C'),  # TYR 23
        (-11.338,  28.147,  16.171, 'C'),  # SER 24
        (-10.547,  25.379,  13.897, 'H'),  # LEU 25
        ( -8.174,  27.224,  12.002, 'H'),  # GLY 26
        ( -6.262,  28.279,  15.161, 'H'),  # ASN 27
        ( -5.603,  24.588,  15.540, 'H'),  # TRP 28
        ( -4.614,  23.731,  11.876, 'H'),  # VAL 29
        ( -2.109,  26.697,  11.560, 'H'),  # CYS 30
        ( -0.791,  25.840,  14.718, 'H'),  # ALA 31
        ( -0.198,  22.478,  14.592, 'H'),  # ALA 32
        (  1.384,  23.467,  10.612, 'H'),  # LYS 33
        (  3.955,  25.906,  11.749, 'H'),  # PHE 34
        (  4.680,  23.796,  14.971, 'H'),  # GLU 35
        (  4.878,  20.435,  13.455, 'C'),  # SER 36
        (  4.680,  20.632,   9.665, 'C'),  # ASN 37
        (  1.780,  18.062,   9.475, 'E'),  # PHE 38
        (  4.021,  15.754,  10.676, 'E'),  # ASN 39
        (  2.966,  13.843,  13.771, 'E'),  # THR 40
        (  6.724,  12.063,  14.339, 'C'),  # GLN 41
        (  8.569,  15.293,  14.339, 'E'),  # ALA 42
        ( 10.481,  15.623,  17.751, 'E'),  # THR 43
        ( 12.195,  18.787,  19.077, 'E'),  # ASN 44
        ( 14.766,  19.248,  21.857, 'E'),  # ARG 45
        ( 15.161,  22.676,  23.499, 'E'),  # ASN 46
        ( 18.589,  23.071,  26.026, 'C'),  # THR 47
        ( 17.007,  21.819,  29.500, 'C'),  # ASP 48
        ( 16.480,  17.930,  28.805, 'C'),  # GLY 49
        ( 13.184,  18.787,  27.605, 'E'),  # SER 50
        ( 11.931,  17.798,  24.257, 'E'),  # THR 51
        (  8.899,  18.457,  22.109, 'E'),  # ASP 52
        (  6.987,  15.623,  20.277, 'E'),  # TYR 53
        (  4.087,  15.161,  17.687, 'E'),  # GLY 54
        (  1.846,  17.600,  15.413, 'C'),  # ILE 55
        (  1.187,  19.775,  18.319, 'C'),  # LEU 56
        (  4.746,  19.907,  20.025, 'E'),  # GLN 57
        (  3.889,  18.853,  23.373, 'E'),  # ILE 58
        (  6.724,  19.248,  25.899, 'E'),  # ASN 59
        (  8.042,  16.611,  28.426, 'E'),  # SER 60
        (  8.701,  18.655,  31.332, 'C'),  # ARG 61
        (  4.812,  18.787,  32.090, 'C'),  # TRP 62
        (  2.703,  16.875,  29.563, 'C'),  # TRP 63
        (  4.153,  13.579,  28.805, 'C'),  # CYS 64
        (  6.921,  11.470,  30.195, 'C'),  # ASN 65
        (  9.954,  10.151,  27.858, 'C'),  # ASP 66
        ( 12.195,   8.833,  30.321, 'C'),  # GLY 67
        ( 15.029,  11.404,  30.005, 'C'),  # ARG 68
        ( 13.843,  14.700,  31.079, 'C'),  # THR 69
        ( 14.172,  14.832,  34.869, 'C'),  # PRO 70
        ( 11.865,  17.666,  35.754, 'C'),  # GLY 71
        (  9.229,  15.623,  34.806, 'C'),  # SER 72
        (  5.867,  15.689,  36.259, 'C'),  # ARG 73
        (  3.757,  13.711,  33.985, 'C'),  # ASN 74
        (  0.725,  16.018,  33.732, 'C'),  # LEU 75
        ( -1.187,  14.107,  30.700, 'C'),  # CYS 76
        ( -0.066,  10.942,  32.280, 'C'),  # ASN 77
        (  0.791,   9.492,  28.679, 'C'),  # ILE 78
        (  4.614,   8.569,  27.542, 'C'),  # PRO 79
        (  5.933,  11.206,  24.762, 'H'),  # CYS 80
        (  5.999,   8.635,  22.299, 'H'),  # SER 81
        (  2.307,   8.108,  22.236, 'H'),  # ALA 82
        (  2.439,  11.536,  20.846, 'H'),  # LEU 83
        (  4.021,  10.679,  17.624, 'H'),  # LEU 84
        (  1.846,   7.910,  16.361, 'C'),  # SER 85
        ( -0.264,   8.503,  13.329, 'C'),  # SER 86
        ( -3.428,   8.899,  15.413, 'C'),  # ASP 87
        ( -3.823,  12.261,  17.182, 'C'),  # ILE 88
        ( -5.933,  11.008,  19.961, 'H'),  # THR 89
        ( -3.230,  11.668,  22.425, 'H'),  # ALA 90
        ( -2.175,  14.766,  21.478, 'H'),  # SER 91
        ( -5.339,  16.348,  20.909, 'H'),  # VAL 92
        ( -6.658,  14.766,  24.257, 'H'),  # ASN 93
        ( -3.362,  16.084,  25.836, 'H'),  # CYS 94
        ( -3.691,  19.446,  23.941, 'H'),  # ALA 95
        ( -7.053,  19.710,  25.647, 'H'),  # LYS 96
        ( -5.273,  20.303,  29.247, 'C'),  # LYS 97
        ( -2.835,  22.742,  27.921, 'C'),  # ILE 98
        ( -5.076,  24.851,  26.278, 'C'),  # VAL 99
        ( -7.581,  24.851,  29.563, 'C'),  # SER 100
        ( -4.944,  25.313,  32.153, 'C'),  # ASP 101
        ( -4.482,  29.004,  31.774, 'C'),  # GLY 102
        ( -2.769,  30.454,  28.679, 'C'),  # ASN 103
        ( -4.614,  29.334,  25.899, 'C'),  # GLY 104
        ( -2.966,  28.674,  22.741, 'C'),  # MET 105
        ( -0.198,  31.311,  24.004, 'C'),  # ASN 106
        (  1.318,  28.213,  25.647, 'C'),  # ALA 107
        (  2.373,  27.554,  22.109, 'C'),  # TRP 108
        (  5.273,  29.861,  21.288, 'C'),  # VAL 109
        (  4.482,  29.466,  17.435, 'C'),  # ALA 110
        (  0.461,  30.322,  17.182, 'C'),  # TRP 111
        (  1.318,  33.289,  19.203, 'C'),  # ARG 112
        (  4.219,  34.673,  16.993, 'C'),  # ASN 113
        (  2.769,  33.355,  13.455, 'C'),  # ARG 114
        ( -1.121,  32.564,  13.771, 'C'),  # CYS 115
        ( -2.373,  34.937,  16.677, 'C'),  # LYS 116
        ( -4.153,  37.639,  15.224, 'C'),  # GLY 117
        ( -4.087,  36.519,  11.370, 'C'),  # THR 118
        ( -7.185,  35.200,   9.475, 'C'),  # ASP 119
        ( -6.592,  31.311,  10.676, 'C'),  # VAL 120
        ( -9.954,  30.520,   8.591, 'C'),  # GLN 121
        ( -7.844,  30.652,   5.306, 'C'),  # ALA 122
        ( -6.262,  27.290,   6.759, 'C'),  # TRP 123
        ( -9.756,  25.576,   6.570, 'C'),  # ILE 124
        (-10.877,  27.026,   3.411, 'C'),  # ARG 125
        (-11.602,  24.588,   0.695, 'C'),  # GLY 126
        (-12.327,  21.951,   3.411, 'C'),  # CYS 127
        (-15.359,  19.710,   3.601, 'C'),  # ARG 128
        (-15.952,  19.907,   7.264, 'C'),  # LEU 129
    ],
}

# Insulin A-chain (PDB: 4INS) - 21 residues
# Blood sugar regulation - first protein sequenced (Sanger, Nobel 1958)
# First recombinant protein drug (1982)
INSULIN = {
    'name': 'INSULIN',
    'pdb': '4INS',
    'description': 'Blood sugar hormone',
    'residues': 21,
    'categories': ['signaling', 'disease', 'nobel'],
    'backbone': [
        ( -9.929,  17.026,  13.244, 'H'),  # GLY 1
        (-10.488,  14.266,  10.600, 'H'),  # ILE 2
        ( -6.966,  12.901,  10.576, 'H'),  # VAL 3
        ( -6.889,  12.474,  14.295, 'H'),  # GLU 4
        (-10.407,  11.299,  14.630, 'H'),  # GLN 5
        (-10.050,   8.518,  12.065, 'H'),  # CYS 6
        ( -6.964,   7.186,  13.808, 'H'),  # CYS 7
        ( -7.862,   7.732,  17.520, 'H'),  # THR 8
        (-11.509,   6.803,  17.121, 'H'),  # SER 9
        (-13.350,   5.723,  13.932, 'H'),  # ILE 10
        (-14.665,   7.679,  10.880, 'C'),  # CYS 11
        (-16.999,   6.978,   8.005, 'H'),  # SER 12
        (-16.530,   7.444,   4.259, 'H'),  # LEU 13
        (-19.282,  10.035,   4.368, 'H'),  # TYR 14
        (-17.178,  12.138,   6.774, 'H'),  # GLN 15
        (-14.185,  11.826,   4.470, 'H'),  # LEU 16
        (-16.223,  13.179,   1.589, 'H'),  # GLU 17
        (-16.029,  16.534,   3.332, 'C'),  # ASN 18
        (-12.358,  16.724,   2.380, 'C'),  # TYR 19
        (-12.838,  16.309,  -1.389, 'C'),  # CYS 20
        (-12.404,  19.399,  -3.608, 'C'),  # ASN 21
    ],
}

# List of all proteins
PROTEINS = [
    UBIQUITIN,
    MYOGLOBIN,
    LYSOZYME,
    INSULIN,
]


class Proteins(Visual):
    name = "PROTEINS"
    description = "3D protein backbone structures"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.protein_idx = 0
        self.rotation_y = 0.0  # Manual: left/right
        self.tilt_x = 0.0      # Manual: up/down
        self.rotation_z = 0.0  # Continuous auto-rotate around Z
        self.auto_rotate_speed = 0.3
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 15.0  # Longer view time for proteins
        self.label_timer = 0.0
        self.scroll_offset = 0.0  # For scrolling long text
        self._prepare_protein()

    def _prepare_protein(self):
        """Pre-compute scale and centering for current protein."""
        protein = PROTEINS[self.protein_idx]
        backbone = protein['backbone']

        if len(backbone) == 0:
            self.scale = 1.0
            self.offset = (0, 0, 0)
            return

        # Center of mass
        cx = sum(r[0] for r in backbone) / len(backbone)
        cy = sum(r[1] for r in backbone) / len(backbone)
        cz = sum(r[2] for r in backbone) / len(backbone)
        self.offset = (cx, cy, cz)

        # Find maximum extent
        max_r = 0.0
        for r in backbone:
            dx, dy, dz = r[0] - cx, r[1] - cy, r[2] - cz
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            max_r = max(max_r, dist)

        # Scale to fit display (leave room for labels)
        target_radius = 24.0
        self.scale = target_radius / max_r if max_r > 0 else 1.0
        self.label_timer = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False
        rotation_speed = 2.0  # Radians per second for manual control
        tilt_speed = 1.5

        # Joystick controls rotation (Y and X axes)
        # Any manual rotation pauses auto-cycle until button press
        if input_state.left:
            self.rotation_y -= rotation_speed * 0.016  # Assume ~60fps
            self.auto_cycle = False  # Pause auto-cycle while exploring
            consumed = True
        if input_state.right:
            self.rotation_y += rotation_speed * 0.016
            self.auto_cycle = False
            consumed = True
        if input_state.up:
            self.tilt_x -= tilt_speed * 0.016
            self.auto_cycle = False
            consumed = True
        if input_state.down:
            self.tilt_x += tilt_speed * 0.016
            self.auto_cycle = False
            consumed = True

        # Action buttons cycle through proteins and resume auto-cycle
        if input_state.action_l:
            self.protein_idx = (self.protein_idx - 1) % len(PROTEINS)
            self.cycle_timer = 0.0
            self.auto_cycle = True  # Resume auto-cycle
            self._prepare_protein()
            consumed = True
        if input_state.action_r:
            self.protein_idx = (self.protein_idx + 1) % len(PROTEINS)
            self.cycle_timer = 0.0
            self.auto_cycle = True  # Resume auto-cycle
            self._prepare_protein()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20  # Scroll speed in pixels/sec

        # Continuous auto-rotate around Z axis
        self.rotation_z += self.auto_rotate_speed * dt

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                self.protein_idx = (self.protein_idx + 1) % len(PROTEINS)
                self._prepare_protein()

    def _transform_point(self, x, y, z):
        """Apply rotation and project to screen coords."""
        # Center
        x -= self.offset[0]
        y -= self.offset[1]
        z -= self.offset[2]

        # Scale
        x *= self.scale
        y *= self.scale
        z *= self.scale

        # Auto-rotation around Z axis (constant tumble)
        cos_z, sin_z = math.cos(self.rotation_z), math.sin(self.rotation_z)
        x1 = x * cos_z - y * sin_z
        y1 = x * sin_z + y * cos_z

        # Manual tilt (rotation around X axis) - controlled by up/down
        cos_t, sin_t = math.cos(self.tilt_x), math.sin(self.tilt_x)
        y2 = y1 * cos_t - z * sin_t
        z2 = y1 * sin_t + z * cos_t

        # Manual rotation around Y axis - controlled by left/right
        cos_r, sin_r = math.cos(self.rotation_y), math.sin(self.rotation_y)
        x2 = x1 * cos_r + z2 * sin_r
        z3 = -x1 * sin_r + z2 * cos_r

        # Orthographic projection
        screen_x = GRID_SIZE // 2 + x2
        screen_y = 28 - y2  # Slight offset from center for label room

        return screen_x, screen_y, z3

    def draw(self):
        self.display.clear(Colors.BLACK)

        protein = PROTEINS[self.protein_idx]
        backbone = protein['backbone']

        if len(backbone) < 2:
            return

        # Transform all backbone points
        transformed = []
        for x, y, z, ss in backbone:
            sx, sy, sz = self._transform_point(x, y, z)
            transformed.append((sx, sy, sz, ss))

        # Build draw list: segments between consecutive residues
        # We'll draw back-to-front for proper occlusion
        segments = []
        for i in range(len(transformed) - 1):
            x1, y1, z1, ss1 = transformed[i]
            x2, y2, z2, ss2 = transformed[i + 1]
            avg_z = (z1 + z2) / 2
            # Use the secondary structure of the first residue for color
            segments.append((avg_z, x1, y1, x2, y2, ss1, i))

        # Sort by z (back to front)
        segments.sort(key=lambda s: s[0])

        # Draw backbone segments
        for seg in segments:
            _, x1, y1, x2, y2, ss, idx = seg
            color = SS_COLORS.get(ss, SS_COLORS['C'])

            # Apply depth shading
            avg_z = seg[0]
            depth_factor = 0.5 + 0.5 * (avg_z / 30.0 + 0.5)
            depth_factor = max(0.3, min(1.0, depth_factor))

            shaded = (
                int(color[0] * depth_factor),
                int(color[1] * depth_factor),
                int(color[2] * depth_factor),
            )

            # Draw thicker line for helices and sheets
            self._draw_backbone_segment(x1, y1, x2, y2, shaded, ss)

        # Draw small dots at Cα positions for structure
        for i, (sx, sy, sz, ss) in enumerate(transformed):
            color = SS_COLORS.get(ss, SS_COLORS['C'])
            depth_factor = 0.5 + 0.5 * (sz / 30.0 + 0.5)
            depth_factor = max(0.3, min(1.0, depth_factor))
            dot_color = (
                int(color[0] * depth_factor),
                int(color[1] * depth_factor),
                int(color[2] * depth_factor),
            )
            # Just the center pixel for Cα
            ix, iy = int(round(sx)), int(round(sy))
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, dot_color)

        # Draw label at bottom - cycle through name, description, PDB ID
        cycle = int(self.label_timer / 6) % 3
        if cycle == 0:
            label = protein['name']
        elif cycle == 1:
            label = protein['description']
        else:
            label = f"PDB: {protein['pdb']}"

        # Reset scroll when label changes
        if not hasattr(self, '_last_cycle') or self._last_cycle != cycle:
            self._last_cycle = cycle
            self.scroll_offset = 0

        # Scroll long text (4px per char, ~14 chars fit on screen)
        max_chars = 14
        if len(label) > max_chars:
            # Add padding for smooth loop
            padded = label + "    " + label
            char_width = 4
            total_width = len(label + "    ") * char_width
            offset = int(self.scroll_offset) % total_width
            self.display.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            self.display.draw_text_small(2, 58, label, Colors.WHITE)

    def _draw_backbone_segment(self, x1, y1, x2, y2, color, ss):
        """Draw a backbone segment with thickness based on secondary structure."""
        ix1, iy1 = int(round(x1)), int(round(y1))
        ix2, iy2 = int(round(x2)), int(round(y2))

        # Draw main line
        self.display.draw_line(ix1, iy1, ix2, iy2, color)

        # For helices and sheets, draw thicker (offset lines)
        if ss in ('H', 'G', 'I', 'E', 'B'):
            # Calculate perpendicular offset for thickness
            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                # Perpendicular unit vector
                px = -dy / length
                py = dx / length

                # Draw parallel lines for thickness
                dimmed = (color[0] // 2, color[1] // 2, color[2] // 2)
                self.display.draw_line(
                    int(round(x1 + px)), int(round(y1 + py)),
                    int(round(x2 + px)), int(round(y2 + py)),
                    dimmed
                )
                self.display.draw_line(
                    int(round(x1 - px)), int(round(y1 - py)),
                    int(round(x2 - px)), int(round(y2 - py)),
                    dimmed
                )
