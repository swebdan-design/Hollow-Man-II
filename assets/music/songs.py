"""HOLLOW MAN II: THE SECOND SHADOW - original soundtrack by Synth Centric.

Channels: 0 = pulse lead, 1 = pulse harmony/arp, 2 = wave bass, 3 = noise drums.
Rows per bar = 32 (16th notes = 2 rows) unless noted.  speed = frames per row.
Instruments (pulse): 0 lead 1 pluck 2 minor-arp 3 vibrato 4 swell 5 stab-drop
                     6 quiet pad 7 octave-arp 8 ghost 9 loud short
Wave instruments: 0 triangle 1 saw 2 soft sine 3 quiet triangle 4 growl
Drums: k kick, s snare, h hat, o open hat, n dusty snare, w rumble, c crash, x rim

The recurring "Hollow motif": D - F - E - A, answered by the tritone (G#) of
the Second Shadow.
"""


def bar(s, n=32):
    tot = 0
    for t in s.split():
        k, _, v = t.partition(':')
        if k != 'i':
            tot += int(v)
    assert tot == n, (tot, s)
    return s + ' '


def B(*bars, n=32):
    return ''.join(bar(b, n) for b in bars)


def R(s, times):
    return s * times


# ---- drum bars (32 rows, swung boom-bap at speed 5 ~ 90 BPM) ----
BB = bar("k:5 h:3 s:5 h:3 k:3 k:2 h:3 s:5 h:3")
BB2 = bar("k:5 h:3 s:5 h:3 k:5 h:1 k:2 s:3 h:2 n:3")
BBX = bar("k:5 h:3 n:5 h:3 k:3 k:2 h:3 n:5 o:3")
HEART = bar("k:3 k:29")
SPARSE = bar("k:8 r:8 n:8 r:8")
TICK = bar("x:4 h:4 x:4 h:4 x:4 h:4 x:4 h:4")
DRIVE = bar("k:4 h:2 h:2 s:4 h:2 h:2 k:2 k:2 h:2 h:2 s:4 h:2 h:2")
DRIP = bar("x:12 r:10 x:10")
MACH = bar("k:4 x:2 x:2 k:4 x:2 x:2 k:4 x:2 x:2 s:4 x:2 x:2")
SILENT = bar("r:32")

SONGS = []


def song(id, title, speed, ch0, ch1, ch2, ch3, loop=True, where=''):
    SONGS.append(dict(id=id, title=title, speed=speed, ch=[ch0, ch1, ch2, ch3], loop=loop, where=where))


# 0 ---------------------------------------------------------------- TITLE
song('title', 'The Second Shadow', 6,
     'i:3 ' + B("r:16 D4:4 F4:4 E4:8", "A3:24 r:8", "D4:4 F4:4 E4:8 G#4:16", "A4:24 r:8",
                "D5:8 C5:8 A4:8 F4:8", "E4:16 D4:16", "Bb4:12 A4:4 G4:16", "G#4:16 A4:16"),
     'i:4 ' + B("F3:32", "E3:32", "F3:32", "C#3:32", "F3:32", "A3:32", "D3:32", "D3:16 C#3:16"),
     'i:2 ' + B("D2:32", "D2:32", "Bb2:32", "A2:32", "D2:32", "D2:32", "G2:32", "A2:16 G#2:16"),
     HEART * 7 + bar("k:3 k:13 w:16"),
     where='Title screen')

# 1 ---------------------------------------------------------------- GLOAM (overworld)
g_bass = B("D2:6 r:2 D2:4 r:4 A2:4 r:4 C3:4 r:4", "Bb2:6 r:2 Bb2:4 r:4 F2:4 r:4 A2:4 r:4",
           "G2:6 r:2 G2:4 r:4 D2:4 r:4 F2:4 r:4", "A2:6 r:2 A2:4 r:4 E2:4 r:4 C#3:4 r:4")
g_keys = B("i:2 D4:8 F4:8 C5:8 A4:8", "D4:8 F4:8 A4:8 F4:8",
           "Bb3:8 D4:8 F4:8 D4:8", "A3:8 C#4:8 E4:8 G4:8")
