import music21  # type: ignore


def convert(fname: str, ofname: str):
    duration_map = {
        4: 1,
        5: 2,
        6: 4,
        7: 8,
        8: 16,
        9: 32,
    }

    stream = music21.converter.parseFile(fname)

    notes = []
    note_str = []

    for s in stream:
        if isinstance(s, music21.metadata.Metadata):
            composer = s.composer
            title = s.title
        elif isinstance(s, music21.stream.Part):
            for el in s.flatten():
                if isinstance(el, music21.tempo.MetronomeMark):
                    tempo = el.getQuarterBPM()
                    spc_tempo = int(tempo * 256 / 625)

                if isinstance(el, music21.note.Note):
                    notes.append(el)

    for note in notes:
        octave = note.octave
        dur = duration_map[note.duration.ordinal]
        name = note.name.lower().replace("#", "+")
        note_str.append(f"o{octave} {name}{dur}")

    spc = ["#amk 2"]
    spc.append("")
    spc.append("#spc")
    spc.append("{")
    spc.append(f'#author  "{composer}"')
    spc.append(f'#title   "{title}"')
    spc.append("}")
    spc.append(f"#0 w255 t{spc_tempo}")
    spc.append("@9 v150 o5")
    spc.append(" ".join(note_str))

    with open(ofname, "w") as fobj:
        print("\r\n".join(spc), end="\r\n", file=fobj)
