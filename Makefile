.PHONY: up demo report clean publish-check

up:
	@echo "==> Booting LLM Guard + garak worker"
	docker compose up -d --build

demo:
	@echo "==> Running secured agent loop (sandbox only)"
	python3 scripts/run_demo.py

report:
	@echo "==> Rendering findings report"
	python3 scripts/render_report.py reports/findings.md

clean:
	@echo "==> Tearing down lab"
	docker compose down -v

publish-check:
	@echo "==> Scanning for secrets before anything leaves the sandbox"
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner --log-opts=--all; \
	elif command -v trufflehog >/dev/null 2>&1; then trufflehog filesystem $$(pwd) --only-verified=false; \
	else echo "!! install gitleaks or trufflehog (see SECURITY.md checklist)"; exit 1; fi