#!/bin/bash
#
# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

SRC="smw_music/data/resources.qrc"
DST="smw_music/ui/resources.py"

rcc ${SRC} -g python -o ${DST}
sed -i                          \
    -e 's/PySide2/PyQt6/'       \
    -e '6 i # type: ignore\n'   \
    -e '6 i # Library imports'  \
    ${DST}
black ${DST}
