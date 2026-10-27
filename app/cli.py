import sys
from pathlib import Path
from portfolio.importer import read_file_path
from portfolio.analyzer import analyze_portfolio
from portfolio.commentary import generate_commentary


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python cli.py <file.csv|file.pdf>", file=sys.stderr)
        return 1
    try:
        positions = read_file_path(Path(args[0]))
        result = analyze_portfolio(positions)
        comment = generate_commentary(result)
    except (OSError, ValueError) as exc:
        print(f"Processing failed: {exc}", file=sys.stderr)
        return 1

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
    print(comment)
    return 0


if __name__ == "__main__":
    sys.exit(main())
