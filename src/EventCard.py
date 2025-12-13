from PIL import Image, ImageDraw, ImageFont

CARD_WIDTH = 600
CARD_HEIGHT = 300
CORNER_RADIUS = 30
FONT_PATH = r"assets\RuneScape-Chat-Bold-07.ttf"
ICON_SIZE = 30  # Size for each icon

def create_card_with_side_icons(title_text, left_icon_path=None, right_icon_path=None):
    # ---------- Load background image exactly as-is ----------
    card = Image.open("assets/red-gloss-background.png").convert("RGBA")
    card = card.resize((CARD_WIDTH, CARD_HEIGHT))

    draw = ImageDraw.Draw(card)

    # ---------- Title ----------
    title_font = ImageFont.truetype(FONT_PATH, 40)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (CARD_WIDTH - text_width) // 2
    text_y = 20

    draw.text((text_x, text_y), title_text, fill="yellow", font=title_font)  # Main title in white

    # ---------- Subtitle below title ----------
    subtitle_text = "Hunt 14 - BigBloor vs Zachhh"
    subtitle_font = ImageFont.truetype(FONT_PATH, 16)
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]

    subtitle_x = (CARD_WIDTH - subtitle_width) // 2
    subtitle_y = text_y + text_height + 5  # 5px gap below title

    draw.text((subtitle_x, subtitle_y), subtitle_text, fill="yellow", font=subtitle_font)

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

    # ---------- Bottom-right "Powered by Flux" ----------
    footer_text = "Powered by Flux"
    footer_font = ImageFont.truetype(FONT_PATH, 12)
    footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    footer_height = footer_bbox[3] - footer_bbox[1]

    footer_x = CARD_WIDTH - footer_width - 10  # 10px padding from right
    footer_y = CARD_HEIGHT - footer_height - 10  # 10px padding from bottom

    draw.text((footer_x, footer_y), footer_text, fill="yellow", font=footer_font)

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
    filename = "assets/hunt14_card_side_icons.png"
    rounded.save(filename)
    print(f"Saved {filename}")

    return filename


if __name__ == "__main__":
    create_card_with_side_icons("Snape Grass", left_icon_path="assets/lieutenant-icon.png", right_icon_path="assets/lieutenant-icon.png")
