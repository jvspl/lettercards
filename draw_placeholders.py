#!/usr/bin/env python3
"""
Generate simple, cute placeholder images for letter cards.
Uses basic Pillow drawing — shapes, colors, and text labels.
"""

from PIL import Image, ImageDraw, ImageFont
import os

SIZE = (400, 400)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()


def draw_appel(draw, img):
    """Red apple with green leaf."""
    # Apple body
    draw.ellipse([100, 120, 300, 340], fill='#E63946', outline='#C1121F', width=3)
    # Stem
    draw.line([200, 120, 195, 80], fill='#5C4033', width=5)
    # Leaf
    draw.ellipse([200, 70, 260, 110], fill='#2D6A4F')
    # Shine
    draw.ellipse([140, 160, 170, 200], fill='#FF8FA3')


def draw_auto(draw, img):
    """Simple car."""
    # Body
    draw.rounded_rectangle([60, 180, 340, 300], radius=15, fill='#457B9D', outline='#1D3557', width=3)
    # Roof
    draw.rounded_rectangle([120, 120, 280, 195], radius=12, fill='#457B9D', outline='#1D3557', width=3)
    # Windows
    draw.rounded_rectangle([135, 135, 195, 185], radius=5, fill='#A8DADC')
    draw.rounded_rectangle([205, 135, 265, 185], radius=5, fill='#A8DADC')
    # Wheels
    draw.ellipse([90, 275, 150, 335], fill='#333', outline='#555', width=2)
    draw.ellipse([250, 275, 310, 335], fill='#333', outline='#555', width=2)
    draw.ellipse([105, 290, 135, 320], fill='#888')
    draw.ellipse([265, 290, 295, 320], fill='#888')
    # Headlight
    draw.ellipse([310, 220, 335, 250], fill='#F4A261')


def draw_banaan(draw, img):
    """Yellow banana."""
    # Banana curve using a thick arc
    draw.arc([50, 80, 350, 380], start=200, end=340, fill='#F4D35E', width=70)
    draw.arc([50, 80, 350, 380], start=200, end=340, fill='#E9C46A', width=60)
    # Tip
    draw.ellipse([70, 240, 100, 270], fill='#8B6914')
    # Top
    draw.rounded_rectangle([290, 95, 320, 125], radius=5, fill='#8B6914')


def draw_beer(draw, img):
    """Teddy bear."""
    # Body
    draw.ellipse([130, 200, 270, 350], fill='#C4A77D', outline='#8B6914', width=2)
    # Head
    draw.ellipse([120, 80, 280, 240], fill='#C4A77D', outline='#8B6914', width=2)
    # Ears
    draw.ellipse([100, 70, 150, 130], fill='#C4A77D', outline='#8B6914', width=2)
    draw.ellipse([250, 70, 300, 130], fill='#C4A77D', outline='#8B6914', width=2)
    draw.ellipse([110, 80, 140, 120], fill='#DEB887')
    draw.ellipse([260, 80, 290, 120], fill='#DEB887')
    # Eyes
    draw.ellipse([160, 140, 180, 165], fill='#333')
    draw.ellipse([220, 140, 240, 165], fill='#333')
    # Nose
    draw.ellipse([185, 170, 215, 195], fill='#333')
    # Mouth
    draw.arc([175, 180, 225, 215], start=0, end=180, fill='#333', width=2)
    # Belly
    draw.ellipse([160, 230, 240, 320], fill='#DEB887')


def draw_bal(draw, img):
    """Colorful ball."""
    draw.ellipse([80, 80, 320, 320], fill='#E63946', outline='#C1121F', width=3)
    # Stripes
    draw.arc([80, 80, 320, 320], start=60, end=120, fill='#FFF', width=20)
    draw.arc([80, 80, 320, 320], start=240, end=300, fill='#457B9D', width=20)
    # Shine
    draw.ellipse([130, 120, 170, 160], fill='#FF8FA3')


