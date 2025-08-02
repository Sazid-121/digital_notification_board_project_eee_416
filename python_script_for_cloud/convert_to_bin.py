from PIL import Image
import numpy as np

def quantize_rgb565(r, g, b):
    """Convert 8-bit RGB to 16-bit RGB565 format."""
    r_5 = (int(r) * 31) // 255
    g_6 = (int(g) * 63) // 255
    b_5 = (int(b) * 31) // 255
    return (r_5 << 11) | (g_6 << 5) | b_5

def save_image_as_bin(img: Image.Image, output_path="current_display.bin", width=640, height=480):
    """
    Converts a PIL image to RGB565 .bin format and saves to file.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")

    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img_np = np.array(img)

    with open(output_path, "wb") as f:
        for y in range(height):
            for x in range(width):
                r, g, b = img_np[y, x]
                rgb565 = quantize_rgb565(r, g, b)
                f.write(rgb565.to_bytes(2, byteorder='little'))

    print(f"[Info] Saved: {output_path} ({width}x{height}, {width * height * 2} bytes)")
