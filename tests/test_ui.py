"""Regression checks for real Streamlit workflows."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60
        ).run()

    def test_demo_questions_and_stale_results(self):
        app = self.app()
        self.assertFalse(app.exception)
        next(b for b in app.button if b.label == "Run all 20 questions").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["report"].questions), 20)
        next(s for s in app.selectbox if s.label == "Question").select(9).run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any("Average age" in frame.value.columns for frame in app.dataframe)
        )
        next(s for s in app.selectbox if s.label == "Question").select(20).run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any("Relative records are private" in info.value for info in app.info)
        )
        original = app.session_state["report"]
        next(
            t for t in app.text_input if t.label == "Relative’s last name (Q20)"
        ).set_value("changed").run()
        self.assertTrue(any("Inputs changed" in w.value for w in app.warning))
        self.assertEqual(app.session_state["report"].stats, original.stats)

    def test_private_export_refuses_repository_destination(self):
        import tempfile
        app = self.app()
        next(b for b in app.button if b.label == "Run all 20 questions").click().run()
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as folder:
            destination = Path(folder) / "private.csv"
            next(t for t in app.text_input if t.label == "Private destination CSV path").set_value(str(destination)).run()
            next(b for b in app.button if b.label == "Export private Q20 CSV").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any("outside this repository" in error.value for error in app.error))
            self.assertFalse(destination.exists())

    def test_every_machine_traces(self):
        app = self.app()
        for kind in ["suffix", "vowel", "credit", "risk", "balance"]:
            next(s for s in app.selectbox if s.label == "Machine").select(kind).run()
            next(b for b in app.button if b.label == "Trace machine").click().run()
            self.assertFalse(app.exception, kind)
            self.assertTrue(app.json, kind)
            if app.slider:
                app.slider[0].set_value(1).run()
                self.assertFalse(app.exception, kind)
                self.assertTrue(
                    any("Result:" in heading.value for heading in app.subheader)
                )


    def test_empty_word_machine_traces_show_verdict_without_index_error(self):
        app = self.app()
        for kind in ['suffix', 'vowel']:
            next(s for s in app.selectbox if s.label == 'Machine').select(kind).run()
            next(t for t in app.text_input if t.label == 'Name / last name').set_value('').run()
            next(b for b in app.button if b.label == 'Trace machine').click().run()
            self.assertFalse(app.exception, kind)
            self.assertTrue(any('Result: Rejected' in h.value for h in app.subheader))
            self.assertTrue(any('Empty input' in info.value for info in app.info))


if __name__ == "__main__":
    unittest.main()
