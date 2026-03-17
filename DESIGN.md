# Card Design Reference

## Card dimensions

- **Card size**: 6cm × 9cm (~170 × 255 points)
- **Page**: A4 (210 × 297mm)
- **Grid**: 3 columns × 3 rows = 9 cards per page
- **Margins**: 0.8cm page margin, 0.3cm gap between cards
- **Corner radius**: 3mm rounded corners

## Picture card layout

```
┌──────────────┐
│ a             │  ← small letter indicator (12pt, accent color)
│               │
│   [IMAGE]     │  ← top ~65% of card, centered with aspect ratio preserved
│               │
│               │
│   appel       │  ← bottom ~28%, word centered, first letter in accent color
│               │
└──────────────┘
```

- Image area: 4mm inner margin, top 65% of card height
- Word area: positioned at 8% from bottom
- Font size: auto-scales from 28pt down to 12pt to fit card width
- If no image exists and `personal=yes`: shows `[foto: word]` placeholder in tinted box
- If no image exists and `personal=no`: generate.py calls placeholder generator

## Letter card layout

```
┌──────────────┐
│               │
│               │
│      a        │  ← 120pt, accent color, centered
│               │
│      A        │  ← 24pt, accent color at 40% opacity, centered at bottom
│               │
└──────────────┘
```

- Background: light blue (#F0F7FF)
- Shows lowercase as primary, uppercase as secondary (or vice versa)
- One letter card per unique letter (not per word)

## Color palette

### Background colors
- Picture cards: `#FFF8F0` (warm cream)
- Letter cards: `#F0F7FF` (light blue)
- Card border: `#CCCCCC`

### Letter accent colors
| Letter | Color | Hex |
|--------|-------|-----|
| a | red | #E63946 |
| b | blue | #457B9D |
| d | teal | #2A9D8F |
| e | orange | #F4A261 |
| f | purple | #6A4C93 |
| h | coral | #E76F51 |
| k | orange | #F4A261 |
| l | teal | #2A9D8F |
| m | red | #E63946 |
| n | blue | #457B9D |
| o | gold | #E9C46A |
| p | purple | #6A4C93 |
| r | coral | #E76F51 |
| s | teal | #2A9D8F |
| t | orange | #F4A261 |
| v | blue | #457B9D |
| w | dark blue | #1D3557 |
| z | red | #E63946 |

Word text color: `#2B2D42` (dark blue-gray)

## Font rotation

Cards automatically rotate between available fonts for variety. The font is selected by hashing the word, so the same word always gets the same font (deterministic). Available system fonts:

- DejaVuSans (clean sans-serif)
- Lato (modern sans-serif)
- Carlito (Calibri-like)
- LiberationSans (Arial-like)

Custom .ttf fonts in `fonts/` are auto-registered.

## Placeholder images

`draw_placeholders.py` creates 400×400 pixel PNG images using Pillow shape drawing. Each word has a custom drawing function (e.g., `draw_appel` draws a red circle with a green leaf). The images are simple and cartoon-like, suitable for a toddler.

Images are only generated if they don't already exist, so personal photos or upgraded images won't be overwritten.

## Printing recommendations

- Paper: 160+ g/m² for sturdiness, or regular paper + lamination
- Cut along card edges after printing
- Consider double-sided printing with a neutral pattern on the back
