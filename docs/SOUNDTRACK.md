# HOLLOW MAN: THE SECOND SHADOW — Original Soundtrack

### Music by **Synth Centric**

Every cue is an original composition written for the Game Boy Color's four-channel sound
hardware. Nothing is sampled or streamed: the game's own driver (`src/audio.c`) plays note
data compiled from `assets/music/songs.py` on the real APU channels.

## Recorded tracks (GBA version)

The GBA version can also play Synth Centric's own recordings in place of a chip cue. They are
listed in `assets/music/audio/tracks.py` and converted at build time (`tools/audio_convert.py`:
mono, signed 8-bit, 18,157 Hz) then streamed by DMA to the GBA's Direct Sound channel A. Sound
effects keep playing on the Game Boy channels on top. The GBC version cannot play recordings
and keeps the chip arrangement for these cues.

| Cue | Recording | Length | Music Player title |
|---|---|---|---|
| Title screen | `assets/music/audio/title_intro.wav` (01. Intro) | 68.9 s, loops | Intro |

**Adding another recording:** put the WAV (16/24/32-bit, any rate, mono or stereo) in
`assets/music/audio/`, add a line to `TRACKS` in `tracks.py` with the cue id from
`assets/music/songs.py` (e.g. `'gloam'`), a title of up to 16 characters and whether it loops,
then run `make gba`. Each minute of audio adds about 1.1 MB to the ROM (GBA limit: 32 MB).

## The cues

| # | Title | Where it plays | Mood / idea | Tempo |
|---|---|---|---|---|
| 01 | **Second Shadow** | Title screen | Slow D-minor drone; the Hollow Motif (D–F–E–A) answered by the tritone G#; heartbeat kick | 6 frames/row |
| 02 | **Gloam, Midnight** | City streets (Commercial Strip) | Dusty boom-bap at ~90 BPM, swung hats, Dm7–Bbmaj7–Gm7–A7, plucked minor chords, sparse lead | 5 |
| 03 | **Mercy Street** | Mercy Street, Mrs. Hale's house, the old house | Music-box F# minor lament on a ghostly vibrato lead over octave arps | 7 |
| 04 | **Cold Storage** | Industrial Quarter and Vale Cold Storage | Mechanical 16th-note growl bass, rim-shot machinery, stabbing pitch-drop lead | 5 |
| 05 | **Red Lantern** | Red Lantern district, motel, bar | Sleazy C-minor noir with swung drums and walking pluck chords | 5 |
| 06 | **St. Agnes** | Old Gloam, the church, the crypt | Organ-like octave arpeggios in A minor, slow choral lead, distant rumble and bell | 7 |
| 07 | **The Drain** | The canal and the storm drains | Near silence: dripping rim clicks, growling drone, isolated notes | 6 |
| 08 | **Records Room** | Police Records Annex | Ticking detective pulse in B minor, steady eighth-note bass | 5 |
| 09 | **The Last Ward** | Hospital grounds and wards | C# drone, dissonant swells, heartbeat; the most sparse cue | 7 |
| 10 | **Pursuit** | Boss encounters, lockdown, chases | Driving 16th bass, fast snare fills, the motif at full speed | 4 |
| 11 | **The Eighth Man** | Supernatural events, the cellar | Swelling D / G# tritone pads, rumble and crash | 8 |
| 12 | **Victor Rusk** | Final confrontation (ruined chapel) | Pursuit material re-harmonised; motif climbs to G# then A | 4 |
| 13 | **Not Tonight** | Endings and credits | Bittersweet lo-fi F major turning to D minor, the motif finally resolved | 6 |
| 14 | **Pawn & Pray** | Chapter 1: the pawnshop | Plucked A-minor hustle over boom-bap | 5 |
| 15 | **One Less Name** | Chapter-complete jingle | The motif once, with a crash | 6 |
| 16 | **Dead Air** | Game over | Descending chromatic lead into silence | 8 |

The spec's thirteen required cues map to tracks 01–13; 14–16 are additional.

## Implementation

- **Channels:** pulse 1 = lead (shared with sound effects), pulse 2 = harmony / arpeggio,
  wave = bass, noise = drums.
- **Format:** per-channel byte streams (note / rest / hold, length, instrument, loop) with one
  row = `speed` frames. A bar is 32 rows; at speed 5 that is ~90 BPM in swung 16ths.
- **Instruments:** ten pulse instruments (duty + envelope + effect: vibrato, minor arpeggio,
  octave arpeggio, pitch-drop stab, slow swell), five wave instruments over four custom
  waveforms (triangle, saw, sine, growl), eight noise drums (kick, snare, hats, dusty snare,
  rumble, crash, rim).
- **Driver:** runs in the VBlank interrupt (60 Hz). Song data lives in ROM banks; the interrupt
  switches to the song's bank and restores the interrupted bank afterwards.
- **Sound effects** (20) play on pulse 1 or noise; while an effect owns a channel the music on
  that channel keeps time silently and resumes on its next note.
- **The Second Shadow's influence** reaches the music: at *Awakened* every plain lead note gains
  a slow, sick vibrato; at *Possession* the vibrato deepens and lurches.
- **Music Player:** title menu → MUSIC PLAYER. Tracks unlock when you first hear them in the
  game (entering a district) or find hidden cassettes (the diner, the bar, the abandoned house,
  the Mercy Street cellar). It uses the game's own driver and shows a four-channel visualiser.

All music © Synth Centric.
