"""Input integrity and trace-free execution preserve the coursework answers."""
import csv
import io
import unittest

from bank_workbench.automata import credit_decision, credit_nfa, risk_nfa
from bank_workbench.bank_core import COLUMNS, Config, execute_pipeline
from bank_workbench.demo import demo_csv


class InputIntegrityTests(unittest.TestCase):
    def test_duplicate_actual_headers_are_not_silently_mangled(self):
        for duplicate in ('national_id', ' national_id '):
            with self.subTest(duplicate=duplicate):
                stream=io.StringIO();writer=csv.writer(stream)
                writer.writerow([*COLUMNS,duplicate])
                writer.writerow(['1','A','B','C','1380/01/01','X','X','X','X','999'])
                with self.assertRaisesRegex(ValueError,'Duplicate CSV'):
                    execute_pipeline(stream.getvalue().encode())

    def test_invalid_integer_settings_fail_before_processing(self):
        for setting,value in [('preview_limit',.5),('balance_max',200000.5),('seed',True),('reference_year',float('nan'))]:
            with self.subTest(setting=setting,value=value):
                events=[]
                with self.assertRaisesRegex(ValueError,'whole integer'):
                    execute_pipeline(demo_csv(),config=Config(**{setting:value}),progress=events.append)
                self.assertEqual(events,[])
        with self.assertRaises(ValueError):execute_pipeline(demo_csv(),chunksize=True)

    def test_fast_verdict_and_teaching_trace_agree(self):
        names=['احمدی','رضایی نژاد','محمدیپور','نمونه','']
        for name in names:
            for year in [1369,1370,1404,1405,'۱۳۷۰',None,1370.9]:
                with self.subTest(name=name,year=year):
                    self.assertEqual(credit_decision(name,year),credit_nfa(name,year,trace=True)['decision'])

    def test_fractional_year_is_not_silently_truncated(self):
        self.assertEqual(credit_decision('احمدی',1370.9),'review')
        self.assertEqual(credit_decision('احمدی','۱۳۷۰'),'reject')
        # A fractional year cannot satisfy the birth-year evidence predicate.
        trace=risk_nfa('الف','اصغری',1360.5,'هرمزگان',trace=True)
        self.assertFalse(trace['evidence'][0])

    def test_valid_data_remains_chunk_independent(self):
        for chunksize in [1,11,5000]:
            result=execute_pipeline(demo_csv(),chunksize=chunksize)
            self.assertEqual(result.questions,execute_pipeline(demo_csv(),chunksize=7).questions)


if __name__=='__main__':unittest.main()
