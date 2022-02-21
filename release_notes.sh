#!/bin/bash
# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: CC0-1.0

pandoc -s --wrap=none -o /tmp/CHANGELOG.md CHANGELOG.rst
