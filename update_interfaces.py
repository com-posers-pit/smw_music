#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# Standard library imports
import pathlib
import xml.etree.ElementTree as ET
from collections import defaultdict
from contextlib import redirect_stdout
from typing import cast

uis = [
    ("dashboard.ui", "dashboard_view.py", "DashboardView"),
    ("preferences.ui", "preferences_view.py", "PreferencesView"),
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
    custom_widgets: defaultdict[str, list[str]] = defaultdict(lambda: [])

    for widget in top.findall(".//widget"):
        widget_name = cast(str, widget.get("name"))
        widget_class = cast(str, widget.get("class"))
        widgets[widget_name] = widget_class

    for action in top.findall(".//action"):
        actions.append(cast(str, action.get("name")))

    widget_set = set(widgets.values())
    top_class = cast(str, top.get("class"))
    widget_set.add(top_class)

    for widget in root.findall(".//customwidget"):
        widget_class = widget.find("class").text
        header = widget.find("header").text.replace("/", ".")
        custom_widgets[header].append(widget_class)
        widget_set.remove(widget_class)

    fname = base_dir / "ui" / py_fname
    with open(fname, "w", encoding="utf8") as fobj, redirect_stdout(fobj):
        print(lic)
        print("# Generated from a tool, do not manually update.")
        print("")
        print("# Library imports")
        if actions:
            print("from PyQt6.QtGui import QAction")
        print("from PyQt6.QtWidgets import (")
        for widget_class in sorted(widget_set):
            print(f"    {widget_class},")
        print(")")
        if custom_widgets:
            print("")
            print("# Package imports")
        for widget_module in sorted(custom_widgets.keys()):
            imports = ",".join(custom_widgets[widget_module])
            print(f"from {widget_module} import {imports}")
        print("")
        print("")

        print(f"class {module}({top_class}):")
        for action in actions:
            widgets[action] = "QAction"
        for widget_name in sorted(widgets):
            print(f"    {widget_name}: {widgets[widget_name]}")
