#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# Standard library imports
import pathlib
import xml.etree.ElementTree as ET
from typing import cast

uis = [
    ("dashboard.ui", "dashboard_view.py", "DashboardView"),
    ("preferences.ui", "preferences_view.py", "PreverencesView"),
]

base_dir = pathlib.Path("smw_music")

lic = """\
# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only
"""

for ui_fname, py_fname, module in uis:
    tree = ET.parse(base_dir / "data" / ui_fname)
    root = tree.getroot()
    top = root[1]  # Gets the top-level widget
    widgets: dict[str, str] = {}
    actions: list[str] = []

    for widget in top.findall(".//widget"):
        widget_name = cast(str, widget.get("name"))
        widget_class = cast(str, widget.get("class"))
        widgets[widget_name] = widget_class

    for action in top.findall(".//addaction"):
        actions.append(cast(str, action.get("name")))

    widget_set = set(widgets.values())
    widget_set.add(cast(str, top.get("class")))

    with open(base_dir / "ui" / py_fname, "w", encoding="utf8") as fobj:
        print(lic, file=fobj)
        print("# Generated from a tool, do not manually update.", file=fobj)
        print("", file=fobj)
        print("# Library imports", file=fobj)
        if actions:
            print("from PyQt6.QtGui import QAction", file=fobj)
        print("from PyQt6.QtWidgets import (", file=fobj)
        for widget_class in sorted(widget_set):
            print(f"    {widget_class},", file=fobj)
        print(")", file=fobj)
        print("", file=fobj)
        print("", file=fobj)
        print(f"class {module}(QMainWindow):", file=fobj)
        for widget_name in sorted(widgets):
            print(f"    {widget_name}: {widgets[widget_name]}", file=fobj)