song('gloam', 'Gloam at Midnight', 5,
     'i:0 ' + B("r:32", "r:32", "r:32", "r:32",
                "r:8 D5:4 F5:4 E5:8 A4:8", "r:8 D5:4 F5:4 G5:8 F5:4 E5:4",
                "D5:12 C5:4 Bb4:8 A4:8", "G#4:16 A4:16",
                "r:8 A4:4 C5:4 D5:12 r:4", "F5:8 E5:8 D5:8 C5:8",
                "Bb4:8 A4:8 G4:8 F4:8", "E4:24 r:8"),
     'i:1 ' + R(g_keys, 3),
     'i:0 ' + R(g_bass, 3),
     BB * 3 + BB2 + BB * 3 + BB2 + BB * 3 + BBX,
     where='Gloam city streets')

# 2 ---------------------------------------------------------------- MERCY STREET
song('mercy', 'Mercy Street', 7,
     'i:8 ' + B("C#5:8 E5:8 A4:16", "B4:8 C#5:8 F#4:16", "D5:8 C#5:8 B4:8 A4:8", "G#4:24 r:8",
                "C#5:8 E5:8 A5:16", "G#5:8 E5:8 C#5:16", "D5:8 F#4:8 A4:8 C#5:8", "B4:32"),
     'i:7 ' + B("F#3:32", "D3:32", "B2:32", "C#3:32", "F#3:32", "E3:32", "D3:32", "C#3:32"),
     'i:3 ' + B("F#2:16 C#3:16", "D2:16 A2:16", "B2:16 F#2:16", "C#3:16 G#2:16",
                "F#2:16 C#3:16", "E2:16 B2:16", "D2:16 A2:16", "C#3:32"),
     SPARSE * 8,
     where='Mercy Street, the ruined house')

# 3 ---------------------------------------------------------------- INDUSTRIAL
ib = B("E2:2 E2:2 r:2 E2:2 G2:2 r:2 E2:2 r:2 E2:2 E2:2 r:2 B2:2 Bb2:2 r:2 E2:2 r:2")
song('indust', 'Cold Storage', 5,
     'i:5 ' + B("E4:4 r:28", "r:16 G4:4 r:12", "E4:4 r:12 Bb4:4 r:12", "B4:4 r:28",
                "E5:6 D5:6 B4:4 r:16", "G4:6 F#4:6 E4:4 r:16", "Bb4:8 A4:8 G4:8 F#4:8", "E4:16 r:16"),
     'i:6 ' + B("r:32", "r:32", "B3:32", "Bb3:32", "E4:32", "C4:32", "D4:32", "B3:32"),
     'i:4 ' + R(ib, 8),
     MACH * 7 + bar("k:4 x:2 x:2 k:4 x:2 x:2 c:16"),
     where='Industrial Quarter, Cold Storage')

# 4 ---------------------------------------------------------------- RED LANTERN
song('motel', 'Red Lantern', 5,
     'i:3 ' + B("r:8 G4:4 Bb4:4 C5:8 Eb5:8", "D5:12 C5:4 Bb4:8 G4:8", "Ab4:8 C5:8 Eb5:8 D5:8", "B4:24 r:8",
                "r:8 G5:4 F5:4 Eb5:8 C5:8", "D5:8 Bb4:8 G4:16", "Ab4:12 G4:4 F4:8 Eb4:8", "D4:16 B3:16"),
     'i:1 ' + B("C4:4 r:4 Eb4:4 r:4 G4:4 r:4 Eb4:4 r:4", "Bb3:4 r:4 D4:4 r:4 F4:4 r:4 D4:4 r:4",
                "Ab3:4 r:4 C4:4 r:4 Eb4:4 r:4 C4:4 r:4", "G3:4 r:4 B3:4 r:4 D4:4 r:4 F4:4 r:4") * 2,
     'i:0 ' + B("C2:8 r:4 G2:4 C3:8 Bb2:8", "Bb2:8 r:4 F2:4 Bb2:8 A2:8", "Ab2:8 r:4 Eb2:4 Ab2:8 G2:8",
                "G2:8 r:4 D2:4 G2:4 B2:4 D3:8") * 2,
     (BB + BBX) * 4,
     where='Red Lantern Motel')

# 5 ---------------------------------------------------------------- ST. AGNES
song('church', 'St. Agnes', 7,
     'i:3 ' + B("A4:16 C5:16", "B4:16 E4:16", "F4:16 A4:16", "G#4:32",
                "A4:8 B4:8 C5:8 D5:8", "E5:16 D5:16", "C5:8 B4:8 A4:8 F4:8", "E4:32"),
     'i:7 ' + B("A3:32", "E3:32", "F3:32", "E3:32", "A3:32", "C4:32", "F3:32", "E3:32"),
     'i:2 ' + B("A2:32", "G2:32", "F2:32", "E2:32", "A2:32", "G2:32", "D2:32", "E2:32"),
     bar("w:32") + SILENT + bar("x:16 x:16") + SILENT + bar("w:32") + SILENT + bar("x:16 x:16") + bar("c:32"),
     where='St. Agnes Church, Old Gloam')

