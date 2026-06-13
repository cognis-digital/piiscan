<a name="top"></a>
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=rect&color=0:6b46c1,100:2b6cb0&height=120&section=header&text=PIISCAN&fontSize=48&fontColor=ffffff&fontAlignY=58" width="100%" alt="PIISCAN"/>

# PIISCAN

### PII discovery across warehouses and lakes (data-side scanner)

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=3500&pause=1000&color=6B46C1&center=true&vCenter=true&width=720&lines=PII+discovery+across+warehouses+and+lakes+dataside+scanner;Self-hostable+%C2%B7+MCP-native+%C2%B7+CI-ready+%C2%B7+polyglot" width="720"/>

[![PyPI](https://img.shields.io/pypi/v/cognis-piiscan.svg?color=6b46c1)](https://pypi.org/project/cognis-piiscan/) [![CI](https://github.com/cognis-digital/piiscan/actions/workflows/ci.yml/badge.svg)](https://github.com/cognis-digital/piiscan/actions) [![License: COCL 1.0](https://img.shields.io/badge/License-COCL%201.0-2b6cb0.svg)](LICENSE) [![Suite](https://img.shields.io/badge/Cognis-Neural%20Suite-6b46c1.svg)](https://github.com/cognis-digital)

*Data & Datasets — zero-setup quality, lineage, and governance.*

</div>

```bash
pip install cognis-piiscan
piiscan scan .            # → prioritized findings in seconds
```

## Usage — step by step

1. Install the CLI (Python 3.9+):

   ```bash
   pip install git+https://github.com/cognis-digital/piiscan.git
   ```

2. Scan a CSV extract (e.g. a warehouse export) for PII:

   ```bash
   piiscan scan customers.csv
   ```

3. Tune sampling and confidence, and emit JSON for cataloging:

   ```bash
   piiscan scan customers.csv --sample 5000 --format json > pii.json
   ```

4. Hide low-confidence columns in the table view:

   ```bash
   piiscan scan customers.csv --min-confidence 0.7
   ```

5. Profile exports for PII in a pipeline:

   ```yaml
   - name: pii discovery
     run: |
       pip install git+https://github.com/cognis-digital/piiscan.git
       piiscan scan export.csv --format json
   ```

## Contents

- [Why piiscan?](#why) · [Features](#features) · [Quick start](#quick-start) · [Example](#example) · [Architecture](#architecture) · [AI stack](#ai-stack) · [How it compares](#how-it-compares) · [Integrations](#integrations) · [Install anywhere](#install-anywhere) · [Related](#related) · [Contributing](#contributing)

<a name="why"></a>
## Why piiscan?

data governance

`piiscan` is single-purpose, scriptable, and self-hostable: point it at a target, get prioritized results in the format your workflow already speaks (table · JSON · SARIF), gate CI on it, and let agents drive it over MCP.

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="features"></a>
## Features

- ✅ Luhn Valid
- ✅ Ssn Valid
- ✅ Ipv4 Valid
- ✅ Classify Risk
- ✅ Scan Column
- ✅ Scan Dataset
- ✅ Load Csv
- ✅ Runs on Linux/macOS/Windows · Docker · devcontainer
- ✅ Ports in Python, JavaScript, Go, and Rust (`ports/`)

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="quick-start"></a>
## Quick start

```bash
pip install cognis-piiscan
piiscan --version
piiscan scan .                       # scan current project
piiscan scan . --format json         # machine-readable
piiscan scan . --fail-on high        # CI gate (non-zero exit)
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="example"></a>
## Example

```text
$ piiscan scan .
  [HIGH    ] PII-001  example finding             (./src/app.py)
  [MEDIUM  ] PII-002  another signal              (./config.yaml)

  2 findings · risk score 5 · 38ms
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="architecture"></a>
## Architecture

```mermaid
flowchart LR
  IN[target / manifest] --> P[piiscan<br/>checks + rules]
  P --> OUT[findings (JSON / SARIF)]
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="ai-stack"></a>
## Use it from any AI stack

`piiscan` is interoperable with every popular way of using AI:

- **MCP server** — `piiscan mcp` (Claude Desktop, Cursor, Cognis.Studio, [uncensored-fleet](https://github.com/cognis-digital/uncensored-fleet))
- **OpenAI-compatible / JSON** — pipe `piiscan scan . --format json` into any agent or LLM
- **LangChain · CrewAI · AutoGen · LlamaIndex** — wrap the CLI/JSON as a tool in one line
- **CI / scripts** — exit codes + SARIF for non-AI pipelines

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="how-it-compares"></a>
## How it compares

| | **Cognis piiscan** | Presidio |
|---|:---:|:---:|
| Self-hostable, no account | ✅ | varies |
| Single command, zero config | ✅ | ⚠️ |
| JSON + SARIF for CI | ✅ | varies |
| MCP-native (AI agents) | ✅ | ❌ |
| Polyglot ports (JS/Go/Rust) | ✅ | ❌ |
| Open license | ✅ COCL | varies |

*Built in the spirit of **Presidio**, re-framed the Cognis way. Missing a credit? Open a PR.*

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="integrations"></a>
## Integrations

Pipes into your stack: **SARIF** for code-scanning, **JSON** for anything, an **MCP server** (`piiscan mcp`) for AI agents, and a webhook forwarder for SIEM/Slack/Jira. See [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md).

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="install-anywhere"></a>
## Install — every way, every platform

```bash
pip install "git+https://github.com/cognis-digital/piiscan.git"    # pip (works today)
pipx install "git+https://github.com/cognis-digital/piiscan.git"   # isolated CLI
uv tool install "git+https://github.com/cognis-digital/piiscan.git" # uv
pip install cognis-piiscan                                          # PyPI (when published)
docker run --rm ghcr.io/cognis-digital/piiscan:latest --help        # Docker
brew install cognis-digital/tap/piiscan                             # Homebrew tap
curl -fsSL https://raw.githubusercontent.com/cognis-digital/piiscan/main/install.sh | sh
```

| Linux | macOS | Windows | Docker | Cloud |
|---|---|---|---|---|
| `scripts/setup-linux.sh` | `scripts/setup-macos.sh` | `scripts/setup-windows.ps1` | `docker run ghcr.io/cognis-digital/piiscan` | [DEPLOY.md](docs/DEPLOY.md) (AWS/Azure/GCP/k8s) |

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="related"></a>
## Related Cognis tools

- [`duckprobe`](https://github.com/cognis-digital/duckprobe) — Zero-setup data-quality checks on any file or warehouse via DuckDB
- [`schemadrift`](https://github.com/cognis-digital/schemadrift) — Schema-change detector and data-contract tests
- [`csvlens`](https://github.com/cognis-digital/csvlens) — Fast CLI for profiling and cleaning huge CSV / Parquet files
- [`lineagemap`](https://github.com/cognis-digital/lineagemap) — Column-level lineage extracted from SQL and dbt
- [`datasetcard`](https://github.com/cognis-digital/datasetcard) — Auto Dataset Cards / datasheets with Croissant + provenance
- [`seedforge`](https://github.com/cognis-digital/seedforge) — Synthetic test-data generator with referential integrity

**Explore the suite →** [🗂️ all 170+ tools](https://github.com/cognis-digital/cognis-neural-suite) · [⭐ awesome-cognis](https://github.com/cognis-digital/awesome-cognis) · [🔗 cognis-sources](https://github.com/cognis-digital/cognis-sources) · [🤖 uncensored-fleet](https://github.com/cognis-digital/uncensored-fleet) · [🧠 engram](https://github.com/cognis-digital/engram)

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="contributing"></a>
## Contributing

PRs, new rules, and demo scenarios are welcome under the collaboration-pull model — see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

> ### ⭐ If `piiscan` saved you time, **star it** — it genuinely helps others find it.

## Interoperability

`{}` composes with the 300+ tool Cognis suite — JSON in/out and a shared
OpenAI-compatible `/v1` backbone. See **[INTEROP.md](INTEROP.md)** for the
suite map, composition patterns, and reference stacks.

## License

Source-available under the **Cognis Open Collaboration License (COCL) v1.0** — free for personal, internal-evaluation, research, and educational use; **commercial / production use requires a license** (licensing@cognis.digital). See [LICENSE](LICENSE).

---

<div align="center"><sub><b><a href="https://cognis.digital">Cognis Digital</a></b> · one of 170+ tools in the <a href="https://github.com/cognis-digital/cognis-neural-suite">Cognis Neural Suite</a> · <i>Making Tomorrow Better Today</i></sub></div>