def draw_boom(draw, img):
    """Tree."""
    # Trunk
    draw.rectangle([175, 220, 225, 360], fill='#8B6914', outline='#5C4033', width=2)
    # Crown
    draw.ellipse([80, 60, 320, 260], fill='#2D6A4F', outline='#1B4332', width=2)
    draw.ellipse([60, 100, 250, 240], fill='#40916C')
    draw.ellipse([150, 50, 340, 230], fill='#52B788')


def draw_bad(draw, img):
    """Bathtub."""
    # Tub
    draw.rounded_rectangle([50, 160, 350, 320], radius=20, fill='#FFF', outline='#457B9D', width=4)
    # Water
    draw.rounded_rectangle([60, 200, 340, 310], radius=15, fill='#A8DADC')
    # Bubbles
    for x, y, r in [(100, 170, 15), (130, 155, 12), (160, 165, 10), (280, 160, 13), (310, 175, 11)]:
        draw.ellipse([x-r, y-r, x+r, y+r], fill='#E8F4F8', outline='#A8DADC', width=1)
    # Faucet
    draw.rectangle([310, 130, 330, 180], fill='#888', outline='#666', width=2)
    draw.rounded_rectangle([290, 120, 340, 140], radius=5, fill='#888', outline='#666', width=2)
    # Legs
    draw.ellipse([70, 310, 100, 340], fill='#888')
    draw.ellipse([300, 310, 330, 340], fill='#888')


def draw_deur(draw, img):
    """Door."""
    # Door frame
    draw.rectangle([110, 50, 290, 360], fill='#8B6914', outline='#5C4033', width=3)
    # Door panel
    draw.rectangle([125, 65, 275, 345], fill='#C19A6B', outline='#8B6914', width=2)
    # Panels
    draw.rectangle([140, 80, 260, 180], outline='#8B6914', width=2)
    draw.rectangle([140, 200, 260, 330], outline='#8B6914', width=2)
    # Handle
    draw.ellipse([245, 210, 265, 230], fill='#F4D35E', outline='#C9A227', width=2)


def draw_draak(draw, img):
    """Simple dragon."""
    # Body
    draw.ellipse([100, 150, 300, 320], fill='#2D6A4F', outline='#1B4332', width=2)
    # Head
    draw.ellipse([220, 80, 340, 190], fill='#2D6A4F', outline='#1B4332', width=2)
    # Eye
    draw.ellipse([275, 115, 305, 145], fill='#FFF')
    draw.ellipse([283, 123, 300, 140], fill='#E63946')
    draw.ellipse([288, 128, 296, 136], fill='#000')
    # Nose smoke
    draw.ellipse([330, 130, 350, 145], fill='#F4A261')
    draw.ellipse([345, 125, 365, 140], fill='#F4A261')
    # Wings
    draw.polygon([(180, 150), (100, 60), (150, 150)], fill='#40916C', outline='#1B4332', width=2)
    draw.polygon([(210, 150), (160, 50), (240, 130)], fill='#52B788', outline='#1B4332', width=2)
    # Tail
    draw.polygon([(100, 250), (40, 280), (60, 240)], fill='#2D6A4F', outline='#1B4332', width=2)
    # Spikes
    for x in [230, 250, 270]:
        draw.polygon([(x, 90), (x+10, 60), (x+20, 90)], fill='#F4A261')
    # Belly
    draw.ellipse([140, 200, 260, 300], fill='#52B788')


def draw_druif(draw, img):
    """Bunch of grapes."""
    # Stem
    draw.line([200, 60, 200, 110], fill='#5C4033', width=4)
    # Leaf
    draw.ellipse([200, 50, 270, 100], fill='#2D6A4F')
    # Grapes cluster
    positions = [
        (170, 120), (210, 120), (250, 120),
        (150, 160), (190, 160), (230, 160), (270, 160),
        (160, 200), (200, 200), (240, 200), (280, 200),
        (170, 240), (210, 240), (250, 240),
        (190, 280), (230, 280),
        (210, 310),
    ]
    for x, y in positions:
        draw.ellipse([x-18, y-18, x+18, y+18], fill='#6A4C93', outline='#5A3D82', width=1)
        draw.ellipse([x-10, y-14, x-2, y-6], fill='#8B6DB0')


