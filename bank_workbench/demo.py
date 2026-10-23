"""Fictional small dataset; no original or personal records are distributed."""

import csv
import io


def demo_csv():
    from bank_workbench.bank_core import COLUMNS

    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(COLUMNS)
    names = [
        "علیزاده",
        "حسنپور",
        "حسینی مهدوی",
        "احمدی",
        "رضایی نژاد",
        "محمدی پور",
        "اصغری",
        "جعفری",
        "آزاده",
        "نمونه",
    ]
    for i in range(50):
        writer.writerow(
            [
                str(i + 1),
                ["وانیا", "آرمان", "نازنین", "نمونه"][i % 4],
                names[i % 10],
                "پژمان" if i % 2 else "نمونه",
                ["1295/01/01", "1395/02/02", "1380/01/01", "1375/03/03"][i % 4],
                "نمونه",
                "فارس",
                "خلخال" if i % 3 == 0 else "نمونه",
                ["هرمزگان", "اصفهان", "مرکزی", "خوزستان", ""][i % 5],
            ]
        )
    return stream.getvalue().encode("utf-8-sig")
