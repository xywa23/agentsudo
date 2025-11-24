# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-11-24

### Added
- Complete documentation suite:
  - API Reference (`docs/api.md`)
  - Contributing guidelines (`CONTRIBUTING.md`)
  - Example scripts (`examples/`)
  - Pull request template
- Examples:
  - `basic_usage.py` - Core concepts
  - `wildcard_scopes.py` - Pattern matching
  - `audit_mode.py` - Non-blocking mode
  - `approval_workflow.py` - Human-in-the-loop
  - `pydantic_integration.py` - Model permissions

### Changed
- Updated README with comprehensive feature documentation
- Improved PyPI package description

## [0.1.0] - 2025-11-24

### Added
- Initial release
- Core `Agent` class with identity management
- `@sudo` decorator for function-level permissions
- Wildcard scope matching (e.g., `read:*`)
- Session expiry (TTL-based)
- Audit mode (`on_deny="log"`)
- Approval callbacks for human-in-the-loop workflows
- Pydantic `ScopedModel` integration
- Structured JSON logging for SIEM integration
- Comprehensive test suite with pytest
- MIT License

### Features
- Thread-safe agent context using `contextvars`
- Fine-grained permission scopes
- Detailed error messages with remediation hints
- Professional logging (no emojis in library code)
- Type hints throughout

[0.1.1]: https://github.com/xywa23/agentsudo/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/xywa23/agentsudo/releases/tag/v0.1.0