# 6 ---------------------------------------------------------------- THE DRAIN
song('drain', 'The Drain', 6,
     'i:8 ' + B("r:32", "G4:4 r:12 Bb4:4 r:12", "r:32", "A4:4 r:12 C#5:4 r:12",
                "r:16 D5:4 r:4 C#5:8", "r:32", "G4:4 r:4 Bb4:4 r:4 D5:16", "C#5:32"),
     'i:6 ' + B("D3:32", "D3:32", "Eb3:32", "D3:32", "D3:32", "C3:32", "Bb2:32", "A2:32"),
     'i:4 ' + B("G2:32", "G2:32", "G2:32", "G2:32", "Eb2:32", "Eb2:32", "D2:32", "D2:32"),
     DRIP * 8,
     where='The Drain, beneath Gloam')

# 7 ---------------------------------------------------------------- RECORDS ROOM
song('records', 'Records Room', 5,
     'i:1 ' + B("B4:4 r:4 D5:4 r:4 F#5:4 r:4 D5:4 r:4", "B4:4 r:4 D5:4 r:4 G5:4 r:4 E5:4 r:4",
                "B4:4 r:4 D5:4 r:4 F#5:4 r:4 C#5:4 r:4", "A#4:4 r:4 C#5:4 r:4 F#5:8 r:8") * 2,
     'i:0 ' + B("r:32", "r:32", "r:32", "r:32", "F#4:16 E4:8 D4:8", "E4:16 G4:16", "F#4:8 E4:8 D4:8 C#4:8", "A#3:32"),
     'i:0 ' + B("B2:8 B2:8 B2:8 B2:8", "G2:8 G2:8 G2:8 G2:8", "E2:8 E2:8 E2:8 E2:8", "F#2:8 F#2:8 F#2:8 F#2:8") * 2,
     TICK * 8,
     where='Police Records Annex')

# 8 ---------------------------------------------------------------- THE LAST WARD
song('ward', 'The Last Ward', 7,
     'i:8 ' + B("C#5:16 r:16", "D5:16 r:16", "G4:16 r:16", "G#4:32",
                "C#5:8 E5:8 G5:16", "F#5:16 r:16", "D5:8 Bb4:8 G4:16", "G#4:32"),
     'i:4 ' + B("E3:32", "F3:32", "Bb3:32", "B3:32", "E3:32", "D#3:32", "D3:32", "C#3:32"),
     'i:4 ' + B("C#2:32", "C#2:32", "C#2:32", "C#2:32", "C2:32", "C2:32", "B2:32", "C#2:32"),
     HEART * 3 + bar("w:32") + HEART * 3 + bar("c:32"),
     where='The Last Ward hospital')

# 9 ---------------------------------------------------------------- PURSUIT
pb = B("D2:2 D2:2 D3:2 D2:2 r:2 D2:2 C3:2 D2:2 D2:2 D2:2 F2:2 D2:2 r:2 D2:2 A2:2 G#2:2")
song('pursuit', 'Pursuit', 4,
     'i:9 ' + B("D5:4 r:2 D5:2 F5:4 E5:4 D5:4 r:4 A4:8", "Bb4:4 r:2 Bb4:2 C5:4 D5:4 E5:8 r:8",
                "D5:4 r:2 D5:2 F5:4 G5:4 G#5:8 A5:8", "A5:4 G5:4 F5:4 E5:4 D5:8 C#5:8"),
     'i:2 ' + B("D4:16 D4:16", "Bb3:16 Bb3:16", "D4:16 F4:16", "A3:32"),
     'i:1 ' + R(pb, 4),
     DRIVE * 4,
     where='Combat and pursuit')

# 10 ---------------------------------------------------------------- THE SECOND SHADOW
song('shadow', 'The Eighth Man', 8,
     'i:4 ' + B("D4:32", "G#4:32", "D4:32", "A4:16 G#4:16"),
     'i:4 ' + B("r:8 A3:24", "r:8 D4:24", "r:8 F3:24", "r:8 E3:24"),
     'i:4 ' + B("D2:32", "D2:32", "D2:32", "D2:16 C#2:16"),
     bar("w:32") + SILENT + bar("w:32") + bar("c:32"),
     where='Supernatural encounters')

