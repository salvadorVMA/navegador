# Security Tools and Scanning Procedures

This document describes the security tools configured for the Navegador project, what each tool does, how it runs, and how often.

---

## Editor-Level Tools (Real-Time)

### SonarLint

- **What it does**: Analyzes code as you type in VS Code, flagging security vulnerabilities, bugs, and code smells. Covers OWASP Top 10 categories including injection, broken authentication, and sensitive data exposure.
- **Languages**: Python, JavaScript, HTML, JSON, and others.
- **How it runs**: Automatically in the editor on every file save and as you type. No manual step needed.
- **Frequency**: Continuous (real-time).
- **Configuration**: Installed via `devcontainer.json` as the extension `SonarSource.sonarlint-vscode`.

### Pylint

- **What it does**: Python linter that catches errors, enforces coding standards, and includes checks for common security anti-patterns (e.g., use of `exec`, `eval`, dangerous imports).
- **How it runs**: Automatically in VS Code when editing Python files.
- **Frequency**: Continuous (real-time).
- **Configuration**: Installed via `devcontainer.json` as the extension `ms-python.pylint`.

---

## CLI Tools (On-Demand / Local)

### Bandit

- **What it does**: Static Application Security Testing (SAST) tool specifically designed for Python. Scans code for common security issues including:
  - Use of weak cryptographic hashes (MD5, SHA1)
  - Insecure deserialization (pickle)
  - Hardcoded passwords and bind addresses
  - SQL injection vectors
  - Use of dangerous functions (`exec`, `eval`, `assert`)
  - Insecure file permissions
- **How to run locally**:
  ```bash
  # Scan the full project (excluding test/archive dirs)
  bandit -r . -x ./tests,./archive,./notebooks,./.devcontainer,./node_modules --severity-level medium

  # Scan a specific file
  bandit path/to/file.py

  # Output as JSON for tooling
  bandit -r . -f json -o bandit-report.json
  ```
- **Frequency**: Run manually before committing significant changes. Also runs automatically in CI on every push and PR.
- **Configuration**: Installed in `postCreateCommand` in `devcontainer.json`. CI workflow in `.github/workflows/security.yml`.

### Safety

- **What it does**: Checks Python dependencies (from `requirements.txt`) against the Safety vulnerability database. Detects known CVEs in installed packages.
- **How to run locally**:
  ```bash
  # Check project dependencies
  safety check -r config/requirements.txt

  # Scan with JSON output
  safety check -r config/requirements.txt --output json
  ```
- **Frequency**: Run manually when adding or updating dependencies. Also runs automatically in CI on every push and PR, and weekly on Monday at 6am UTC.
- **Configuration**: Installed in `postCreateCommand` in `devcontainer.json`. CI workflow in `.github/workflows/security.yml`.

### Semgrep

- **What it does**: Multi-language static analysis engine that uses pattern-matching rules to detect security issues, bugs, and anti-patterns. Supports custom rules and has an extensive community rule registry covering:
  - Injection vulnerabilities (SQL, command, XSS)
  - Authentication and authorization flaws
  - Cryptographic misuse
  - Hardcoded secrets
  - Framework-specific issues (Flask, Django, etc.)
- **How to run locally**:
  ```bash
  # Run with default Python security rules
  semgrep --config auto .

  # Run specific security ruleset
  semgrep --config p/python .

  # Run OWASP Top 10 rules
  semgrep --config p/owasp-top-ten .
  ```
- **Frequency**: Run manually for deep analysis before releases or major changes.
- **Configuration**: Installed in `postCreateCommand` in `devcontainer.json`.

### Gitleaks

- **What it does**: Scans files and git history for hardcoded secrets such as API keys, tokens, passwords, and private keys. Uses regex patterns and entropy analysis to detect secrets that should not be in source code.
- **How to run locally**:
  ```bash
  # Scan current files (no git history)
  gitleaks detect --source . --no-git -c .gitleaks.toml

  # Scan full git history
  gitleaks detect --source . -c .gitleaks.toml

  # Verbose output showing each finding
  gitleaks detect --source . --no-git -c .gitleaks.toml -v
  ```
- **Frequency**: Run manually before committing. Also runs automatically in CI on every push and PR.
- **Allowlist**: Configured in `.gitleaks.toml` to skip `.env` files (local-only, gitignored), `.env.example` (contains placeholders only), and `config/environment*.yml` (conda package hashes trigger false positives).
- **Configuration**: Binary installed in `postCreateCommand` in `devcontainer.json`. Allowlist in `.gitleaks.toml`. CI workflow in `.github/workflows/security.yml`.

---

## CI/CD Tools (Automated)

### GitHub Actions Security Workflow

