#!/bin/sh
## SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
## <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
##
## SPDX-License-Identifier: AGPL-3.0-only

wine ./AddmusicK.exe -c -norom -visualize "${project}.txt" < /dev/null
