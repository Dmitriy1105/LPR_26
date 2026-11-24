# LPR_26 UI/UX Automated Testing v1.0
14 Chromium tests covering 11 acceptance categories. Static public site served locally; no production CRM access. Keyboard edge selection tests keyboard functionality, not pointer hit testing. Label bounding boxes are a proxy, screenshots need visual review. Responsive tests check horizontal overflow and visibility, not complete usability. Run from repository root: npm install --prefix tests/ui --no-audit --no-fund; npx --prefix tests/ui playwright install chromium; npx --prefix tests/ui playwright test --config tests/ui/playwright.config.mjs. Results in Actions artifacts. Initial status: not yet executed.

## Run 1 — 45387777100
- CI-001 (blocking infrastructure): ubuntu-latest resolved to Ubuntu 26.04; Playwright 1.51.1 rejected Chromium dependency installation. All 14 tests skipped, no UI verdict.
- Fix e533612: pin ubuntu-24.04. Verification pending fresh run.
