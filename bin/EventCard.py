from PIL import Image, ImageDraw, ImageFont

CARD_WIDTH = 600
CARD_HEIGHT = 300
CORNER_RADIUS = 30
FONT_PATH = r"assets\RuneScape-Chat-Bold-07.ttf"
ICON_SIZE = 50  # Size for each icon

def create_card_with_side_icons(title_text, left_icon_path=None, right_icon_path=None):
    # ---------- Load background image exactly as-is ----------
    card = Image.open("bin/red-gloss-background.png").convert("RGBA")
    card = card.resize((CARD_WIDTH, CARD_HEIGHT))

    draw = ImageDraw.Draw(card)

    # ---------- Title ----------
    title_font = ImageFont.truetype(FONT_PATH, 40)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (CARD_WIDTH - text_width) // 2
    text_y = 20

    draw.text((text_x, text_y), title_text, fill="yellow", font=title_font)

    # ---------- Icons left and right ----------
    icon_y = text_y + (text_height - ICON_SIZE) // 2
    spacing = 10

    if left_icon_path:
        try:
            left_icon = Image.open(left_icon_path).convert("RGBA").resize((ICON_SIZE, ICON_SIZE))
            left_x = text_x - ICON_SIZE - spacing
            card.paste(left_icon, (left_x, icon_y), left_icon)
        except Exception as e:
            print(f"Failed to load left icon {left_icon_path}: {e}")

    if right_icon_path:
        try:
            right_icon = Image.open(right_icon_path).convert("RGBA").resize((ICON_SIZE, ICON_SIZE))
            right_x = text_x + text_width + spacing
            card.paste(right_icon, (right_x, icon_y), right_icon)
        except Exception as e:
            print(f"Failed to load right icon {right_icon_path}: {e}")

    # ---------- Apply rounded corner mask ----------
    mask = Image.new("L", (CARD_WIDTH, CARD_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (CARD_WIDTH, CARD_HEIGHT)],
        radius=CORNER_RADIUS,
        fill=255
    )

    rounded = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT))
    rounded.paste(card, (0, 0), mask)

    # ---------- Save ----------
    filename = "hunt14_card_side_icons.png"
    rounded.save(filename)
    print(f"Saved {filename}")

    return filename

if __name__ == "__main__":
    # create_card_with_side_icons(
    #     "Hunt 14",
    #     left_icon_path="bin/hunt-14-icon.jpg",
    #     right_icon_path="bin/hunt-14-icon.jpg"
    # )
        create_card_with_side_icons(
        "Hunt 14"
    )

