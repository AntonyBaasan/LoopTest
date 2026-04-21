from looptest.services.formatting import BOLD, DIM, GREEN, RED, WHITE, c


def print_summary(all_results):
    total = len(all_results)
    passed = sum(1 for item in all_results if item["status"] == "PASS")
    failed = total - passed

    print(c("─" * 60, DIM))
    print(f"  {c('SUMMARY', WHITE, BOLD)}")
    print(c("─" * 60, DIM))
    for result in all_results:
        icon = "✔" if result["status"] == "PASS" else "✘"
        color = GREEN if result["status"] == "PASS" else RED
        print(f"  {c(icon, color, BOLD)}  {result['name']}")
    print()
    print(f"  Total: {total}   Passed: {passed}   Failed: {failed}")
    print(c("─" * 60, DIM))
