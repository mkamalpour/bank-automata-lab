"""Bounded, replayable coursework pipeline. All money is integer IRR."""

import csv
import hashlib
import io
import os
import random
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bank_workbench.automata import balance_tm, credit_nfa, normalize, risk_nfa, suffix_dfa, vowel_dfa

COLUMNS = "national_id first_name last_name father_name birth_date birth_city birth_province residence_city residence_province".split()
CAPITALS = dict(
    zip(
        "تهران|اصفهان|فارس|خراسان رضوی|آذربایجان شرقی|آذربایجان غربی|اردبیل|البرز|ایلام|بوشهر|چهارمحال و بختیاری|خراسان جنوبی|خراسان شمالی|خوزستان|زنجان|سمنان|سیستان و بلوچستان|گیلان|گلستان|هرمزگان|همدان|کرمان|کرمانشاه|کهگیلویه و بویراحمد|کردستان|لرستان|مازندران|مرکزی|یزد|قزوین|قم".split(
            "|"
        ),
        "تهران|اصفهان|شیراز|مشهد|تبریز|ارومیه|اردبیل|کرج|ایلام|بوشهر|شهرکرد|بیرجند|بجنورد|اهواز|زنجان|سمنان|زاهدان|رشت|گرگان|بندرعباس|همدان|کرمان|کرمانشاه|یاسوج|سنندج|خرم آباد|ساری|اراک|یزد|قزوین|قم".split(
            "|"
        ),
    )
)
TITLES = [
    "Random dataset scan",
    "Fill residence province",
    "Standardize national IDs",
    "Alizadeh in Hormozgan",
    "Dormitory ADDRESS",
    "Unique card numbers",
    "Hosseini Mahdavi",
    "Vania count",
    "Age cohorts",
    "Birth-date twins",
    "Persian father-name letters",
    "Khalkhal residents",
    "Suffix DFA rejections",
    "Credit NFA",
    "Vowel DFA",
    "Risk NFA",
    "Redistribute richest balance",
    "Balance Turing machine",
    "VIP customers",
    "Private relatives",
]
RULES = {
    2: "Fill missing residence_province with the birth province capital, as specified by the assignment; unknown provinces remain blank.",
    4: "Exact normalized surname علیزاده and residence province هرمزگان.",
    5: "Exact surname حسنپور and residence province اصفهان receive ADDRESS خوابگاه امینیان.",
    6: "3550 followed by a 12-digit global zero-based row counter.",
    7: "Exact normalized surname حسینی مهدوی.",
    8: "Exact normalized first name وانیا.",
    10: "Exact normalized configured birth date.",
    11: "Father name contains at least one of گ چ پ ژ.",
    12: "Exact residence city خلخال.",
    13: "Count names rejected by the suffix DFA (must end in ی or پور).",
    15: "DFA requires an allowed vowel before the last character and final ز ژ و ه.",
    16: "NFA accepts at least two of the three specified risk conditions.",
    18: "TM output is مسدود above 100 billion IRR; numeric balance is retained separately.",
    19: "First name begins آ, active balance exceeds 1 billion IRR, and province is مرکزی.",
}
ALIASES = {
    "national_code": "national_id",
    "FATHER_NAME": "father_name",
    "BIRTH_DATE": "birth_date",
    "CITY_NAME": "residence_city",
    "PROVINCE_NAME": "residence_province",
    "BIRTH_CITY": "birth_city",
    "BIRTH_PROVINCE": "birth_province",
    "FIRST_NAME": "first_name",
    "LAST_NAME": "last_name",
}


@dataclass(frozen=True)
class Config:
    seed: int = 42
    reference_year: int = 1405
    birth_date: str = "1380/01/01"
    relative_last_name: str = ""
    relative_city: str = ""
    balance_max: int = 200_000_000_001
    preview_limit: int = 20


