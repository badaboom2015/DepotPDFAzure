from .models import AnalysisResult
import pandas as pd

TECH = ["apple", "microsoft", "amazon", "alphabet", "google", "meta", "nvidia", "tesla", "nasdaq", "tech", "technology"]
USA = ["usa", "us ", "s&p", "sp500", "nasdaq", "apple", "microsoft", "amazon", "alphabet", "google", "meta", "nvidia", "tesla"]

def analyze_portfolio(df):
    positions = df.copy()
    total = float(positions["value"].sum())
    if total <= 0:
        raise ValueError("Total value must be positive.")

    positions["weight_pct"] = positions["value"] / total * 100
    positions["asset_type"] = positions.apply(classify_asset_type, axis=1)
    positions["is_tech_related"] = positions.apply(lambda r: has_keywords(r, TECH), axis=1)
    positions["is_usa_related"] = positions.apply(lambda r: has_keywords(r, USA), axis=1)
    positions = positions.sort_values("value", ascending=False).reset_index(drop=True)

    risks = detect_risks(positions)
    top5 = positions.head(5)
    cols = ["name", "ticker", "quantity", "value", "weight_pct", "asset_type", "is_tech_related", "is_usa_related"]

    return AnalysisResult(
        positions=positions[cols],
        top5=top5[cols],
        total_value=total,
        max_weight=float(positions["weight_pct"].max()),
        risks=risks,
        warnings=[],
    )

def classify_asset_type(row):
    text = f"{row.get('name', '')} {row.get('ticker', '')}".lower()
    if "cash" in text or "konto" in text or "liquidität" in text:
        return "Cash"
    if "option" in text or "call" in text or "put" in text:
        return "Option"
    if "etf" in text or "ucits" in text or "ishares" in text or "vanguard" in text:
        return "ETF"
    return "Aktie"

def has_keywords(row, keywords):
    text = f"{row.get('name', '')} {row.get('ticker', '')}".lower()
    return any(k in text for k in keywords)

def detect_risks(positions):
    risks = []
    largest = positions.iloc[0]
    if largest["weight_pct"] >= 25:
        risks.append(f"Single-name concentration: {largest['name']} is {largest['weight_pct']:.1f}% of the portfolio.")
    elif largest["weight_pct"] >= 15:
        risks.append(f"Large single position: {largest['name']} is {largest['weight_pct']:.1f}% of the portfolio.")

    top5 = float(positions.head(5)["weight_pct"].sum())
    if top5 >= 70:
        risks.append(f"Top-5 concentration: largest five positions represent {top5:.1f}%.")

    tech = float(positions[positions["is_tech_related"]]["weight_pct"].sum())
    if tech >= 40:
        risks.append(f"Tech concentration: recognizable tech positions represent {tech:.1f}%.")

    usa = float(positions[positions["is_usa_related"]]["weight_pct"].sum())
    if usa >= 50:
        risks.append(f"USA concentration: recognizable US-related positions represent {usa:.1f}%.")

    return risks
