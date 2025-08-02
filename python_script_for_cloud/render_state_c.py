from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import requests

def render_state_c(topic_text, speaker_name, image_url, abstract_text, width=640, height=480):
    background_color = (0, 0, 0)
    white = (255, 255, 255)
    red = (255, 0, 0)
    green = (0, 255, 0)
    margin = 30
    photo_size = (220, 220)
    max_font_size = 30
    min_font_size = 14

    canvas = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(canvas)

    # === Load speaker photo ===
    try:
        if "drive.google.com/open?id=" in image_url:
            image_url = image_url.replace("open?id=", "uc?id=")

        response = requests.get(image_url)
        response.raise_for_status()
        speaker_img = Image.open(BytesIO(response.content)).convert("RGB").resize(photo_size)
        canvas.paste(speaker_img, (width - photo_size[0] - margin, margin))
    except Exception as e:
        print(f"[WARN] Could not load speaker image: {e}")

    # === Font loader ===
    def get_font(name, size):
        font_path = os.path.join("fonts", name)
        return ImageFont.truetype(font_path, size) if os.path.exists(font_path) else ImageFont.load_default()

    # === Text wrapping ===
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    # === Justified line drawer ===
    def draw_justified_line(text, y, font, max_width, color):
        words = text.split()
        if len(words) <= 1:
            draw.text((margin, y), text, font=font, fill=color)
            return get_line_height(font)

        line_width = draw.textlength(text, font=font)
        total_spacing = max_width - line_width
        space_count = len(words) - 1
        space_widths = [draw.textlength(" ", font=font)] * space_count

        if space_count > 0:
            extra_space = total_spacing / space_count
            space_widths = [sw + extra_space for sw in space_widths]

        x = margin
        for i, word in enumerate(words):
            draw.text((x, y), word, font=font, fill=color)
            x += draw.textlength(word, font=font)
            if i < len(space_widths):
                x += space_widths[i]

        return get_line_height(font)

    # === Accurate line height ===
    def get_line_height(font):
        ascent, descent = font.getmetrics()
        return ascent + descent + 4  # +4 padding

    # === Topic Rendering ===
    topic_area_width = width - photo_size[0] - 3 * margin
    topic_area_height = photo_size[1]

    for size in range(max_font_size, min_font_size - 1, -2):
        topic_font = get_font("arialbd.ttf", size)
        topic_lines = wrap_text(topic_text, topic_font, topic_area_width)
        topic_height = len(topic_lines) * get_line_height(topic_font)
        if topic_height <= topic_area_height:
            break

    y = margin
    for line in topic_lines:
        text_width = draw.textlength(line, font=topic_font)
        x = margin + (topic_area_width - text_width) // 2
        draw.text((x, y), line, font=topic_font, fill=red)
        y += get_line_height(topic_font)

    topic_bottom_y = y

    # === Speaker Name Rendering ===
    speaker_text = f"Speaker: {speaker_name}"
    speaker_area_width = width - photo_size[0] - 2 * margin

    for size in range(24, 12, -1):
        speaker_font = get_font("arialbd.ttf", size)
        if draw.textlength(speaker_text, font=speaker_font) <= speaker_area_width:
            break

    speaker_x = margin + (speaker_area_width - draw.textlength(speaker_text, font=speaker_font)) // 2
    speaker_y = (topic_bottom_y + height // 2 - margin) // 2
    draw.text((speaker_x, speaker_y), speaker_text, font=speaker_font, fill=green)

    # === Abstract Rendering (Adaptive Font) ===
    abstract_top = height // 2 + margin
    abstract_width = width - 2 * margin
    abstract_height = height // 2 - 2 * margin
    paragraphs = [p.strip() for p in abstract_text.strip().split("\n") if p.strip()]

    for size in range(22, min_font_size, -1):
        abstract_font = get_font("arial.ttf", size)
        wrapped_paragraphs = [wrap_text(p, abstract_font, abstract_width) for p in paragraphs]
        total_lines = sum(len(p) for p in wrapped_paragraphs)
        line_height = get_line_height(abstract_font)
        total_height = total_lines * line_height + (len(paragraphs) - 1) * 10
        if total_height <= abstract_height:
            break

    # Draw abstract
    y = abstract_top + (abstract_height - total_height) // 2
    for para in wrapped_paragraphs:
        for i, line in enumerate(para):
            if i == len(para) - 1:
                draw.text((margin, y), line, font=abstract_font, fill=white)
            else:
                draw_justified_line(line, y, abstract_font, abstract_width, white)
            y += line_height
        y += 10  # space between paragraphs

    return canvas  # Return the final image object
