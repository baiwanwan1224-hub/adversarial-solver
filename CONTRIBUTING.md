# Contributing to Adversarial Solver

Thanks for your interest! This guide covers how to contribute.

## Ways to Contribute

- **Report bugs** — Open an Issue with reproduction steps
- **Suggest features** — Open an Issue with the `enhancement` label
- **Submit PRs** — Bug fixes, docs, new features (discuss first for large changes)
- **Share feedback** — Real-world usage stories are valuable

## Development Setup

```bash
git clone https://github.com/baiwanwan1224-hub/adversarial-solver.git
cd adversarial-solver
pip install -e ".[dev]"
```

## Code Style

- Follow PEP 8
- Type hints on public functions
- Docstrings on public functions (Google style)
- Keep modules under 300 lines

## Testing

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=adversarial_solver --cov-report=html
```

## Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests for your changes
4. Ensure all tests pass
5. Open a PR with a clear description

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `test:` — tests
- `refactor:` — code restructuring
- `chore:` — maintenance

## License

By contributing, you agree your contributions will be licensed under the MIT License.