def draw_eend(draw, img):
    """Duck."""
    # Body
    draw.ellipse([80, 180, 300, 330], fill='#F4D35E', outline='#C9A227', width=2)
    # Head
    draw.ellipse([220, 90, 340, 210], fill='#F4D35E', outline='#C9A227', width=2)
    # Eye
    draw.ellipse([280, 125, 305, 150], fill='#FFF')
    draw.ellipse([287, 130, 302, 145], fill='#000')
    # Beak
    draw.polygon([(330, 155), (380, 165), (330, 180)], fill='#E76F51', outline='#C1440E', width=2)
    # Wing
    draw.ellipse([100, 200, 230, 290], fill='#E9C46A', outline='#C9A227', width=2)
    # Water
    draw.ellipse([50, 290, 350, 370], fill='#A8DADC')


def draw_fiets(draw, img):
    """Bicycle."""
    # Wheels
    draw.ellipse([50, 200, 170, 320], outline='#333', width=4)
    draw.ellipse([230, 200, 350, 320], outline='#333', width=4)
    # Spokes center
    draw.ellipse([100, 250, 120, 270], fill='#888')
    draw.ellipse([280, 250, 300, 270], fill='#888')
    # Frame
    draw.line([110, 260, 200, 160], fill='#E63946', width=4)  # down tube
    draw.line([290, 260, 200, 160], fill='#E63946', width=4)  # chain stay
    draw.line([110, 260, 200, 260], fill='#E63946', width=4)  # bottom
    draw.line([200, 260, 290, 260], fill='#E63946', width=4)
    # Seat
    draw.rounded_rectangle([180, 140, 220, 155], radius=3, fill='#333')
    # Handlebars
    draw.line([290, 260, 310, 160], fill='#E63946', width=4)
    draw.line([290, 160, 330, 155], fill='#333', width=3)
    # Pedals
    draw.line([195, 260, 195, 285], fill='#333', width=3)
    draw.line([205, 260, 205, 235], fill='#333', width=3)


def draw_huis(draw, img):
    """House."""
    # Wall
    draw.rectangle([80, 180, 320, 360], fill='#E9C46A', outline='#C9A227', width=2)
    # Roof
    draw.polygon([(60, 185), (200, 60), (340, 185)], fill='#E63946', outline='#C1121F', width=2)
    # Door
    draw.rectangle([170, 250, 230, 360], fill='#8B6914', outline='#5C4033', width=2)
    draw.ellipse([218, 295, 228, 305], fill='#F4D35E')
    # Window
    draw.rectangle([100, 210, 155, 260], fill='#A8DADC', outline='#457B9D', width=2)
    draw.line([127, 210, 127, 260], fill='#457B9D', width=2)
    draw.line([100, 235, 155, 235], fill='#457B9D', width=2)
    draw.rectangle([245, 210, 300, 260], fill='#A8DADC', outline='#457B9D', width=2)
    draw.line([272, 210, 272, 260], fill='#457B9D', width=2)
    draw.line([245, 235, 300, 235], fill='#457B9D', width=2)


def draw_hand(draw, img):
    """Hand / palm."""
    # Palm
    draw.ellipse([120, 180, 280, 360], fill='#F4D4B0', outline='#D4A574', width=2)
    # Fingers
    for x, h in [(135, 100), (165, 70), (195, 60), (225, 80), (255, 120)]:
        draw.rounded_rectangle([x, h, x+30, 220], radius=15, fill='#F4D4B0', outline='#D4A574', width=2)
    # Thumb
    draw.rounded_rectangle([90, 200, 130, 300], radius=15, fill='#F4D4B0', outline='#D4A574', width=2)


def draw_jas(draw, img):
    """Jacket / coat."""
    # Body
    draw.rectangle([120, 100, 280, 340], fill='#457B9D', outline='#1D3557', width=2)
    # Collar
    draw.polygon([(120, 100), (200, 140), (280, 100), (240, 100), (200, 120), (160, 100)], fill='#1D3557')
    # Sleeves
    draw.rectangle([60, 110, 125, 260], fill='#457B9D', outline='#1D3557', width=2)
    draw.rectangle([275, 110, 340, 260], fill='#457B9D', outline='#1D3557', width=2)
    # Buttons
    for y in [170, 220, 270]:
        draw.ellipse([193, y, 207, y+14], fill='#FFF', outline='#DDD', width=1)
    # Zipper line
    draw.line([200, 140, 200, 340], fill='#1D3557', width=2)


