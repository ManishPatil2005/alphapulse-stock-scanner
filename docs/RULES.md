# Development Rules and Standards

## 1. Code Style
- **Python:** 
  - Formatter: Black.
  - Imports: isort.
  - Typing: Strict typing enforced using `mypy --strict`.
- **TypeScript:** 
  - Linter: ESLint with strict rules.
  - Formatter: Prettier.
  - Compiler: `strict: true` in tsconfig.json. No `any` types allowed.

## 2. Git Workflow
- **Strategy:** Trunk-based development.
- **Commits:** Conventional Commits (e.g., `feat:`, `fix:`, `chore:`, `refactor:`).
- **PRs:** Pull Request reviews are mandatory. CI checks must pass before merging.

## 3. Testing
- **Coverage:** Minimum 80% line coverage for both frontend and backend.
- **Integration:** All public APIs and WebSocket endpoints must have integration tests.
- **Frameworks:** `pytest` for Python, `Jest`/`Vitest` for TypeScript.

## 4. Security
- **Secrets:** NEVER commit secrets or credentials. Use Vault or `.env` files (excluded via `.gitignore`).
- **Validation:** Strict input validation on every endpoint using Pydantic (FastAPI) and Zod (TypeScript).
- **Auth:** JWT-based authentication with short-lived tokens and secure HttpOnly refresh cookies.

## 5. Documentation
- **Codebase:** All public functions, classes, and modules must have docstrings (Google style for Python, JSDoc for TS).
- **Decisions:** Architecture Decision Records (ADRs) must be written for any major technology or design choice.

## 6. Performance
- **APIs:** All REST endpoints must have a p99 response time of <200ms.
- **WebSockets:** Tick processing and WS message dispatching must occur in <10ms.
- **Database:** Proper indexing required; N+1 query problems will fail code review.

## 7. Output Philosophy (CRITICAL)
- The system must **NEVER** output "BUY", "SELL", or "HOLD" signals.
- All analytical outputs must be contextual: Market Context, Auction Context, Structure Context, or Teaching Notes.

## 8. Dependency Management
- **Pinning:** All dependencies must be strictly pinned (e.g., `requirements.txt` / `poetry.lock` or `package-lock.json`).
- **Audits:** Weekly automated vulnerability scans using Dependabot or Snyk.
- **Updates:** Dependencies should be updated monthly unless a critical CVE requires immediate patching.

## 9. Review Checklist Template
```markdown
### PR Review Checklist
- [ ] Code follows style guidelines (Black/isort/Prettier).
- [ ] Type hints are complete and strict.
- [ ] Tests added/updated (min 80% coverage maintained).
- [ ] No secrets or sensitive data committed.
- [ ] Input validation handled appropriately.
- [ ] Documentation/Docstrings updated.
- [ ] Performance implications considered (<200ms APIs).
- [ ] NO buy/sell/hold logic introduced.
```
