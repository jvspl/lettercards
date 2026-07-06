"""Shared 'Using the cards' guidance.

Single source of truth: the PDF how-to page is drawn from these strings, and a
test asserts the README's "Using the cards" section mirrors them verbatim — so
the printed guidance and the README can't drift.

Deliberately minimal (v2): a practical page, not a pedagogy. The staged
letter-learning progression is frozen for v3 — see issue #26.
"""

TITLE = "Using the cards"

INTRO = ("Print on thick paper (≥ 200 g/m²) or laminate — plain paper doesn't survive "
         "toddlers. The deck grows with the child; don't use all of it at once — show a "
         "handful of cards at a time, led by the child's interest.")

OUTRO = ("Say letter sounds, not names — “mmm”, not “em”. The word list "
         "is curated for this: the first letter is the first sound.")
