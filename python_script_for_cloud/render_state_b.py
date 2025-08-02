from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os

def render_state_b(meeting_topic, meeting_time_date, speaker_name, width=640, height=480):
    background_color = (0, 0, 0)
    white = (255, 255, 255)
    red = (255, 0, 0)
    green = (0, 255, 0)
    yellow = (255, 255, 0)
    margin = 40
    topic_max_font_size = 40
    topic_min_font_size = 20

    img = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(img)

    def load_font(name, size):
        path = os.path.join("fonts", name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
        else:
            print(f"[WARN] Font not found: {path}")
            return ImageFont.load_default()

    font_small = load_font("arial.ttf", 35)

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        line = ""
        for word in words:
            test_line = line + " " + word if line else word
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    # === Format date and time ===
    try:
        date_part, time_part = [x.strip() for x in meeting_time_date.split(',')]
        dt_date = datetime.strptime(date_part, "%m/%d/%Y")
        dt_time = datetime.strptime(time_part, "%I:%M:%S %p")
        formatted_date = dt_date.strftime("%d %B %Y")
        formatted_time = dt_time.strftime("%I:%M %p")
        meeting_time_date = f"{formatted_date}, {formatted_time}"
    except Exception as e:
        print(f"[Warning] Failed to format date/time: {e}")

    # === Fit topic ===
    for size in range(topic_max_font_size, topic_min_font_size - 1, -2):
        font_candidate = load_font("arialbd.ttf", size)
        wrapped_topic = wrap_text(meeting_topic, font_candidate, width - 2 * margin)
        total_height = sum([
            draw.textbbox((0, 0), line, font=font_candidate)[3] - draw.textbbox((0, 0), line, font=font_candidate)[1] + 15
            for line in wrapped_topic
        ])
        if total_height <= 200:
            topic_font = font_candidate
            break
    else:
        topic_font = font_small
        wrapped_topic = wrap_text(meeting_topic, topic_font, width - 2 * margin)

    # Compose lines
    lines = [{"text": "Next Meeting:", "font": font_small, "color": yellow}, {"gap": 40}]
    for line in wrapped_topic:
        lines.append({"text": line, "font": topic_font, "color": white, "topic": True})
    lines.append({"gap": 30})

    speaker_line = f"Speaker: {speaker_name}"
    if draw.textlength(speaker_line, font=font_small) > width - 2 * margin:
        for line in wrap_text(speaker_line, font_small, width - 2 * margin):
            lines.append({"text": line, "font": font_small, "color": red})
    else:
        lines.append({"text": speaker_line, "font": font_small, "color": red})

    lines.append({"gap": 30})
    lines.append({"text": meeting_time_date, "font": font_small, "color": green})

    # Vertical layout
    line_heights = []
    for item in lines:
        if "gap" in item:
            line_heights.append(item["gap"])
        else:
            h = draw.textbbox((0, 0), item["text"], font=item["font"])[3]
            if item.get("topic"):
                h += 15
            line_heights.append(h)

    total_text_height = sum(line_heights)
    current_y = (height - total_text_height) // 2

    for i, item in enumerate(lines):
        if "gap" in item:
            current_y += line_heights[i]
        else:
            text_width = draw.textlength(item["text"], font=item["font"])
            x = (width - text_width) // 2
            draw.text((x, current_y), item["text"], font=item["font"], fill=item["color"])
            current_y += line_heights[i]

    return img
