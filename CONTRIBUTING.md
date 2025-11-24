# Contributing to AgentSudo

Thank you for your interest in contributing to AgentSudo! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building security infrastructure for AI agents—professionalism matters.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/xywa23/agentsudo/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Minimal code example

### Suggesting Features

1. Check [existing feature requests](https://github.com/xywa23/agentsudo/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
2. Create a new issue with:
   - Use case description
   - Proposed API/interface
   - Why it's important

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests**
   ```bash
   pytest
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "Add wildcard support for hierarchical scopes"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/agentsudo.git
cd agentsudo

# Install in development mode
pip install -e ".[test]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentsudo

# Run specific test file
pytest tests/test_core.py
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small
- No emojis in library code (only in examples/demos)

### Example

```python
def has_scope(self, required_scope: str) -> bool:
    """
    Check if the agent has the required scope.
    
    Args:
        required_scope: The scope string to check (e.g., "read:users")
    
    Returns:
        True if agent has the scope, False otherwise
    """
    return required_scope in self.scopes
```

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Test both success and failure cases
- Use descriptive test names

### Example Test

```python
def test_wildcard_scope_matching():
    """Test that wildcard scopes match correctly."""
    agent = Agent(name="TestBot", scopes=["read:*"])
    
    assert agent.has_scope("read:users")
    assert agent.has_scope("read:orders")
    assert not agent.has_scope("write:users")
```

## Documentation

- Update `README.md` for user-facing changes
- Add examples to `examples/` for new features
- Update `docs/api.md` for API changes

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvements

**Example:**
```
feat: Add session expiry support

- Add session_ttl parameter to Agent class
- Check expiry in @sudo decorator
- Add tests for session timeout

Closes #42
```

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.2.0`
4. Build: `python -m build`
5. Upload: `python -m twine upload dist/*`

## Questions?

- Open a [Discussion](https://github.com/xywa23/agentsudo/discussions)
- Join our community (coming soon)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
