"""Recorded tracks by Synth Centric that replace chip music cues in the GBA version.
id (see assets/music/songs.py) -> (wav file in this folder, Music Player title (<=16 chars), loop)
The GBC version cannot play recordings and keeps the chip arrangement for these cues."""
TRACKS = {
    'title': ('title_intro.wav', 'Intro', True),
}
