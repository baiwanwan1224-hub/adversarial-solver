"""Custom department example — define your own department and rules.

This shows how to create a custom department with custom banned words.
"""

# Step 1: Create a custom config directory
#   adversarial-solver init -p my_config
#
# Step 2: Edit my_config/departments.yaml to add your department:
#   departments:
#     content_team:
#       name: "Content Team"
#       scope: "Blog posts, email newsletters, social media"
#       primary_model: "openai/gpt-4.1"
#       reviewer_model: "anthropic/claude-sonnet-4-6"
#       tone_checker: true
#       reviewer_role: "Review style guide compliance, factual accuracy, banned words"
#
# Step 3: Edit my_config/rules.yaml to add your banned words
# Step 4: Copy my_config/.env.example to my_config/.env with your API keys

from adversarial_solver import adversarial_solve

result = adversarial_solve(
    task="Write a blog post introduction about remote work productivity.",
    dept="content_team",
    max_rounds=3,
    config_path="my_config",
)

print("\n" + "=" * 60)
print("FINAL OUTPUT")
print("=" * 60)
print(result["final"])
print(f"\nStatus: {result['status']}")