def draw_kat(draw, img):
    """Cat."""
    # Body
    draw.ellipse([100, 180, 280, 340], fill='#F4A261', outline='#C17D3A', width=2)
    # Head
    draw.ellipse([130, 80, 270, 210], fill='#F4A261', outline='#C17D3A', width=2)
    # Ears
    draw.polygon([(140, 100), (120, 40), (175, 90)], fill='#F4A261', outline='#C17D3A', width=2)
    draw.polygon([(260, 100), (280, 40), (225, 90)], fill='#F4A261', outline='#C17D3A', width=2)
    draw.polygon([(148, 100), (130, 55), (170, 95)], fill='#FFB7A5')
    draw.polygon([(252, 100), (270, 55), (230, 95)], fill='#FFB7A5')
    # Eyes
    draw.ellipse([160, 125, 185, 155], fill='#2D6A4F')
    draw.ellipse([215, 125, 240, 155], fill='#2D6A4F')
    draw.ellipse([168, 132, 180, 148], fill='#000')
    draw.ellipse([223, 132, 235, 148], fill='#000')
    # Nose
    draw.polygon([(195, 160), (205, 160), (200, 170)], fill='#FFB7A5')
    # Whiskers
    for dy in [-5, 5]:
        draw.line([150, 165+dy, 100, 160+dy*2], fill='#C17D3A', width=1)
        draw.line([250, 165+dy, 300, 160+dy*2], fill='#C17D3A', width=1)
    # Tail
    draw.arc([260, 200, 360, 340], start=180, end=350, fill='#F4A261', width=8)


def draw_koe(draw, img):
    """Cow."""
    # Body
    draw.ellipse([70, 160, 310, 320], fill='#FFF', outline='#333', width=2)
    # Spots
    draw.ellipse([110, 190, 170, 240], fill='#333')
    draw.ellipse([200, 210, 260, 270], fill='#333')
    draw.ellipse([140, 260, 190, 300], fill='#333')
    # Head
    draw.ellipse([250, 100, 370, 220], fill='#FFF', outline='#333', width=2)
    # Eyes
    draw.ellipse([285, 135, 305, 155], fill='#000')
    draw.ellipse([325, 135, 345, 155], fill='#000')
    # Nose
    draw.ellipse([290, 165, 350, 210], fill='#FFB7A5', outline='#C17D3A', width=2)
    draw.ellipse([300, 178, 315, 193], fill='#C17D3A')
    draw.ellipse([325, 178, 340, 193], fill='#C17D3A')
    # Horns
    draw.arc([285, 80, 310, 120], start=180, end=0, fill='#C9A227', width=4)
    draw.arc([340, 80, 365, 120], start=180, end=0, fill='#C9A227', width=4)
    # Legs
    for x in [110, 170, 220, 270]:
        draw.rectangle([x, 300, x+20, 360], fill='#FFF', outline='#333', width=2)


def draw_leeuw(draw, img):
    """Lion."""
    # Mane
    draw.ellipse([80, 60, 320, 300], fill='#C9A227')
    # Face
    draw.ellipse([120, 100, 280, 260], fill='#F4D35E', outline='#C9A227', width=2)
    # Eyes
    draw.ellipse([155, 150, 185, 175], fill='#FFF')
    draw.ellipse([215, 150, 245, 175], fill='#FFF')
    draw.ellipse([163, 155, 180, 172], fill='#5C4033')
    draw.ellipse([223, 155, 240, 172], fill='#5C4033')
    # Nose
    draw.polygon([(190, 195), (210, 195), (200, 210)], fill='#C17D3A')
    # Mouth
    draw.arc([180, 205, 220, 235], start=0, end=180, fill='#C17D3A', width=2)
    # Body
    draw.ellipse([130, 240, 270, 370], fill='#F4D35E', outline='#C9A227', width=2)


