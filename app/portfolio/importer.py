from pathlib import Path
import re
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
    return _read_csv(uploaded_file) if suffix == ".csv" else _read_pdf(uploaded_file)

def read_file_path(path: Path):
    return _read_csv(path) if path.suffix.lower() == ".csv" else _read_pdf(path)

def _read_csv(source):
    for sep in [",", ";", "\\t"]:
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            df = pd.read_csv(source, sep=sep)
            if len(df.columns) > 1:
                return normalize(df)
        except Exception:
            pass
    raise ValueError("CSV could not be parsed.")

def _read_pdf(source):
    if pdfplumber is None:
        raise ValueError("pdfplumber is not installed.")
    rows = []
    if hasattr(source, "seek"):
        source.seek(0)
    with pdfplumber.open(source) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if table and len(table) > 1:
                    header = table[0]
                    for row in table[1:]:
                        if len(row) == len(header):
                            rows.append(dict(zip(header, row)))
    if not rows:
        raise ValueError("No table-like positions found in PDF.")
    return normalize(pd.DataFrame(rows))

def normalize(df):
    df = df.copy()
    lookup = {str(c).strip().lower(): c for c in df.columns}
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
    df["name"] = df["name"].astype(str).str.strip()
    df["ticker"] = df["ticker"].astype(str).str.strip()
    df["currency"] = df["currency"].astype(str).str.strip()

    return df.dropna(subset=["name", "quantity", "value"])[["name", "ticker", "quantity", "value", "currency"]]

def parse_number(value):
    if pd.isna(value):
        return None
    text = str(value).replace("CHF", "").replace("EUR", "").replace("USD", "")
    text = text.replace("'", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    text = re.sub(r"[^0-9.\\-]", "", text)
    return float(text) if text else None
