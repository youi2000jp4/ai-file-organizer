# 🗂️ ai-file-organizer

**Organize any folder with a single natural language command — in English or Japanese.**

[![CI](https://github.com/youi2000jp4/ai-file-organizer/actions/workflows/ci.yml/badge.svg)](https://github.com/youi2000jp4/ai-file-organizer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

```
$ file-org "ダウンロードフォルダを種類別に整理して" ~/Downloads --dry-run

  Organization Plan
  ┌─────────────────────┬──────────────────────┬──────────────────────┐
  │ Source              │ → Destination        │ Reason               │
  ├─────────────────────┼──────────────────────┼──────────────────────┤
  │ photo_2026.jpg      │ images/photo_2026... │ JPEG image file      │
  │ invoice_jan.pdf     │ documents/invoice... │ PDF document         │
  │ setup.exe           │ installers/setup.exe │ Windows installer    │
  │ vacation.mp4        │ videos/vacation.mp4  │ MP4 video file       │
  └─────────────────────┴──────────────────────┴──────────────────────┘

  Proceed with moving 4 file(s)? [y/N]:
```

---

## ✨ Features

- **Natural language instructions** — type what you want, in any language
- **Dry-run mode** — always preview before touching the filesystem
- **Safe by design** — never overwrites files (auto-renames conflicts), never deletes
- **OpenAI & X.AI (Grok) support** — plug in the API key you already have
- **Structured LLM output** — deterministic JSON schema, not fragile text parsing
- **Japanese (日本語) fully supported** — instructions, folder names, filenames
- **Beautiful terminal UI** — powered by Rich
- **Configurable** — exclude patterns, max files, per-project `.file-organizer.toml`

---

## 📦 Installation

### pip / pipx (recommended)

```bash
# One-off use (recommended — keeps your global Python clean)
pipx install ai-file-organizer

# Or with pip
pip install ai-file-organizer
```

### Homebrew (macOS / Linux)

```bash
# Coming soon — tap will be added after first PyPI release
brew install youi2000jp4/tap/ai-file-organizer
```

### From source

```bash
git clone https://github.com/youi2000jp4/ai-file-organizer.git
cd ai-file-organizer
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### 1. Set your API key

```bash
# OpenAI
file-org config set-key sk-...

# Or X.AI (Grok)
file-org config set-key xai-... --provider xai
file-org config set provider xai

# Or use environment variables
export OPENAI_API_KEY=sk-...
```

### 2. Organize!

```bash
# Preview first (always a good idea)
file-org "Sort by file type" ~/Downloads --dry-run

# Execute with confirmation
file-org "ダウンロードフォルダを種類別に整理して" ~/Downloads

# Skip confirmation prompt
file-org "Move PDFs to documents folder" ~/Desktop --yes

# Recursive (including subdirectories)
file-org "Group photos by year" ~/Pictures --recursive

# Use a different model
file-org "Clean up" --model gpt-4o
```

---

## 📖 Command Reference

```
Usage: file-org [OPTIONS] INSTRUCTION [TARGET]

  Organize files with a natural language instruction.

Arguments:
  INSTRUCTION  Natural language instruction (Japanese OK)  [required]
  TARGET       Target directory  [default: current directory]

Options:
  -n, --dry-run       Preview changes without moving files
  -y, --yes           Skip confirmation prompt
  -r, --recursive     Scan subdirectories recursively
  -m, --model TEXT    Override LLM model
  --max-files INT     Max files to send to LLM  [default: 300]
  --help              Show this message and exit.

Config subcommands:
  file-org config show              Show current configuration
  file-org config set-key KEY       Save API key
  file-org config set KEY VALUE     Set a config option
  file-org config init              Create default config file
```

---

## ⚙️ Configuration

Config is stored at `~/.config/file-organizer/config.toml`.  
API keys are stored in `~/.config/file-organizer/.env` (chmod 600 — never committed).

```toml
# ~/.config/file-organizer/config.toml
provider = "openai"          # "openai" or "xai"
model = "gpt-4o-mini"        # any model your provider supports
max_files = 300              # max files per LLM call
confirm_before_execute = true
exclude_patterns = [".DS_Store", "*.pyc", "node_modules"]
```

### Per-project override

Place a `.file-organizer.toml` in any directory to override settings for that project:

```toml
# .file-organizer.toml
exclude_patterns = [".git", "*.log", "tmp"]
max_files = 50
```

---

## 🛡️ Safety

| Risk | Mitigation |
|------|-----------|
| Accidental overwrite | Files are **never** overwritten — conflicts get a numeric suffix (`file_1.txt`) |
| Accidental delete | The tool only **moves** files. Deletion is not possible. |
| Hidden files | Hidden files (`.dotfiles`) are skipped unless explicitly included |
| Too many files | `max_files` limits LLM context. Extra files are skipped with a warning. |
| API errors | All LLM errors surface clearly; filesystem is not touched on failure |

**Recommended workflow:** always run with `--dry-run` first, review the table, then re-run without it.

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

```bash
git clone https://github.com/youi2000jp4/ai-file-organizer.git
cd ai-file-organizer
pip install -e ".[dev]"
pytest          # run tests
ruff check .    # lint
```

---

## 📄 License

[MIT](LICENSE) © ai-file-organizer contributors
