"""`python -m bots` runs the complete 5-bot intelligent engineering verification suite."""

from bots.bot_runner import run_all_bots

if __name__ == "__main__":
    reports = run_all_bots()
    for item in reports:
        print(item.to_text())
        print("\n" + "=" * 70 + "\n")
    raise SystemExit(0 if all(item.all_passed for item in reports) else 1)
