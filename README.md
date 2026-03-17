# Letterkaarten

A card generator for teaching a toddler to associate letter sounds with words — in Dutch.

Each word produces two printable cards:
- **Picture card**: image + word (first letter highlighted)
- **Letter card**: the letter itself

Output is a printable A4 PDF with 9 cards per page.

## Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate cards
python generate.py
```

This creates `letterkaarten.pdf` ready for printing.

## Documentation

See [CLAUDE.md](CLAUDE.md) for full documentation:
- How to add words and images
- Personal photo workflow
- Font and color configuration
- Architecture details