def draw_lamp(draw, img):
    """Table lamp."""
    # Shade
    draw.polygon([(120, 100), (200, 60), (280, 100), (300, 200), (100, 200)], fill='#F4D35E', outline='#C9A227', width=2)
    # Light glow
    draw.ellipse([150, 120, 250, 190], fill='#FFF8E7')
    # Stem
    draw.rectangle([190, 200, 210, 310], fill='#888', outline='#666', width=2)
    # Base
    draw.ellipse([140, 300, 260, 340], fill='#888', outline='#666', width=2)


def draw_melk(draw, img):
    """Milk carton."""
    # Carton
    draw.rectangle([120, 80, 280, 340], fill='#FFF', outline='#457B9D', width=3)
    # Top
    draw.polygon([(120, 80), (200, 40), (280, 80)], fill='#457B9D', outline='#1D3557', width=2)
    # Label area
    draw.rectangle([135, 140, 265, 280], fill='#A8DADC', outline='#457B9D', width=2)
    # Text "MELK"
    font = get_font(28)
    draw.text((200, 200), "MELK", font=font, fill='#1D3557', anchor='mm')
    # Cow spot decoration
    draw.ellipse([155, 155, 195, 185], fill='#333')
    draw.ellipse([215, 170, 245, 195], fill='#333')


def draw_muis(draw, img):
    """Mouse."""
    # Body
    draw.ellipse([80, 180, 280, 330], fill='#AAAAAA', outline='#888', width=2)
    # Head
    draw.ellipse([200, 140, 340, 270], fill='#AAAAAA', outline='#888', width=2)
    # Ears
    draw.ellipse([220, 90, 280, 160], fill='#AAAAAA', outline='#888', width=2)
    draw.ellipse([290, 90, 350, 160], fill='#AAAAAA', outline='#888', width=2)
    draw.ellipse([230, 100, 270, 150], fill='#FFB7A5')
    draw.ellipse([300, 100, 340, 150], fill='#FFB7A5')
    # Eye
    draw.ellipse([280, 180, 300, 200], fill='#000')
    # Nose
    draw.ellipse([330, 200, 350, 218], fill='#FFB7A5')
    # Whiskers
    for dy in [-8, 0, 8]:
        draw.line([340, 210+dy, 390, 200+dy*2], fill='#888', width=1)
    # Tail
    draw.arc([20, 220, 120, 360], start=0, end=180, fill='#FFB7A5', width=4)


def draw_neus(draw, img):
    """Nose."""
    # Face background
    draw.ellipse([60, 60, 340, 340], fill='#F4D4B0')
    # Nose
    draw.polygon([(200, 130), (150, 280), (250, 280)], fill='#DEB887', outline='#C4A574', width=3)
    # Nostrils
    draw.ellipse([165, 250, 190, 275], fill='#C4A574')
    draw.ellipse([210, 250, 235, 275], fill='#C4A574')
    # Bridge highlight
    draw.line([200, 140, 195, 250], fill='#F4E4C4', width=4)


def draw_oog(draw, img):
    """Eye."""
    # Eye shape
    draw.ellipse([60, 100, 340, 300], fill='#FFF', outline='#333', width=3)
    # Iris
    draw.ellipse([130, 130, 270, 270], fill='#457B9D')
    # Pupil
    draw.ellipse([170, 170, 230, 230], fill='#000')
    # Reflection
    draw.ellipse([195, 160, 220, 185], fill='#FFF')
    # Eyelashes top
    for angle_x in [80, 120, 160, 200, 240, 280, 320]:
        draw.line([angle_x, 110, angle_x, 80], fill='#333', width=2)


