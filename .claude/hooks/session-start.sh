#!/bin/bash
# Cloud sessions start from a fresh container without the test tools, so
# ./tools/check.sh cannot run. Install the dev extras from pyproject.toml
# (pytest, pytest-xdist, pyyaml). The tooling itself stays stdlib-only.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Ask pip's metadata, not `import`: a leftover empty package folder imports fine.
if python3 -c "import importlib.metadata as m; [m.version(p) for p in ('pytest', 'pytest-xdist', 'PyYAML')]" 2>/dev/null; then
  exit 0
fi
python3 -m pip install --quiet --disable-pip-version-check \
  "pytest>=8" "pytest-xdist>=3" "pyyaml>=6"
