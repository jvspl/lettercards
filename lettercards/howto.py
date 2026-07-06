"""Shared 'Using the cards' guidance.

Single source of truth: the final PDF how-to page is drawn from these
strings, and a test asserts the README's "Using the cards" section mirrors
them verbatim — so the printed guidance and the README can't drift.
"""

TITLE = "Using the cards"

INTRO = ("Print on thick paper (≥ 200 g/m²) or laminate — plain paper doesn't survive "
         "toddlers. The deck grows with the child; don't use all of it at once. The ages "
         "below are the roughest of guides: children vary enormously and many are keen on "
         "letters long before they're \"supposed\" to be — follow the child, not the number.")

# (stage, indicative ages, what to do)
STAGES = [
    ("Naming", "from ~1",
     "As soon as the child points at and names pictures — often early in the second year — "
     "start here. Picture cards only; letter cards stay in the drawer. Show a card, say the "
     "word, let the child point and name. A handful of cards at a time, led by the child's "
     "interest. The printed word is for you, not them."),
    ("First sounds", "from ~2",
     "Sound games with the picture cards: “b-b-b… bal!” The colored first letter shows what "
     "to stress. Sort cards by first sound — all cards for a letter share their band color."),
    ("Letters", "child-led, often 2–5",
     "Bring in the letter-family cards; match picture cards to their letter. Plenty of "
     "children are fascinated by letters as toddlers — if she's already pointing at them, "
     "follow her lead. The specimen row is the same letter in different clothes."),
]

OUTRO = ("Say letter sounds, not names — “mmm”, not “em”. The word list "
         "is curated for this: the first letter is the first sound.")
