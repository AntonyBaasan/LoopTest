# LoopTest

Python CLI for executing YAML-defined UI tests against Chrome with Selenium.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python executor.py tests/
python executor.py tests/01_menu_navigation.yaml
python executor.py tests/ --headless
python executor.py tests/ --stop-on-fail
python executor.py tests/ --timeout 3
```

## YAML schema

Top-level keys:

- `name`: suite name
- `description`: optional suite description
- `base_url`: root URL for relative navigation
- `timeout`: optional per-step timeout in seconds, defaults to `10`
- `steps`: ordered list of step objects

Step keys:

- `id`: optional step identifier
- `action`: one of `navigate`, `click`, `hover`, `menu_navigate`, `type`, `toggle`, `select`, `custom_select`
- `assert`: optional assertion object

Selector prefixes:

- `css:`
- `xpath:`
- `id:`
- `name:`
- `text=`
- bare selector falls back to CSS
- `A >> B` performs a scoped child lookup inside the parent selector

Assertions:

- `title_contains`
- `url_contains`
- `element_visible`
- `element_hidden`
- `element_missing_class`
- `attribute`
- `element_text`
