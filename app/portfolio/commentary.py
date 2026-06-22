def generate_commentary(result):
    top = result.top5.iloc[0]
    risks = " ".join(result.risks) if result.risks else "No clear concentration risk was detected."
    return (
        f"The portfolio has a total value of {result.total_value:,.2f}. "
        f"The largest position is {top['name']} with a weight of {top['weight_pct']:.1f}%. "
        f"{risks} "
        "This is an educational portfolio analysis only. It is not investment advice and not a buy or sell recommendation."
    )
