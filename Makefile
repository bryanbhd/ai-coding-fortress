.PHONY: up demo report clean publish-check trace-export

up:
	@echo "==> Booting LLM Guard + garak worker"
	docker compose up -d --build

demo:
	@echo "==> Running secured agent loop (sandbox only)"
	.venv/bin/python scripts/run_demo.py

report:
	@echo "==> Rendering findings report"
	.venv/bin/python scripts/render_report.py
	@echo "==> Rendering hardening re-run"
	.venv/bin/python scripts/render_hardening.py

trace-export:
	@echo "==> Exporting run trace to Langfuse (skips if no creds)"
	.venv/bin/python scripts/export_trace.py

clean:
	@echo "==> Tearing down lab"
	docker compose down -v

publish-check:
	@echo "==> Scanning for secrets before anything leaves the sandbox"
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner --log-opts=--all; \
	elif command -v trufflehog >/dev/null 2>&1; then trufflehog filesystem $$(pwd) --only-verified=false; \
	else echo "!! install gitleaks or trufflehog (see SECURITY.md checklist)"; exit 1; fi