"""Regression checks for global state, privacy and integer conservation."""

import csv
import io
import tempfile
import unittest
from pathlib import Path

from bank_workbench.bank_core import COLUMNS, Config, execute_pipeline
from bank_workbench.demo import demo_csv


class PipelineTests(unittest.TestCase):
    def test_demo_expected_filters(self):
        # Hand-counted periodic demo records, independent of pipeline predicates.
        report = execute_pipeline(
            demo_csv(), config=Config(relative_last_name="حسنپور")
        )
        expected = {
            1: 10,
            2: 10,
            3: 50,
            4: 5,
            5: 5,
            6: 50,
            7: 5,
            8: 13,
            9: 26,
            10: 12,
            11: 25,
            12: 17,
            13: 20,
            14: 10,
            15: 15,
            17: 5,
            20: 5,
        }
        self.assertEqual({q: report.questions[q]["count"] for q in expected}, expected)
        self.assertEqual(
            report.questions[14]["summary"],
            {"accepted": 10, "rejected": 5, "undecided": 35},
        )

    def test_all_questions_chunk_independent(self):
        a = execute_pipeline(demo_csv(), chunksize=1)
        b = execute_pipeline(demo_csv(), chunksize=17)
        self.assertEqual(a.questions, b.questions)
        self.assertEqual(set(a.questions), set(range(1, 21)))
        self.assertEqual(a.questions[20]["preview"], [])
        self.assertNotIn("20", a.notebook_payload())
        self.assertEqual(a.questions[6]["count"], 50)
        self.assertEqual(a.questions[9]["summary"]["1290"]["average_age"], 110)
        q = a.questions[17]["summary"]
        self.assertEqual(q["total_before"], q["total_after"])
        self.assertEqual(q["donor_row"], 11)  # Richest is also a dorm recipient.

    def test_no_recipients_and_invalid_id(self):
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(COLUMNS)
        writer.writerow(
            [
                "123456789012",
                "وانيا",
                "نمونه",
                "پدر",
                "1395/01/01",
                "نمونه",
                "فارس",
                "",
                "",
            ]
        )
        report = execute_pipeline(stream.getvalue().encode())
        self.assertEqual(report.questions[8]["count"], 1)
        self.assertEqual(report.stats["invalid_national_ids"], 1)
        self.assertEqual(report.questions[17]["summary"]["recipients"], 0)
        self.assertEqual(report.questions[3]["count"], 0)
        self.assertEqual(
            report.questions[1]["preview"][0]["national_id"], "123456789012"
        )

    def test_export_private_and_preserves_files(self):
        report = execute_pipeline(
            demo_csv(), config=Config(relative_last_name="حسنپور")
        )
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "private.csv"
            self.assertEqual(report.export_relative_csv(target), 5)
            before = target.read_bytes()
            with self.assertRaises(FileExistsError):
                report.export_relative_csv(target)
            self.assertEqual(target.read_bytes(), before)
            source = Path(folder) / "source.csv"
            source.write_bytes(demo_csv())
            local = execute_pipeline(source)
            with self.assertRaises(ValueError):
                local.export_relative_csv(source)

    def test_validation(self):
        with self.assertRaises(ValueError):
            execute_pipeline(b"first_name\nexample\n")
        with self.assertRaises(ValueError):
            execute_pipeline(demo_csv(), chunksize=0)
        with self.assertRaises(ValueError):
            execute_pipeline(demo_csv(), config=Config(birth_date="1380/13/01"))
        with self.assertRaises(ValueError):
            execute_pipeline(demo_csv(), config=Config(relative_last_name="نمونه"))

    def test_original_schema(self):
        records = list(csv.DictReader(io.StringIO(demo_csv().decode("utf-8-sig"))))
        stream = io.StringIO()
        fields = [
            "national_code",
            "FULL_NAME",
            "FATHER_NAME",
            "BIRTH_DATE",
            "BIRTH_CITY",
            "BIRTH_PROVINCE",
            "CITY_NAME",
            "PROVINCE_NAME",
        ]
        writer = csv.writer(stream)
        writer.writerow(fields)
        for row in records:
            writer.writerow(
                [
                    row["national_id"],
                    row["first_name"] + " " + row["last_name"],
                    row["father_name"],
                    row["birth_date"],
                    row["birth_city"],
                    row["birth_province"],
                    row["residence_city"],
                    row["residence_province"],
                ]
            )
        canonical = execute_pipeline(demo_csv())
        legacy = execute_pipeline(stream.getvalue().encode("utf-8"))
        self.assertEqual(
            [q["count"] for q in canonical.questions.values()],
            [q["count"] for q in legacy.questions.values()],
        )

    def test_unicode_and_mutation(self):
        report = execute_pipeline(demo_csv())
        self.assertGreater(
            report.questions[1]["summary"]["raw_unicode_character_counts"][
                "persian_ye"
            ],
            0,
        )
        self.assertIn("tm_balance", report.questions[18]["preview"][0])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.csv"
            source.write_bytes(demo_csv())
            report = execute_pipeline(source)
            source.write_bytes(demo_csv() + b"\n")
            with self.assertRaises(ValueError):
                report.export_relative_csv(Path(folder) / "result.csv")

            def mutate(event):
                if event["pass"] == 1:
                    source.write_bytes(demo_csv() + b"\n\n")

            with self.assertRaises(ValueError):
                execute_pipeline(source, chunksize=50, progress=mutate)


if __name__ == "__main__":
    unittest.main()