- **File**: `.github/workflows/security.yml`
- **What it does**: Runs four security jobs in parallel on every push and PR:
  1. **Bandit** - Python SAST scan, uploads report as artifact
  2. **Gitleaks** - Secret detection across full git history
  3. **Safety** - Dependency vulnerability check, uploads report as artifact
  4. **Codacy** - Comprehensive code quality and security analysis (requires setup, see below)
- **Triggers**:
  - Every push to `main`, `master`, or `Claude1` branches
  - Every pull request targeting those branches
  - Weekly scheduled run on Monday at 6am UTC
- **Artifacts**: Bandit and Safety reports are uploaded as GitHub Actions artifacts and retained for the default period.

### Codacy

- **What it does**: Cloud-based code quality and security platform. Analyzes code on every PR and commit, providing:
  - Security issue detection (using Bandit, Pylint, and its own rules)
  - Code quality grading
  - Complexity analysis
  - Duplication detection
  - Coverage tracking
  - PR-level review comments
- **How it runs**: Two modes:
  1. **GitHub App** (recommended): Install from [GitHub Marketplace](https://github.com/marketplace/codacy). Free for open-source projects. Scans automatically on every PR.
  2. **CI Action**: Runs in `.github/workflows/security.yml` using the `codacy/codacy-analysis-cli-action`.
- **Setup required**:
  1. Install the Codacy GitHub App on the repository
  2. Get the project token from the Codacy dashboard
  3. Add it as a repository secret named `CODACY_PROJECT_TOKEN`
- **Frequency**: Every push and PR (via CI), plus continuous via GitHub App.
- **Configuration**: `.codacy.yml` in the project root defines which engines to enable and which paths to exclude.

---

## GitHub Platform Security (Always-On)

### Dependabot

- **What it does**: Monitors project dependencies for known vulnerabilities and outdated packages. Automatically opens pull requests to update vulnerable or outdated dependencies.
- **Ecosystems monitored**:
  - **pip** (Python packages in `config/`): Weekly scans
  - **npm** (Node.js packages in `/`): Weekly scans
  - **GitHub Actions** (workflow dependencies in `/`): Weekly scans
- **How it runs**: Fully automated by GitHub. PRs are labeled with `dependencies` and `security` (or `ci` for Actions updates).
- **Frequency**: Weekly for each ecosystem.
- **Configuration**: `.github/dependabot.yml`.
- **PR limit**: 5 open PRs per ecosystem to avoid PR overload.

### GitHub Secret Scanning

- **What it does**: Scans the repository (including git history) for known secret patterns from 200+ service providers (AWS, Google, Azure, Stripe, etc.). Alerts repository admins when secrets are detected.
- **How it runs**: Automatically by GitHub. No configuration needed.
- **Frequency**: Continuous. Scans every push and periodically re-scans the full repository.
- **Activation**: Automatically enabled for public repositories. For private repositories, requires GitHub Advanced Security license.
- **Note**: When the Navegador repo goes public, this will activate immediately and may flag secrets that exist in git history.

### GitHub Code Scanning (CodeQL)

- **What it does**: GitHub's semantic code analysis engine. Performs deep analysis beyond pattern matching, understanding data flow to detect vulnerabilities like SQL injection, XSS, and insecure deserialization.
- **Activation**: Automatically available for public repositories. Can be enabled via repository Settings > Code security and analysis.
- **Frequency**: Runs on every push and PR once enabled.
- **Note**: Not yet configured as a workflow. Will activate automatically when the repo goes public and can be enabled in repository settings.

---

## Secret Management Policy

- **`.env` files** are listed in `.gitignore` and must never be committed to git
- **API keys** should be managed through:
  - GitHub Codespace secrets (for development)
  - Environment variables (for deployment)
  - `.env` files (local development only, never committed)
- **`.env.example`** contains placeholder values only and is safe to commit
- **Key rotation**: Any keys that were previously exposed in git history should be rotated immediately

---

## Quick Reference

| Tool | Layer | Frequency | Runs Automatically |
|------|-------|-----------|-------------------|
| SonarLint | Editor | Real-time | Yes (on file edit) |
| Pylint | Editor | Real-time | Yes (on file edit) |
| Bandit | CLI + CI | On-demand + every push/PR + weekly | Yes (CI) |
| Safety | CLI + CI | On-demand + every push/PR + weekly | Yes (CI) |
| Semgrep | CLI | On-demand | No |
| Gitleaks | CLI + CI | On-demand + every push/PR | Yes (CI) |
| Codacy | CI + GitHub App | Every push/PR | Yes (after setup) |
| Dependabot | GitHub | Weekly | Yes |
| Secret Scanning | GitHub | Continuous | Yes (public repos) |
| CodeQL | GitHub | Every push/PR | Yes (after enabling) |
