.PHONY: setup up demo report clean publish-check trace-export charts

setup:
	@echo "==> Creating venv + installing pinned deps (garak, llm-guard, checkov)"
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

up:
	@echo "==> OPTIONAL: booting LLM Guard as a hosted service (docker-compose.yml)."
	@echo "    Not required for 'make demo' — that runs llm-guard in-process. See README."
	docker compose up -d --build

demo:
	@echo "==> Running secured agent loop (sandbox only)"
	.venv/bin/python scripts/run_demo.py $(ARGS)

report:
	@echo "==> Rendering findings report"
	.venv/bin/python scripts/render_report.py
	@echo "==> Rendering hardening re-run"
	.venv/bin/python scripts/render_hardening.py

trace-export:
	@echo "==> Exporting run trace to Langfuse (skips if no creds)"
	.venv/bin/python scripts/export_trace.py

charts:
	@echo "==> Rendering LinkedIn-friendly chart PNGs"
	python3 scripts/render_charts.py

clean:
	@echo "==> Tearing down the optional docker-compose service (if you ran 'make up')"
	docker compose down -v

publish-check:
	@echo "==> Scanning for secrets before anything leaves the sandbox"
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner --log-opts=--all; \
	elif command -v trufflehog >/dev/null 2>&1; then trufflehog filesystem $$(pwd) --only-verified=false; \
	else echo "!! install gitleaks or trufflehog (see SECURITY.md checklist)"; exit 1; fi