# 11 ---------------------------------------------------------------- FINAL
fb = B("D2:2 r:2 D2:2 D2:2 A2:2 r:2 D2:2 G#2:2 D2:2 r:2 D2:2 D2:2 F2:2 r:2 E2:2 C#2:2")
song('final', 'Victor Rusk', 4,
     'i:3 ' + B("D5:16 F5:8 E5:8", "A4:16 G#4:16", "D5:8 E5:8 F5:8 G#5:8", "A5:32",
                "Bb5:16 A5:8 G5:8", "F5:16 E5:16", "D5:8 C#5:8 D5:8 E5:8", "D5:16 G#4:16"),
     'i:2 ' + B("D4:32", "D4:32", "Bb3:32", "A3:32", "G3:32", "Bb3:32", "A3:32", "D4:32"),
     'i:4 ' + R(fb, 8),
     DRIVE * 3 + bar("k:4 k:4 k:4 k:4 s:2 s:2 s:2 s:2 s:2 s:2 c:4") +
     DRIVE * 3 + bar("k:4 k:4 k:4 k:4 s:2 s:2 s:2 s:2 s:2 s:2 c:4"),
     where='Final confrontation')

# 12 ---------------------------------------------------------------- ENDING / CREDITS
song('ending', 'Not Tonight', 6,
     'i:0 ' + B("r:8 A4:4 C5:4 F5:8 E5:8", "D5:12 C5:4 A4:16", "r:8 Bb4:4 D5:4 G5:8 F5:8", "E5:24 r:8",
                "r:8 A4:4 C5:4 F5:8 A5:8", "G5:12 F5:4 E5:16", "D5:8 C5:8 Bb4:8 A4:8", "D5:32"),
     'i:1 ' + B("F3:4 A3:4 C4:4 E4:4 F3:4 A3:4 C4:4 E4:4", "D3:4 F3:4 A3:4 C4:4 D3:4 F3:4 A3:4 C4:4",
                "Bb2:4 D3:4 F3:4 A3:4 Bb2:4 D3:4 F3:4 A3:4", "C3:4 E3:4 G3:4 Bb3:4 C3:4 E3:4 G3:4 Bb3:4") * 2,
     'i:0 ' + B("F2:12 r:4 F2:8 C2:8", "D2:12 r:4 D2:8 A2:8", "Bb2:12 r:4 Bb2:8 F2:8", "C2:12 r:4 C2:8 E2:8") * 2,
     BB * 3 + BBX + BB * 3 + BB2,
     where='Endings and credits')

# 13 ---------------------------------------------------------------- PAWNSHOP
song('pawn', 'Pawn & Pray', 5,
     'i:1 ' + B("A4:4 r:4 C5:4 r:4 E5:4 r:4 D5:4 C5:4", "B4:8 G#4:8 E4:16",
                "A4:4 r:4 C5:4 r:4 F5:4 r:4 E5:4 D5:4", "C5:8 B4:8 A4:16"),
     'i:6 ' + B("C4:32", "B3:32", "C4:32", "E4:32"),
     'i:0 ' + B("A2:8 r:4 A2:4 E2:8 G2:8", "E2:8 r:4 E2:4 G#2:8 B2:8", "F2:8 r:4 F2:4 C3:8 A2:8", "E2:8 r:4 E2:4 E2:8 G#2:8"),
     BB + BB2 + BB + BBX,
     where="Chapter 1: Eddie Voss's pawnshop")

# 14 ---------------------------------------------------------------- CHAPTER JINGLE
song('jingle', 'One Less Name', 6,
     'i:3 ' + B("D5:4 F5:4 E5:8 A4:16", "G#4:32"),
     'i:4 ' + B("F4:32", "D4:32"),
     'i:2 ' + B("D2:32", "D2:32"),
     bar("c:32") + SILENT,
     loop=False, where='Chapter complete')

# 15 ---------------------------------------------------------------- GAME OVER
song('gameover', 'Dead Air', 8,
     'i:3 ' + B("A4:8 G#4:8 G4:8 F#4:8", "F4:32"),
     'i:6 ' + B("D4:32", "D4:32"),
     'i:2 ' + B("D2:32", "D2:32"),
     bar("w:32") + SILENT,
     loop=False, where='Game over')