def _chunks(source, size):
    """Read strings without losing leading zeros or treating names as NA."""
    stream = io.BytesIO(source) if isinstance(source, bytes) else Path(source)
    accepted = set(COLUMNS) | set(ALIASES) | {"FULL_NAME"}
    with pd.read_csv(
        stream,
        chunksize=size,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
        usecols=lambda column: str(column).strip() in accepted,
    ) as reader:
        for chunk in reader:
            chunk.columns = [str(c).strip() for c in chunk.columns]
            for old, new in ALIASES.items():
                if old in chunk and new not in chunk:
                    chunk[new] = chunk[old]
            if "FULL_NAME" in chunk:
                # Legacy schema lacks separate names: first token is assumed given name.
                parts = chunk["FULL_NAME"].map(
                    lambda value: value.strip().split(maxsplit=1) or [""]
                )
                if "first_name" not in chunk:
                    chunk["first_name"] = parts.map(lambda value: value[0])
                if "last_name" not in chunk:
                    chunk["last_name"] = parts.map(
                        lambda value: value[1] if len(value) > 1 else ""
                    )
            missing = set(COLUMNS) - set(chunk.columns)
            if missing:
                raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
            yield chunk


def _fingerprint(source):
    if isinstance(source, bytes):
        return hashlib.sha256(source).hexdigest()
    info = Path(source).stat()
    return (
        str(Path(source).resolve()),
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _rows(source, size, config):
    """Normalize independently of chunk boundaries; replay seeded RNG each pass."""
    rng = random.Random(config.seed)
    index = 0
    for chunk in _chunks(source, size):
        for raw in chunk.to_dict("records"):
            row = {key: normalize(str(raw[key])) for key in COLUMNS}
            row["_arabic_ye"] = sum(str(raw[k]).count("ي") for k in COLUMNS)
            row["_persian_ye"] = sum(str(raw[k]).count("ی") for k in COLUMNS)
            row["_row"] = index
            row["_filled"] = (
                not row["residence_province"] and row["birth_province"] in CAPITALS
            )
            if row["_filled"]:
                row["residence_province"] = CAPITALS[row["birth_province"]]
            national = row["national_id"]
            row["national_id_valid"] = bool(re.fullmatch(r"[0-9]{1,10}", national))
            row["national_id"] = (
                national.zfill(10) if row["national_id_valid"] else national
            )
            row["card_number"] = f"3550{index:012d}"
            if index >= 10**12:
                raise ValueError("Card-number capacity exceeded")
            row["ADDRESS"] = (
                "خوابگاه امینیان"
                if row["last_name"] == "حسنپور"
                and row["residence_province"] == "اصفهان"
                else ""
            )
            year = re.match(r"^(\d{4})[/.-]", row["birth_date"])
            row["_year"] = int(year[1]) if year else 0
            row["account_balance"] = rng.randrange(100_000, config.balance_max)
            yield row
            index += 1


def _public(row):
    return {k: v for k, v in row.items() if not k.startswith("_")}


def _relative(row, config):
    surname = normalize(config.relative_last_name)
    if not surname or row["last_name"] != surname:
        return False
    suffix = surname.endswith(
        ("پور", "زاده", "نژاد", "وند", "منش", "فر", "پژوه", "خانی", "زاد")
    )
    return (
        suffix
        or bool(normalize(config.relative_city))
        and row["residence_city"] == normalize(config.relative_city)
    )


@dataclass
class Report:
    questions: dict
    stats: dict
    config: Config
    _source: object
    _chunksize: int
    _fingerprint: object

    def notebook_payload(self):
        """No row previews or personal matching criteria in notebook summaries."""
        return {
            str(k): {x: v for x, v in q.items() if x != "preview"}
            for k, q in self.questions.items()
            if k != 20
        }

    def export_relative_csv(self, destination):
        """Write private matches atomically; never overwrite input or existing work."""
        target = Path(destination).expanduser().resolve()
        if _fingerprint(self._source) != self._fingerprint:
            raise ValueError("Source changed since processing; run the pipeline again")
        if (
            not isinstance(self._source, bytes)
            and target == Path(self._source).resolve()
        ):
            raise ValueError("Export cannot overwrite the source CSV")
        if target.exists():
            raise FileExistsError(
                "Choose a new export filename; existing files are preserved"
            )
        temporary = None
        count = 0
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8-sig",
                newline="",
                dir=target.parent,
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                for row in _rows(self._source, self._chunksize, self.config):
                    if _relative(row, self.config):
                        writer.writerow({k: row[k] for k in COLUMNS})
                        count += 1
            # Exclusive link avoids a race overwriting a newly created destination.
            if _fingerprint(self._source) != self._fingerprint:
                raise ValueError("Source changed during export; export cancelled")
            os.link(temporary, target)
            return count
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def execute_pipeline(source, chunksize=100_000, config=Config(), progress=None):
    """Two streaming passes find global donor then apply exact redistribution."""
    if not isinstance(chunksize, int) or chunksize < 1:
        raise ValueError("Chunk size must be a positive integer")
    if config.balance_max <= 100_000 or not 0 <= config.preview_limit <= 100:
        raise ValueError("Invalid balance maximum or preview limit (0–100)")
    if not re.fullmatch(
        r"\d{4}/(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])", normalize(config.birth_date)
    ):
        raise ValueError(
            "Birth date must use YYYY/MM/DD with month 01–12 and day 01–31"
        )
    surname = normalize(config.relative_last_name)
    if (
        surname
        and not surname.endswith(
            ("پور", "زاده", "نژاد", "وند", "منش", "فر", "پژوه", "خانی", "زاد")
        )
        and not normalize(config.relative_city)
    ):
        raise ValueError("Relative city is required for a surname without a suffix")
    fingerprint = _fingerprint(source)
    header_source = io.BytesIO(source) if isinstance(source, bytes) else Path(source)
    original_columns = list(
        pd.read_csv(header_source, nrows=0, encoding="utf-8-sig").columns
    )
    questions = {
        i: dict(title=TITLES[i - 1], count=0, summary={}, preview=[])
        for i in range(1, 21)
    }
    total = recipients = total_before = invalid = 0
    richest = None
    sample = []
    sampler = random.Random(config.seed)
    unicode_counts = {"arabic_ye": 0, "persian_ye": 0}
    for row in _rows(source, chunksize, config):
        total += 1
        recipients += bool(row["ADDRESS"])
        total_before += row["account_balance"]
        invalid += not row["national_id_valid"]
        unicode_counts["arabic_ye"] += row["_arabic_ye"]
        unicode_counts["persian_ye"] += row["_persian_ye"]
        if richest is None or row["account_balance"] > richest["account_balance"]:
            richest = row.copy()
        if len(sample) < 10:
            sample.append(_public(row))
        else:
            slot = sampler.randrange(total)
            if slot < 10:
                sample[slot] = _public(row)
        if progress and total % chunksize == 0:
            progress({"pass": 1, "rows": total, "total": None})
    if not total:
        raise ValueError("CSV contains no records")
    if _fingerprint(source) != fingerprint:
        raise ValueError("Source changed during first pass; processing cancelled")
    share, remainder = (
        divmod(richest["account_balance"], recipients) if recipients else (0, 0)
    )
    recipient_index = total_after = replay_rows = 0
    cohorts = {1290: [0, 0], 1390: [0, 0]}
    credit = {"accepted": 0, "rejected": 0, "undecided": 0}
    for row in _rows(source, chunksize, config):
        replay_rows += 1
        if recipients and row["_row"] == richest["_row"]:
            row["account_balance"] = 0
        if row["ADDRESS"]:
            row["account_balance"] += share + (recipient_index < remainder)
            recipient_index += 1
        total_after += row["account_balance"]
        row["account_status"] = (
            "blocked" if balance_tm(row["account_balance"]) == "مسدود" else "active"
        )
        row["tm_balance"] = (
            "مسدود" if row["account_status"] == "blocked" else row["account_balance"]
        )
        year = row["_year"]
        for start in cohorts:
            if start <= year <= start + 9:
                cohorts[start][0] += 1
                cohorts[start][1] += config.reference_year - year
        verdict = credit_nfa(row["last_name"], year, trace=True)
        label = {"accept": "accepted", "reject": "rejected", "review": "undecided"}.get(
            verdict.get("decision"),
            "accepted" if verdict.get("accepted") else "undecided",
        )
        credit[label] = credit.get(label, 0) + 1
        masks = {
            2: row["_filled"],
            3: row["national_id_valid"],
            4: row["last_name"] == "علیزاده" and row["residence_province"] == "هرمزگان",
            5: bool(row["ADDRESS"]),
            6: True,
            7: row["last_name"] == "حسینی مهدوی",
            8: row["first_name"] == "وانیا",
            9: any(s <= year <= s + 9 for s in cohorts),
            10: row["birth_date"] == normalize(config.birth_date),
            11: bool(re.search("[گچپژ]", row["father_name"])),
            12: row["residence_city"] == "خلخال",
            13: not suffix_dfa(row["last_name"]),
            14: label == "accepted",
            15: vowel_dfa(row["last_name"]),
            16: risk_nfa(
                row["first_name"], row["last_name"], year, row["residence_province"]
            ),
            17: bool(row["ADDRESS"]),
            18: row["account_status"] == "blocked",
            19: row["first_name"].startswith("آ")
            and row["account_status"] == "active"
            and row["account_balance"] > 1_000_000_000
            and row["residence_province"] == "مرکزی",
            20: _relative(row, config),
        }
        for number, match in masks.items():
            if match:
                q = questions[number]
                q["count"] += 1
                if number != 20 and len(q["preview"]) < config.preview_limit:
                    q["preview"].append(_public(row))
        if progress and (row["_row"] + 1) % chunksize == 0:
            progress({"pass": 2, "rows": row["_row"] + 1, "total": total})
    if _fingerprint(source) != fingerprint:
        raise ValueError("Source changed during second pass; processing cancelled")
    if (
        replay_rows != total
        or recipient_index != recipients
        or total_after != total_before
    ):
        raise ValueError(
            "Replay consistency or money conservation failed; discard this run"
        )
    for number, question in questions.items():
        question["summary"] = {
            "rule": RULES.get(number, TITLES[number - 1]),
            "matching_rows": question["count"],
        }
    questions[1].update(
        count=len(sample),
        preview=sample[: config.preview_limit],
        summary={
            "sampling": "Seeded reservoir sample across all rows",
            "columns": original_columns,
            "canonical_columns": COLUMNS,
            "read_dtype": "string (preserves leading zeros)",
            "raw_unicode_character_counts": unicode_counts,
            "legacy_full_name_rule": "First whitespace token is the given name, remainder surname. Compound given names are ambiguous; use canonical first_name/last_name columns to resolve.",
        },
    )
    questions[3]["summary"] = {
        "invalid_ids_preserved": invalid,
        "rule": "Only 1–10 ASCII digits after normalization; invalid values are never truncated",
    }
    questions[9]["summary"] = {
        str(s): {"count": c, "average_age": age / c if c else None}
        for s, (c, age) in cohorts.items()
    }
    questions[14]["summary"] = credit
    questions[17]["summary"] = {
        "recipients": recipients,
        "donor_row": richest["_row"],
        "donor_balance": richest["account_balance"],
        "share": share,
        "remainder": remainder,
        "total_before": total_before,
        "total_after": total_after,
        "policy": "Zero donor then add equal integer shares; first recipients receive remainder. No recipients: no transfer.",
    }
    questions[20]["summary"] = {
        "private": True,
        "export": "Explicit CSV export only; no row preview",
    }
    if progress:
        progress({"pass": 2, "rows": total, "total": total})
    return Report(
        questions,
        {
            "rows": total,
            "passes": 2,
            "chunksize": chunksize,
            "invalid_national_ids": invalid,
            "total_balance": total_after,
        },
        config,
        source,
        chunksize,
        fingerprint,
    )
