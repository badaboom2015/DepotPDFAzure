from pathlib import Path
import re
import math
import csv
import io
import pandas as pd

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

ALIASES = {
    "name": ["name", "wertpapier", "wertpapiername", "security", "instrument", "bezeichnung"],
    "ticker": ["ticker", "symbol", "isin"],
    "quantity": ["quantity", "stückzahl", "stueckzahl", "anzahl", "shares", "qty"],
    "value": ["value", "wert", "aktueller wert", "market value", "marktwert", "betrag"],
    "currency": ["currency", "währung", "waehrung", "ccy"],
}

def read_uploaded_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    uploaded_file.seek(0)
    return _reader_for_suffix(suffix)(uploaded_file)

def read_file_path(path: Path):
    return _reader_for_suffix(path.suffix.lower())(path)

def _reader_for_suffix(suffix):
    if suffix == ".csv":
        return _read_csv
    if suffix == ".pdf":
        return _read_pdf
    raise ValueError("Unsupported file type. Choose a CSV or PDF file.")


def _csv_headers(source, separator):
    if hasattr(source, "read"):
        source.seek(0)
        if isinstance(source.read(0), bytes):
            wrapper = io.TextIOWrapper(source, encoding="utf-8-sig", newline="")
            try:
                return next(csv.reader(wrapper, delimiter=separator), [])
            finally:
                wrapper.detach()
                source.seek(0)
        try:
            return next(csv.reader(source, delimiter=separator), [])
        finally:
            source.seek(0)
    with open(source, encoding="utf-8-sig", newline="") as stream:
        return next(csv.reader(stream, delimiter=separator), [])


def _read_csv(source):
    errors = []
    for sep in [",", ";", "\t"]:
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            df = pd.read_csv(source, sep=sep)
        except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError):
            continue
        if len(df.columns) <= 1:
            continue
        headers = {str(column).strip().lower() for column in df.columns}
        matches = sum(bool(headers.intersection(ALIASES[name])) for name in ("name", "quantity", "value"))
        try:
            original_headers = [name.strip().lower() for name in _csv_headers(source, sep)]
            if len(original_headers) != len(set(original_headers)):
                raise ValueError("Duplicate column names are not supported.")
            return normalize(df)
        except ValueError as exc:
            if matches == 3:
                raise
            errors.append((matches, exc))
    if errors:
        raise max(errors, key=lambda item: item[0])[1]
    raise ValueError("CSV could not be parsed.")

def _read_pdf(source):
    if pdfplumber is None:
        raise ValueError("pdfplumber is not installed.")
    rows = []
    if hasattr(source, "seek"):
        source.seek(0)
    try:
        with pdfplumber.open(source) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if table and len(table) > 1:
                        header = table[0]
                        for row in table[1:]:
                            if len(row) == len(header):
                                rows.append(dict(zip(header, row)))
    except pdfplumber.utils.exceptions.PdfminerException as exc:
        raise ValueError("PDF could not be parsed. Check that it is a readable, unencrypted PDF.") from exc
    if not rows:
        raise ValueError("No table-like positions found in PDF.")
    return normalize(pd.DataFrame(rows))

def normalize(df):
    df = df.copy()
    headers = [str(column).strip().lower() for column in df.columns]
    if len(headers) != len(set(headers)):
        raise ValueError("Duplicate column names are not supported.")
    lookup = dict(zip(headers, df.columns))
    mapping = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if alias in lookup:
                mapping[lookup[alias]] = target
                break
    df = df.rename(columns=mapping)

    missing = [c for c in ["name", "quantity", "value"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

    for optional in ["ticker", "currency"]:
        if optional not in df.columns:
            df[optional] = ""

    df["quantity"] = df["quantity"].apply(parse_number)
    df["value"] = df["value"].apply(parse_number)
    df["name"] = df["name"].fillna("").astype(str).str.strip()
    df["ticker"] = df["ticker"].fillna("").astype(str).str.strip()
    df["currency"] = df["currency"].fillna("").astype(str).str.strip().str.upper()
    df = df.dropna(subset=["quantity", "value"])
    df = df.loc[df["name"].ne(""), ["name", "ticker", "quantity", "value", "currency"]]
    if df.empty:
        raise ValueError("No valid positions found in the file.")
    return df

def parse_number(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"(?i)\b(?:CHF|EUR|USD)\b", "", text)
    text = re.sub(r"[\s'’]", "", text)
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            valid_grouping = r"[+-]?[0-9]{1,3}(?:\.[0-9]{3})+,[0-9]+(?:[eE][+-]?[0-9]+)?"
            if not re.fullmatch(valid_grouping, text):
                raise ValueError(f"Invalid numeric grouping: {value!r}")
            text = text.replace(".", "").replace(",", ".")
        else:
            valid_grouping = r"[+-]?[0-9]{1,3}(?:,[0-9]{3})+\.[0-9]+(?:[eE][+-]?[0-9]+)?"
            if not re.fullmatch(valid_grouping, text):
                raise ValueError(f"Invalid numeric grouping: {value!r}")
            text = text.replace(",", "")
    elif text.count(",") > 1 or text.count(".") > 1:
        separator = "," if "," in text else "."
        if not re.fullmatch(r"[+-]?[0-9]{1,3}(?:" + re.escape(separator) + r"[0-9]{3}){2,}", text):
            raise ValueError(f"Invalid numeric grouping: {value!r}")
        text = text.replace(separator, "")
    elif "," in text:
        text = text.replace(",", ".")
    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", text):
        raise ValueError(f"Invalid numeric value: {value!r}")
    number = float(text)
    if not math.isfinite(number):
        raise ValueError("Numeric values must be finite.")
    return number
