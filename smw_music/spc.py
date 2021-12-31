# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Utilities for SPC file handling.

Notes
-----
See [1]_ for SPC file format specification.  Ambiguities in the specification
(e.g., multi-byte endian, text formats, etc.) were resolved by referencing the
sources for SPCAmp [2]_.

References
----------
.. [1] SPC File Format. http://snesmusic.org/files/spc_file_format.txt
.. [2] SPCAmp v3.1 Source. http://www.alpha-ii.com/Source/SAmp310s.rar
"""


###############################################################################
# Standard Library imports
###############################################################################

import struct

from dataclasses import dataclass, field
from typing import cast, ClassVar, Dict, List, Optional, Union

###############################################################################
# Package imports
###############################################################################

from . import SmwMusicException

###############################################################################
# Private function definitions
###############################################################################


def _decode(binstr: bytes) -> str:
    return binstr.rstrip(b"\x00").decode("ascii")


###############################################################################


def _encode(string: str, width: int) -> bytes:
    return string.encode("ascii").ljust(width, b"\x00")


###############################################################################
# API class definitions
###############################################################################


class SpcException(SmwMusicException):
    """SPC Exceptions."""


###############################################################################


@dataclass
class Chunk:
    chunk_type: str
    subchunks: List["Subchunk"]

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data: bytes) -> "Chunk":
        subchunks = []
        subchunk_type = data[:4].decode("ascii")
        data = data[4:]
        while data:
            subchunk = Subchunk.from_binary(data)
            subchunks.append(subchunk)
            data = data[subchunk.padded_length :]

        return cls(subchunk_type, subchunks)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        return (
            self.chunk_type.encode("ascii")
            + self.chunk_size.to_bytes(4, "little")
            + b"".join(subchunk.binary for subchunk in self.subchunks)
        )

    ###########################################################################

    @property
    def chunk_size(self) -> int:
        return sum(subchunk.padded_length for subchunk in self.subchunks)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self):
        if self.chunk_type != "xid6":
            raise SpcException(f"Invalid chunk type: {self.chunk_type}")


###############################################################################


@dataclass
class DspRegisters:
    regs: bytes

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data: bytes) -> "DspRegisters":
        return cls(data[:64])

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        return self.regs

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self):
        if len(self.regs) != 64:
            raise SpcException(
                f"Invalid DSP register length: {len(self.regs)}"
            )


###############################################################################


@dataclass
class ExtraRam:
    ram: bytes

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data: bytes) -> "ExtraRam":
        return cls(data[:64])

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        return self.ram

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self):
        if len(self.ram) != 64:
            raise SpcException(f"Invalid ExtraRam ram length: {len(self.ram)}")


###############################################################################


@dataclass
class Header:
    file_header: str = "SNES-SPC700 Sound File Data v0.30"
    contains_id666: bool = True
    version: int = 30
    _FILL: ClassVar[bytes] = bytes([26, 26])
    _ID666_FIELD: ClassVar[Dict[bool, int]] = {False: 27, True: 26}

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data: bytes) -> "Header":
        file_header = data[:33].decode("ascii")
        fill = data[33:35]
        contains_id666_field = int(data[35])
        version = int(data[36])

        if fill != cls._FILL:
            raise SpcException(f"Invalid header fill: {fill!r}")

        for key, val in cls._ID666_FIELD.items():
            if contains_id666_field == val:
                contains_id666 = key
                break
        else:
            raise SpcException(
                f"Invalid ID666 header field: {contains_id666_field}"
            )

        return cls(file_header, contains_id666, version)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        id666_flag = bytes([self._ID666_FIELD[self.contains_id666]])
        return (
            _encode(self.file_header, 33)
            + self._FILL
            + id666_flag
            + bytes([self.version])
        )

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self):
        if len(self.file_header) != 33:
            raise SpcException(
                f"Invalid file header length: {len(self.file_header)}"
            )

        if not 0 <= self.version < 256:
            raise SpcException(f"Invalid file header version: {self.version}")


###############################################################################


@dataclass
class Id666Tag:  # pylint: disable=too-many-instance-attributes
    song_title: str
    game_title: str
    dumper_name: str
    comments: str
    dump_date: Union[str, int]
    secs: int
    fade_ms: int
    artist: str
    default_disables: int
    emulator: str
    unused: bytes = bytes(7)

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(  # pylint: disable=too-many-locals
        cls, data: bytes
    ) -> "Id666Tag":
        song_title = _decode(data[:32])
        game_title = _decode(data[32:64])
        dumper_name = _decode(data[64:80])
        comments = _decode(data[80:112])
        dump_date: Union[int, str]

        # This is pretty poor way to figure out if the
        if data[164] in b"012":
            # text ID tag
            dump_date = _decode(data[112:123])
            unused = b""
            secs = int(_decode(data[123:126]))
            fade_ms = int(_decode(data[126:129]))
            artist_offset = 131
        else:
            # binary ID tag
            # Endian isn't actually specified (it never is, why would it be
            # here?), so assuming x86
            dump_date = int.from_bytes(data[112:116], "little")
            unused = data[116:123]
            secs = int.from_bytes(data[123:126], "little")
            fade_ms = int.from_bytes(data[126:130], "little")
            artist_offset = 130

        offset_end = artist_offset + 32
        artist = _decode(data[artist_offset:offset_end])
        default_disables = data[offset_end]
        emulator = chr(data[offset_end + 1])
        reserved = data[offset_end + 2 : 256]

        if any(reserved):
            raise SpcException(f"Invalid ID666 Reserved: {reserved!r}")

        return cls(
            song_title,
            game_title,
            dumper_name,
            comments,
            dump_date,
            secs,
            fade_ms,
            artist,
            default_disables,
            emulator,
            unused,
        )

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        rv = bytearray(210)
        rv[:32] = _encode(self.song_title, 32)
        rv[32:64] = _encode(self.game_title, 32)
        rv[64:80] = _encode(self.dumper_name, 16)
        rv[80:112] = _encode(self.comments, 32)

        if self.text_format:
            rv[112:122] = cast(str, self.dump_date).encode("ascii")
            rv[123:126] = f"{self.secs:03}".encode("ascii")
            rv[126:131] = f"{self.fade_ms:05}".encode("ascii")
            artist_offset = 131
        else:
            rv[112:116] = cast(int, self.dump_date).to_bytes(4, "little")
            rv[116:123] = self.unused
            rv[123:126] = self.secs.to_bytes(3, "little")
            rv[126:130] = self.fade_ms.to_bytes(4, "little")
            artist_offset = 130

        offset_end = artist_offset + 32
        rv[artist_offset:offset_end] = _encode(self.artist, 32)
        rv[offset_end] = self.default_disables
        rv[offset_end + 1] = ord(self.emulator)

        return bytes(rv)

    ###########################################################################

    @property
    def dump_day(self) -> int:
        if self.text_format:
            rv = int(cast(str, self.dump_date)[6:8])
        else:
            rv = 0xFF & (cast(int, self.dump_date) >> 24)
        return rv

    ###########################################################################

    @property
    def dump_month(self) -> int:
        if self.text_format:
            rv = int(cast(str, self.dump_date)[4:6])
        else:
            rv = 0xFF & (cast(int, self.dump_date) >> 16)
        return rv

    ###########################################################################

    @property
    def dump_year(self) -> int:
        if self.text_format:
            rv = int(cast(str, self.dump_date)[:4])
        else:
            rv = 0xFFFF & cast(int, self.dump_date)
        return rv

    ###########################################################################

    @property
    def emu_name(self) -> str:
        return {"0": "Unknown", "1": "ZSNES", "2": "Snes9x"}.get(
            self.emulator, "???"
        )

    ###########################################################################

    @property
    def text_format(self) -> bool:
        return isinstance(self.dump_date, str)

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self):
        if len(self.song_title) > 32:
            raise SpcException(
                f"Invalid song title length: {len(self.song_title)}"
            )

        if len(self.game_title) > 32:
            raise SpcException(
                f"Invalid game title length: {len(self.game_title)}"
            )

        if len(self.dumper_name) > 16:
            raise SpcException(
                f"Invalid dumper name length: {len(self.dumper_name)}"
            )

        if len(self.comments) > 32:
            raise SpcException(f"Invalid comment length: {len(self.comments)}")

        if self.text_format:
            if len(self.dump_date) != 10:
                raise SpcException(
                    f"Invalid dump date length: {len(self.dump_date)}"
                )

        # These limits are taken from the Alpha-II sources
        if not 0 <= self.secs < 960:
            raise SpcException(f"Invalid seconds: {self.secs}")

        if not 0 <= self.fade_ms < 60000:
            raise SpcException(f"Invalid fade ms: {self.fade_ms}")

        if len(self.artist) > 32:
            raise SpcException(
                f"Invalid song artist length: {len(self.artist)}"
            )

        if not 0 <= self.default_disables < 256:
            raise SpcException(
                f"Invalid default disables: {self.default_disables}"
            )

        if self.emulator not in "012":
            raise SpcException(f"Invalid emulator: {self.emulator}")


###############################################################################


@dataclass
class Ram:
    ram: bytes

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data: bytes) -> "Ram":
        return cls(data[:65536])

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        return self.ram

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self):
        if len(self.ram) != 64 * 1024:
            raise SpcException(f"Invalid RAM length: {len(self.ram)}")


###############################################################################


@dataclass
class Registers:
    pc: int  # pylint: disable=C0103
    a: int  # pylint: disable=C0103
    x: int  # pylint: disable=C0103
    y: int  # pylint: disable=C0103
    psw: int
    sp: int  # pylint: disable=C0103
    reserved: bytes

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data: bytes) -> "Registers":
        if len(data) < 9:
            raise SpcException(f"Not enough registers: {len(data)}")

        regs = struct.unpack_from("<H5B", data)
        reserved = data[7:9]
        pc, a, x, y, psw, sp = regs  # pylint: disable=C0103

        return cls(pc, a, x, y, psw, sp, reserved)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        return struct.pack(
            "<H7B",
            self.pc,
            self.a,
            self.x,
            self.y,
            self.psw,
            self.sp,
            *self.reserved,
        )

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self):
        if not 0 <= self.pc < 65536:
            raise SpcException(f"Invalid Register PC: {self.pc}")
        for reg in ["a", "x", "y", "psw", "sp"]:
            val = getattr(self, reg)
            if not 0 <= val < 256:
                raise SpcException(f"Invalid Register {reg}: {val}")
        if len(self.reserved) != 2:
            raise SpcException(
                f"Invalid Register reserved data: {self.reserved}"
            )


###############################################################################


@dataclass
class Spc:  # pylint: disable=too-many-instance-attributes
    header: Header
    regs: Registers = field(repr=False)
    tag: Optional[Id666Tag]
    ram: Ram = field(repr=False)
    dsp_regs: DspRegisters = field(repr=False)
    extra_ram: ExtraRam = field(repr=False)
    chunk: Optional[Chunk]
    unused: bytes = field(default=bytes(64), repr=False)

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data: bytes) -> "Spc":
        header = Header.from_binary(data[0x0:0x25])
        regs = Registers.from_binary(data[0x25:0x2E])
        if header.contains_id666:
            tag = Id666Tag.from_binary(data[0x2E:0x100])
        else:
            tag = None
        ram = Ram.from_binary(data[0x100:0x10100])
        dsp_regs = DspRegisters.from_binary(data[0x10100:0x10180])
        unused = data[0x10180:0x101C0]
        extra_ram = ExtraRam.from_binary(data[0x101C0:0x10200])
        if len(data) > 0x10200:
            chunk = Chunk.from_binary(data[0x10200:])
        else:
            chunk = None

        return cls(header, regs, tag, ram, dsp_regs, extra_ram, chunk, unused)

    ###########################################################################

    @classmethod
    def from_file(cls, fname) -> "Spc":
        with open(fname, "rb") as fobj:
            return cls.from_binary(fobj.read())

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        if self.tag is not None:
            tag = self.tag.binary
        else:
            tag = bytes(256 - 33)

        if self.chunk is not None:
            chunk = self.chunk.binary
        else:
            chunk = b""

        return (
            self.header.binary
            + self.regs.binary
            + tag
            + self.ram.binary
            + self.dsp_regs.binary
            + self.unused
            + self.extra_ram.binary
            + chunk
        )


###############################################################################


@dataclass
class Subchunk:
    subchunk_id: int
    subchunk_type: int
    data: Union[str, int]
    _LENGTH_TYPE: ClassVar[int] = 0
    _STRING_TYPE: ClassVar[int] = 1
    _INTEGER_TYPE: ClassVar[int] = 4

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, data) -> "Subchunk":
        subchunk_id = data[0]
        subchunk_type = data[1]
        length = int.from_bytes(data[2:4], "little")

        if subchunk_type == cls._LENGTH_TYPE:
            subchunk_data = length
        elif subchunk_type == cls._STRING_TYPE:
            if not 4 <= length <= 256:
                raise SpcException(f"Invalid subchunk string length: {length}")
            subchunk_data = data[4 : (4 + length)]
        elif subchunk_type == cls._INTEGER_TYPE:
            if not 4 == length:
                raise SpcException(
                    f"Invalid subchunk integer length: {length}"
                )
            subchunk_data = int.from_bytes(data[4:8], "little")
        else:
            raise SpcException(f"Invalid subchunk type: {subchunk_type}")

        return cls(subchunk_id, subchunk_type, subchunk_data)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        return b""

    ###########################################################################

    @property
    def padded_length(self) -> int:
        if self.subchunk_type == self._LENGTH_TYPE:
            rv = 4
        elif self.subchunk_type == self._STRING_TYPE:
            rv = 4 + ((len(cast(str, self.data)) + 3) & 0xFF)
        elif self.subchunk_type == self._INTEGER_TYPE:
            rv = 8
        else:
            raise SpcException(
                f"Bad subchunk type in padded_length: {self.subchunk_type}"
            )
        return rv

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __str__(self) -> str:
        str_map = {
            0x01: "Song name",
            0x02: "Game name",
            0x03: "Artist's name",
            0x04: "Dumper's name",
            0x05: "Dump date",
            0x06: "Emulator",
            0x07: "Comments",
            0x10: "Official Soundtrack Title",
            0x11: "OST disc",
            0x12: "OST track",
            0x13: "Publisher's name",
            0x14: "Copyright year",
            0x30: "Intro length (ticks)",
            0x31: "Loop length (ticks)",
            0x32: "End length (ticks)",
            0x33: "Fade length (ticks)",
            0x34: "Muted channels",
            0x35: "Number of times to loop",
            0x36: "Amplification value",
        }

        return f"{str_map[self.subchunk_id]}: {self.data}"