def draw_olifant(draw, img):
    """Elephant."""
    # Body
    draw.ellipse([50, 130, 310, 310], fill='#8DA9C4', outline='#6B8EB0', width=2)
    # Head
    draw.ellipse([200, 80, 370, 250], fill='#8DA9C4', outline='#6B8EB0', width=2)
    # Ear
    draw.ellipse([250, 90, 370, 230], fill='#6B8EB0', outline='#5A7A9A', width=2)
    draw.ellipse([265, 110, 355, 220], fill='#A8C4DC')
    # Eye
    draw.ellipse([240, 140, 260, 160], fill='#FFF')
    draw.ellipse([245, 145, 258, 158], fill='#000')
    # Trunk
    draw.arc([200, 180, 280, 360], start=0, end=180, fill='#8DA9C4', width=25)
    draw.arc([200, 180, 280, 360], start=0, end=180, fill='#6B8EB0', width=3)
    # Legs
    for x in [80, 140, 200, 250]:
        draw.rectangle([x, 280, x+30, 360], fill='#8DA9C4', outline='#6B8EB0', width=2)
    # Tusk
    draw.arc([215, 190, 245, 260], start=270, end=90, fill='#FFF8F0', width=6)


def draw_peer(draw, img):
    """Pear."""
    # Bottom
    draw.ellipse([110, 180, 290, 350], fill='#A7C957', outline='#6A994E', width=2)
    # Top
    draw.ellipse([145, 100, 255, 230], fill='#A7C957', outline='#6A994E', width=2)
    # Stem
    draw.line([200, 105, 195, 65], fill='#5C4033', width=4)
    # Leaf
    draw.ellipse([195, 55, 250, 90], fill='#2D6A4F')
    # Shine
    draw.ellipse([155, 140, 180, 180], fill='#BFD979')


def draw_regen(draw, img):
    """Rain cloud."""
    # Cloud
    draw.ellipse([60, 60, 200, 170], fill='#8DA9C4')
    draw.ellipse([120, 40, 280, 150], fill='#8DA9C4')
    draw.ellipse([200, 60, 340, 170], fill='#8DA9C4')
    draw.ellipse([80, 90, 320, 180], fill='#8DA9C4')
    # Raindrops
    for x, y in [(100, 210), (150, 230), (200, 200), (250, 240), (300, 215),
                  (120, 280), (170, 300), (220, 270), (270, 310)]:
        draw.ellipse([x-5, y, x+5, y+15], fill='#457B9D')


def draw_sok(draw, img):
    """Sock."""
    # Leg part
    draw.rounded_rectangle([150, 60, 250, 250], radius=15, fill='#E63946', outline='#C1121F', width=2)
    # Foot part
    draw.rounded_rectangle([130, 230, 320, 320], radius=30, fill='#E63946', outline='#C1121F', width=2)
    # Toe
    draw.ellipse([260, 240, 330, 310], fill='#E63946', outline='#C1121F', width=2)
    # Stripes
    for y in [100, 130, 160]:
        draw.rectangle([150, y, 250, y+15], fill='#FFF')
    # Top cuff
    draw.rounded_rectangle([140, 55, 260, 90], radius=10, fill='#FFF', outline='#DDD', width=2)


def draw_schoen(draw, img):
    """Shoe."""
    # Sole
    draw.rounded_rectangle([40, 260, 360, 310], radius=15, fill='#333', outline='#222', width=2)
    # Shoe body
    draw.rounded_rectangle([60, 150, 340, 270], radius=20, fill='#457B9D', outline='#1D3557', width=3)
    # Toe cap
    draw.ellipse([40, 170, 160, 270], fill='#457B9D', outline='#1D3557', width=3)
    # Opening
    draw.ellipse([200, 130, 350, 200], fill='#1D3557')
    # Laces
    for x in [180, 210, 240]:
        draw.line([x, 155, x+25, 170], fill='#FFF', width=2)
        draw.line([x+25, 155, x, 170], fill='#FFF', width=2)


def draw_tand(draw, img):
    """Tooth."""
    # Tooth body
    draw.rounded_rectangle([130, 80, 270, 250], radius=30, fill='#FFF', outline='#DDD', width=3)
    # Roots
    draw.rounded_rectangle([140, 230, 180, 340], radius=10, fill='#FFF', outline='#DDD', width=3)
    draw.rounded_rectangle([220, 230, 260, 340], radius=10, fill='#FFF', outline='#DDD', width=3)
    # Shine
    draw.ellipse([160, 110, 190, 160], fill='#F8F8FF')
    # Happy face
    draw.ellipse([160, 140, 180, 160], fill='#333')
    draw.ellipse([220, 140, 240, 160], fill='#333')
    draw.arc([170, 170, 230, 210], start=0, end=180, fill='#333', width=2)


