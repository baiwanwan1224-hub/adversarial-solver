"""Basic usage example — run a simple adversarial solve."""

from adversarial_solver import adversarial_solve

# First, make sure you've set up your config:
#   adversarial-solver init
#   Edit config/departments.yaml and config/rules.yaml
#   Copy config/.env.example to config/.env and add your API keys

# Run a simple adversarial solve
result = adversarial_solve(
    task="Write a one-paragraph product description for a tea product.",
    dept="marketing",
    max_rounds=3,
)

print("\n" + "=" * 60)
print("FINAL OUTPUT")
print("=" * 60)
print(result["final"])
print(f"\nStatus: {result['status']}")
print(f"Rounds: {result['total_rounds']}")
