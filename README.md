# lettercards

Generate printable A4 letter-learning cards for toddlers: picture cards (image + word, first letter in an accent color — warm for vowels, cool for consonants) and letter-family cards (one big letter plus a specimen row of its other everyday shapes — capital, serif, handwritten). Feed it a deck — a `deck.csv` word list plus images — and it renders a print-ready PDF. Fonts are bundled, so cards render identically everywhere.

## Usage

```bash
pip install git+https://github.com/jvspl/lettercards.git
lettercards render starter -o cards.pdf     # render the bundled starter deck
lettercards render path/to/your-deck -o cards.pdf
lettercards render starter --letters a,z    # only some letters
lettercards render starter --cards zebra    # reprint specific cards
lettercards check path/to/your-deck         # validate deck.csv and images
lettercards photo IMG_1234.jpg images/oma.png   # crop a photo into a square card image
```

## Deck format

A deck is a directory with a `deck.csv` and (optionally) an `images/` directory:

```csv
letter,word,image,language,status,notes
a,appel,appel.png,nl,active,
k,kasteel,,nl,idea,needs image
```

- `status`: `idea` (word without image yet), `active` (rendered), `retired` (skipped).
- `image` resolves against the deck's own `images/` first, then the bundled starter images.
- `language`: BCP-47-ish code (`nl`, `es`); shown as a small colored pill on each picture card. Defaults to `nl`.
- Lines starting with `#` are comments.

## Starter deck

`lettercards/starter/` is a complete, ready-to-print Dutch deck: 32 words with child-friendly pictograms (Nijntje-ish style), bundled with the package so `lettercards render starter` works anywhere after install. Image provenance and licensing are tracked in [lettercards/starter/images/SOURCES.md](lettercards/starter/images/SOURCES.md).

## Using the cards

Print on thick paper (≥ 200 g/m²) or laminate — plain paper doesn't survive toddlers. The deck grows with the child; don't use all of it at once. Words and letters can grow together from the very start: a child who loves a picture card can just as happily notice the colored letter on it, often well into the second year. You don't have to wait for a "right age" — recognising letters isn't gated behind one; it's blending them into words that usually comes later. So the ages below are the roughest of guides. Follow the child, not the number.

The stages overlap and are led by the child's interest — they are not gates to clear in order:

- **Naming — from ~1:** As soon as the child points at and names pictures — often early in the second year — start here. Show a card, say the word, let the child point and name. A handful at a time, led by the child's interest. The printed word is for you; the colored first letter is right there for the child to notice whenever she's curious about it.
- **First sounds — from ~2:** Sound games with the picture cards: “b-b-b… bal!” The colored first letter shows what to stress. Sort cards by first sound — all cards for a letter share their band color.
- **Letters — child-led, alongside words:** Bring in the letter-family cards and match picture cards to their letter. Many children are keen on letters as young toddlers — if she's already pointing at them, follow her lead rather than holding the cards back for a later age.
- **First words — once a few sounds are known:** When the child knows a handful of letter sounds, start blending them: say the sounds close together and let them melt into the word — “mmm-aaa-nnn… man”. Slide a finger under the letters as you go. Short, sound-it-out words first, with the picture there to confirm the answer. This is the bridge from single letters to reading.

### Two things about letters

- **A letter wears different clothes:** The same letter looks different as a capital and a small letter, in print and in handwriting — A and a are one letter. Children learn this by seeing it, not by being told: point out the same letter in its many forms, on the card, on a sign, in a name. The specimen row on each letter-family card is built for exactly this — one letter, different clothes.
- **A letter can make more than one sound:** Some letters aren't loyal to one sound. Vowels come short and long (the a in “appel” versus “maan”); a c can sound like a k or an s. Teach the sound in the card's word first — one letter, one sound — and mention the others only later, as “this one can also say…”. Don't crowd the first sound with its exceptions.

Say letter sounds, not names — “mmm”, not “em”. The word list is curated for this: the first letter is the first sound.

The same guidance prints as the final page(s) of a full `lettercards render`, so it travels with the deck. Filtered reprints (`--letters`/`--cards`) skip it; `--no-howto` omits it from a full render too.

## Project rules

- **Line budget: ≤ 1,000 lines of Python including tests.** A feature that threatens the budget gets questioned before the budget does.
- **No deck-management commands.** Adding words or changing statuses is editing `deck.csv` directly — by hand or by an assistant — not CLI work.
- **PRs only for changes that could break rendering.** Docs and starter-deck tweaks go straight to `main`.

## Privacy rule

This repo is public and generic. Personal data — family photos, names, per-child progress — never goes here, not in code, fixtures, issues, or commit messages. Keep your own deck in a private repo or local directory.