def draw_tafel(draw, img):
    """Table."""
    # Table top
    draw.rectangle([50, 150, 350, 185], fill='#C19A6B', outline='#8B6914', width=2)
    # Top surface
    draw.polygon([(30, 150), (370, 150), (350, 130), (50, 130)], fill='#D4A97A', outline='#8B6914', width=2)
    # Legs
    draw.rectangle([65, 185, 85, 340], fill='#C19A6B', outline='#8B6914', width=2)
    draw.rectangle([315, 185, 335, 340], fill='#C19A6B', outline='#8B6914', width=2)


def draw_vis(draw, img):
    """Fish."""
    # Body
    draw.ellipse([80, 130, 300, 290], fill='#F4A261', outline='#E76F51', width=3)
    # Tail
    draw.polygon([(85, 210), (30, 150), (30, 270)], fill='#E76F51', outline='#C1440E', width=2)
    # Eye
    draw.ellipse([230, 180, 265, 215], fill='#FFF')
    draw.ellipse([240, 188, 260, 208], fill='#000')
    # Fins
    draw.polygon([(190, 135), (200, 80), (230, 135)], fill='#E76F51', outline='#C1440E', width=2)
    draw.polygon([(170, 285), (190, 330), (220, 285)], fill='#E76F51', outline='#C1440E', width=2)
    # Scales
    for x, y in [(140, 180), (170, 200), (200, 185), (160, 225), (190, 240)]:
        draw.arc([x, y, x+30, y+25], start=0, end=180, fill='#E76F51', width=1)
    # Mouth
    draw.ellipse([290, 200, 310, 215], fill='#C1440E')
    # Bubbles
    draw.ellipse([320, 170, 335, 185], outline='#A8DADC', width=2)
    draw.ellipse([340, 150, 352, 162], outline='#A8DADC', width=2)


def draw_vlinder(draw, img):
    """Butterfly."""
    # Wings
    draw.ellipse([40, 80, 190, 220], fill='#6A4C93', outline='#5A3D82', width=2)
    draw.ellipse([210, 80, 360, 220], fill='#6A4C93', outline='#5A3D82', width=2)
    draw.ellipse([60, 200, 180, 320], fill='#E63946', outline='#C1121F', width=2)
    draw.ellipse([220, 200, 340, 320], fill='#E63946', outline='#C1121F', width=2)
    # Wing patterns
    draw.ellipse([85, 115, 145, 175], fill='#8B6DB0')
    draw.ellipse([255, 115, 315, 175], fill='#8B6DB0')
    draw.ellipse([95, 230, 145, 280], fill='#FF8FA3')
    draw.ellipse([255, 230, 305, 280], fill='#FF8FA3')
    # Body
    draw.ellipse([185, 100, 215, 300], fill='#333')
    # Antennae
    draw.line([200, 100, 160, 50], fill='#333', width=2)
    draw.line([200, 100, 240, 50], fill='#333', width=2)
    draw.ellipse([152, 42, 168, 58], fill='#333')
    draw.ellipse([232, 42, 248, 58], fill='#333')


def draw_water(draw, img):
    """Water drops / waves."""
    # Big drop
    draw.polygon([(200, 40), (130, 180), (200, 240), (270, 180)], fill='#457B9D')
    draw.ellipse([130, 160, 270, 250], fill='#457B9D')
    # Shine
    draw.ellipse([175, 140, 200, 180], fill='#A8DADC')
    # Waves at bottom
    for y_off in [0, 30]:
        for x in range(40, 360, 40):
            draw.arc([x-20, 280+y_off, x+20, 320+y_off], start=0, end=180, fill='#A8DADC', width=4)


