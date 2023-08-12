#!/bin/bash


log() {
  echo $(date "+%Y-%m-%d %H:%M:%S") "$@"
}

fail() {
  log $@
  exit 1
}

log "Running tests..."
pytest -o addopts="-s tests --cov-report term-missing --cov=server --cov-fail-under=35 --cov-branch" || fail "pytest failed."

log "Running linter..."
pylint server tests || fail "linting failed."

log "Running mypy..."
mypy . || fail "mypy failed."

log "Done."
