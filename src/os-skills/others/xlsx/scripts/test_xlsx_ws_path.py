#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for find_ws_path in xlsx_insert_row.py and xlsx_add_column.py.

Per OPC (ECMA-376 Part 2), a relationship Target without a leading "/" is
relative to the directory of the source part (xl/ for workbook.xml), which
is also the form Excel itself writes and the form used by the skill's own
minimal_xlsx template. A leading "/" denotes a package-absolute part name.
"""

import importlib
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

WORKBOOK_TEMPLATE = (
    '<?xml version="1.0"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<sheets><sheet name="Budget" sheetId="1" r:id="rId1"/></sheets></workbook>'
)

RELS_TEMPLATE = (
    '<?xml version="1.0"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"'
    ' Target="{target}"/></Relationships>'
)

SHEET_TEMPLATE = (
    '<?xml version="1.0"?>'
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<sheetData><row r="1"><c r="A1"><v>1</v></c></row></sheetData></worksheet>'
)


def make_work_dir(target: str) -> str:
    """Build a minimal unpacked-xlsx work dir whose sheet rels use `target`."""
    work = tempfile.mkdtemp(prefix="xlsx_ws_path_")
    os.makedirs(os.path.join(work, "xl", "worksheets"))
    os.makedirs(os.path.join(work, "xl", "_rels"))
    with open(os.path.join(work, "xl", "workbook.xml"), "w", encoding="utf-8") as fh:
        fh.write(WORKBOOK_TEMPLATE)
    with open(os.path.join(work, "xl", "_rels", "workbook.xml.rels"), "w", encoding="utf-8") as fh:
        fh.write(RELS_TEMPLATE.format(target=target))
    with open(os.path.join(work, "xl", "worksheets", "sheet1.xml"), "w", encoding="utf-8") as fh:
        fh.write(SHEET_TEMPLATE)
    return work


class FindWsPathTest(unittest.TestCase):
    """Both scripts must resolve the same workbook.xml.rels conventions."""

    MODULES = ("xlsx_insert_row", "xlsx_add_column")

    def _resolved_matches_actual(self, module_name: str, work: str) -> None:
        module = importlib.import_module(module_name)
        resolved = module.find_ws_path(work, "Budget")
        expected = os.path.join(work, "xl", "worksheets", "sheet1.xml")
        self.assertEqual(os.path.normpath(resolved), os.path.normpath(expected))
        self.assertTrue(os.path.isfile(resolved))

    def test_relative_target_resolves_against_xl_dir(self):
        """Excel's own form: Target="worksheets/sheet1.xml" (relative to xl/)."""
        work = make_work_dir("worksheets/sheet1.xml")
        for module_name in self.MODULES:
            with self.subTest(module=module_name):
                self._resolved_matches_actual(module_name, work)

    def test_package_absolute_target_resolves_from_root(self):
        """Package-absolute form: Target="/xl/worksheets/sheet1.xml"."""
        work = make_work_dir("/xl/worksheets/sheet1.xml")
        for module_name in self.MODULES:
            with self.subTest(module=module_name):
                self._resolved_matches_actual(module_name, work)

    def test_default_sheet_resolution(self):
        """Passing sheet_name=None picks the first sheet."""
        work = make_work_dir("worksheets/sheet1.xml")
        module = importlib.import_module("xlsx_insert_row")
        resolved = module.find_ws_path(work, None)
        self.assertTrue(os.path.isfile(resolved))


if __name__ == "__main__":
    unittest.main()