def draw_zon(draw, img):
    """Sun."""
    # Rays
    import math
    cx, cy = 200, 200
    for i in range(12):
        angle = math.radians(i * 30)
        x1 = cx + int(90 * math.cos(angle))
        y1 = cy + int(90 * math.sin(angle))
        x2 = cx + int(160 * math.cos(angle))
        y2 = cy + int(160 * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill='#F4D35E', width=12)
    # Sun body
    draw.ellipse([110, 110, 290, 290], fill='#F4D35E', outline='#E9C46A', width=3)
    # Face
    draw.ellipse([155, 170, 180, 195], fill='#C9A227')
    draw.ellipse([220, 170, 245, 195], fill='#C9A227')
    draw.arc([160, 200, 240, 250], start=0, end=180, fill='#C9A227', width=3)


def draw_zebra(draw, img):
    """Zebra."""
    # Body
    draw.ellipse([60, 150, 300, 300], fill='#FFF', outline='#333', width=2)
    # Stripes on body
    for x in [100, 140, 180, 220, 260]:
        draw.line([x, 170, x-10, 290], fill='#333', width=8)
    # Head
    draw.ellipse([250, 80, 370, 200], fill='#FFF', outline='#333', width=2)
    # Head stripes
    draw.line([280, 100, 275, 180], fill='#333', width=5)
    draw.line([310, 95, 305, 185], fill='#333', width=5)
    draw.line([340, 100, 335, 170], fill='#333', width=5)
    # Eye
    draw.ellipse([290, 125, 310, 145], fill='#000')
    # Nose
    draw.ellipse([340, 150, 370, 180], fill='#FFB7A5')
    # Mane
    for x in [265, 280, 295, 310]:
        draw.rectangle([x, 70, x+8, 95], fill='#333')
    # Legs
    for x in [90, 150, 210, 260]:
        draw.rectangle([x, 280, x+20, 360], fill='#FFF', outline='#333', width=2)
        # Leg stripes
        for y in [290, 310, 330]:
            draw.rectangle([x, y, x+20, y+8], fill='#333')


# ── Mapping ──

DRAW_FUNCTIONS = {
    'appel': draw_appel, 'auto': draw_auto, 'banaan': draw_banaan,
    'beer': draw_beer, 'bal': draw_bal, 'boom': draw_boom, 'bad': draw_bad,
    'deur': draw_deur, 'draak': draw_draak, 'druif': draw_druif,
    'eend': draw_eend, 'fiets': draw_fiets, 'huis': draw_huis,
    'hand': draw_hand, 'jas': draw_jas, 'kat': draw_kat, 'koe': draw_koe,
    'leeuw': draw_leeuw, 'lamp': draw_lamp, 'melk': draw_melk,
    'muis': draw_muis, 'neus': draw_neus, 'oog': draw_oog,
    'olifant': draw_olifant, 'peer': draw_peer, 'regen': draw_regen,
    'sok': draw_sok, 'schoen': draw_schoen, 'tand': draw_tand,
    'tafel': draw_tafel, 'vis': draw_vis, 'vlinder': draw_vlinder,
    'water': draw_water, 'zon': draw_zon, 'zebra': draw_zebra,
}


def generate_all(images_dir):
    os.makedirs(images_dir, exist_ok=True)
    for word, draw_fn in DRAW_FUNCTIONS.items():
        path = os.path.join(images_dir, f"{word}.png")
        if os.path.exists(path):
            continue  # Don't overwrite existing images
        img = Image.new('RGB', SIZE, '#FFFAF0')
        draw = ImageDraw.Draw(img)
        try:
            draw_fn(draw, img)
            img.save(path)
            print(f"  Drew {word}.png")
        except Exception as e:
            print(f"  Error drawing {word}: {e}")


if __name__ == '__main__':
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    # Remove old placeholder images (but keep personal ones)
    for f in os.listdir(images_dir):
        if f.endswith('.png'):
            word = f.replace('.png', '')
            if word in DRAW_FUNCTIONS:
                os.remove(os.path.join(images_dir, f))
    generate_all(images_dir)
    print("\nDone! Placeholder images generated.")
