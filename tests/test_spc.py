# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPC Module Tests."""

###############################################################################
# Standard library imports
###############################################################################

import os
import tempfile
import pathlib

###############################################################################
# Library imports
###############################################################################

import pytest

###############################################################################
# Project imports
###############################################################################

from smw_music import spc


###############################################################################
# Test definitions
###############################################################################

###############################################################################
# DspRegister tests
###############################################################################


def test_dsp_registers_long():
    long = bytes(range(65))
    dsp_regs = spc.DspRegisters.from_binary(long)
    assert long[:64] == dsp_regs.regs
    assert long[:64] == dsp_regs.binary

    long = bytes(range(65))
    with pytest.raises(spc.SpcException):
        dsp_regs = spc.DspRegisters(long)


###############################################################################


def test_dsp_registers_short():
    short = bytes(range(63))
    with pytest.raises(spc.SpcException):
        dsp_regs = spc.DspRegisters.from_binary(short)


###############################################################################


@pytest.mark.parametrize(
    "arg",
    [bytes(64), bytes(range(64)), bytes(reversed(range(64)))],
    ids=["zeros", "counter", "rev counter"],
)
def test_dsp_registers_valid(arg):
    dsp_regs = spc.DspRegisters.from_binary(arg)
    assert arg == dsp_regs.regs
    assert arg == dsp_regs.binary


###############################################################################
# ExtraRam tests
###############################################################################


def test_extra_ram_long():
    long = bytes(range(65))
    extra_ram = spc.ExtraRam.from_binary(long)
    assert long[:64] == extra_ram.ram
    assert long[:64] == extra_ram.binary

    long = bytes(range(63))
    with pytest.raises(spc.SpcException):
        extra_ram = spc.ExtraRam(long)


###############################################################################


def test_extra_ram_short():
    short = bytes(range(63))
    with pytest.raises(spc.SpcException):
        extra_ram = spc.ExtraRam.from_binary(short)


###############################################################################


@pytest.mark.parametrize(
    "arg",
    [bytes(64), bytes(range(64)), bytes(reversed(range(64)))],
    ids=["zeros", "counter", "rev counter"],
)
def test_extra_ram_valid(arg):
    extra_ram = spc.ExtraRam.from_binary(arg)
    assert arg == extra_ram.ram
    assert arg == extra_ram.binary


###############################################################################
# Ram tests
###############################################################################


def test_ram_long():
    long = bytes(0xFF & x for x in range(64 * 1024 + 1))
    ram = spc.Ram.from_binary(long)
    assert long[:0x10000] == ram.ram
    assert long[:0x10000] == ram.binary

    long = bytes(0xFF & x for x in range(64 * 1024 + 1))
    with pytest.raises(spc.SpcException):
        ram = spc.Ram(long)


###############################################################################


def test_ram_short():
    short = bytes(0xFF & x for x in range(64 * 1024 - 1))
    with pytest.raises(spc.SpcException):
        ram = spc.Ram.from_binary(short)


###############################################################################


@pytest.mark.parametrize(
    "arg",
    [
        bytes(64 * 1024),
        bytes(0xFF & x for x in range(64 * 1024)),
        bytes(0xFF & x for x in reversed(range(64 * 1024))),
    ],
    ids=["zeros", "counter", "rev counter"],
)
def test_ram_valid(arg):
    ram = spc.Ram.from_binary(arg)
    assert arg == ram.ram
    assert arg == ram.binary


###############################################################################
# Registers tests
###############################################################################


def test_registers_long():
    arg = bytes(range(10))
    regs = spc.Registers.from_binary(arg)
    assert arg[:9] == regs.binary


###############################################################################


@pytest.mark.parametrize(
    "arg, match",
    [
        ((-1, 0, 0, 0, 0, 0, b"\x00\x00"), r"Register PC"),
        ((65536, 0, 0, 0, 0, 0, b"\x00\x00"), r"Register PC"),
        ((0, -1, 0, 0, 0, 0, b"\x00\x00"), r"Register a"),
        ((0, 256, 0, 0, 0, 0, b"\x00\x00"), r"Register a"),
        ((0, 0, -1, 0, 0, 0, b"\x00\x00"), r"Register x"),
        ((0, 0, 256, 0, 0, 0, b"\x00\x00"), r"Register x"),
        ((0, 0, 0, -1, 0, 0, b"\x00\x00"), r"Register y"),
        ((0, 0, 0, 256, 0, 0, b"\x00\x00"), r"Register y"),
        ((0, 0, 0, 0, -1, 0, b"\x00\x00"), r"Register psw"),
        ((0, 0, 0, 0, 256, 0, b"\x00\x00"), r"Register psw"),
        ((0, 0, 0, 0, 0, -1, b"\x00\x00"), r"Register sp"),
        ((0, 0, 0, 0, 0, 256, b"\x00\x00"), r"Register sp"),
        ((0, 0, 0, 0, 0, 0, b"\x00"), "Register reserved"),
        ((0, 0, 0, 0, 0, 0, b"\x00\x00\x00"), "Register reserved"),
    ],
    ids=[
        "PC low",
        "PC high",
        "A low",
        "A high",
        "X low",
        "X high",
        "Y low",
        "Y high",
        "PSW low",
        "PSW high",
        "SP low",
        "SP high",
        "reserved short",
        "reserved long",
    ],
)
def test_registers_invalid(arg, match):
    with pytest.raises(spc.SpcException, match=match):
        regs = spc.Registers(*arg)


###############################################################################


def test_registers_short():
    arg = bytes(8)
    with pytest.raises(spc.SpcException):
        regs = spc.Registers.from_binary(arg)


###############################################################################


@pytest.mark.parametrize(
    "arg",
    [bytes(9), bytes(range(9)), bytes(reversed(range(9)))],
    ids=["zeros", "counter", "rev counter"],
)
def test_registers_valid(arg):
    regs = spc.Registers.from_binary(arg)
    assert arg == regs.binary

    assert regs.pc == int.from_bytes(arg[:2], "little")
    assert regs.a == arg[2]
    assert regs.x == arg[3]
    assert regs.y == arg[4]
    assert regs.psw == arg[5]
    assert regs.sp == arg[6]
    assert regs.reserved == arg[7:]
