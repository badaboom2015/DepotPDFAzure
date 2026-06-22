import sys
from pathlib import Path
from portfolio.importer import read_file_path
from portfolio.analyzer import analyze_portfolio
from portfolio.commentary import generate_commentary

if len(sys.argv) != 2:
    print("Usage: python cli.py <file.csv|file.pdf>")
    sys.exit(1)

positions = read_file_path(Path(sys.argv[1]))
result = analyze_portfolio(positions)

print("\n=== POSITIONS ===")
print(result.positions.to_string(index=False))
print("\n=== SUMMARY ===")
print(f"Total value: {result.total_value:,.2f}")
print(f"Largest position: {result.max_weight:.1f}%")
print("\n=== TOP 5 ===")
print(result.top5.to_string(index=False))
print("\n=== RISKS ===")
for risk in result.risks or ["No obvious concentration risks detected."]:
    print(f"- {risk}")
print("\n=== COMMENT ===")
print(generate_commentary(result))
