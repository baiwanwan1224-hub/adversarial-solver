# Contributing to Adversarial Solver / 贡献指南

Thanks for your interest! / 感谢你的关注！

## Ways to Contribute / 参与方式

- **Report bugs / 报告 Bug** — Open an Issue with reproduction steps / 提 Issue 附复现步骤
- **Suggest features / 建议功能** — Open an Issue with the `enhancement` label / 提 Issue 加 enhancement 标签
- **Submit PRs / 提交代码** — Bug fixes, docs, new features (discuss first for large changes) / Bug 修复、文档、新功能（大改动先讨论）
- **Share feedback / 分享反馈** — Real-world usage stories are valuable / 真实使用场景非常有价值

## Development Setup / 开发环境

```bash
git clone https://github.com/baiwanwan1224-hub/adversarial-solver.git
cd adversarial-solver
pip install -e ".[dev]"    # Install with dev dependencies / 安装开发依赖
```

## Code Style / 代码风格

- Follow PEP 8 / 遵循 PEP 8
- Type hints on public functions / 公开函数加类型注解
- Docstrings on public functions (Google style) / 公开函数加 Docstring（Google 风格）
- Keep modules under 300 lines / 每个模块不超过 300 行

## Testing / 测试

```bash
# Run all tests / 跑全部测试
pytest tests/ -v

# With coverage / 含覆盖率
pytest tests/ --cov=adversarial_solver --cov-report=html
```

## Pull Request Process / 提交流程

1. Fork the repo / Fork 仓库
2. Create a feature branch / 创建功能分支 (`git checkout -b feature/your-feature`)
3. Write tests for your changes / 为改动写测试
4. Ensure all tests pass / 确保全部测试通过
5. Open a PR with a clear description / 提 PR 附清晰描述

## Commit Messages / 提交信息

Follow [Conventional Commits](https://www.conventionalcommits.org/) / 遵循 Conventional Commits 规范：

- `feat:` — new feature / 新功能
- `fix:` — bug fix / 修复
- `docs:` — documentation / 文档
- `test:` — tests / 测试
- `refactor:` — code restructuring / 重构
- `chore:` — maintenance / 维护

## License / 许可证

By contributing, you agree your contributions will be licensed under the MIT License.
提交贡献即表示你同意将其以 MIT 许可证授权。
