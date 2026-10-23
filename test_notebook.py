"""Verify exported notebook execution, ordering and the private-output boundary."""

import contextlib
import io
import json
import unittest

from bank_core import Config, execute_pipeline
from demo import demo_csv
from notebook_builder import build_notebook


class NotebookTests(unittest.TestCase):
    def test_executed_and_replayable(self):
        report = execute_pipeline(demo_csv())
        document = json.loads(build_notebook(report))
        code = [c for c in document["cells"] if c["cell_type"] == "code"]
        self.assertEqual(len(code), 20)
        self.assertEqual(code[-1]["outputs"], [])
        self.assertTrue(all(c["outputs"] for c in code[:-1]))
        self.assertIn("image/svg+xml", code[8]["outputs"][1]["data"])
        # Fresh namespace actually rereads the demo; chart capture replaces display only.
        namespace = {"_capture_svg": lambda value: None}
        for cell in code:
            with contextlib.redirect_stdout(io.StringIO()):
                exec("".join(cell["source"]), namespace)
        self.assertEqual(namespace["report"].questions, report.questions)

    def test_private_exports_omit_rows_and_criteria(self):
        report = execute_pipeline(
            demo_csv(), config=Config(relative_last_name="حسنپور")
        )
        document = json.loads(build_notebook(report, source_label="Local CSV path"))
        code = [c for c in document["cells"] if c["cell_type"] == "code"]
        self.assertNotIn("relative_last_name': 'حسنپور'", "".join(code[0]["source"]))
        for cell in code:
            for output in cell["outputs"]:
                self.assertNotIn('"preview"', "".join(output.get("text", [])))
        self.assertEqual(code[-1]["outputs"], [])


if __name__ == "__main__":
    unittest.main()
