---
name: get-gold-prices
description: >
  Get vn gold prices by running a Python script. Use this skill whenever the user
  asks to get the gold prices. Trigger on keywords like: gold price(s), giá vàng, vàng, vàng nhẫn, vàng miếng.
---

# My Skill

## Setup

Run the setup script to ensure dependencies are installed. This only
installs on the first run; subsequent runs are instant.

\`\`\`bash
chmod +x <skill-path>/scripts/setup.sh
bash <skill-path>/scripts/setup.sh
\`\`\`

## Running

Activate the virtual environment and run the script:

\`\`\`bash
source ~/.local/share/get-gold-prices-skill-venv/bin/activate
python <skill-path>/scripts/main.py
deactivate
\`\`\`

## What it does

The script goes through a list of vnmese websites that have gold price listings and scrapes those data. Then outputs a json file with these prices categorized by gold types.
