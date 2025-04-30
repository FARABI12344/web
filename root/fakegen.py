from PIL import Image, ImageDraw, ImageFont, ImageOps
import aiohttp
import io
from datetime import datetime
import pytz
import os

async def generate_fake_msg(username, avatar_url, message, bg_color=(26,26,30), custom_time=None, add_watermark=False):
    width, height    = 700, 130
    avatar_size      = 56
    padding          = 20
    text_start_x     = avatar_size + padding*2
    max_text_width   = width - text_start_x - padding

    def is_dark(rgb):
        r,g,b = rgb
        return (r*0.299 + g*0.587 + b*0.114) < 186

    dark_bg = is_dark(bg_color)
    username_color = (255,255,255) if dark_bg else (0,0,0)
    message_color  = (220,221,222) if dark_bg else (50,50,50)
    timestamp_color= (153,170,181) if dark_bg else (100,100,100)
    poke_color     = (255,255,255) if dark_bg else (0,0,0)
    poke_opacity   = 100 if add_watermark else 0

    timestamp = custom_time or datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%-I:%M %p")

    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    def load_font(path, size):
        try:
            return ImageFont.truetype(os.path.join(font_dir, path), size)
        except Exception:
            return ImageFont.load_default()

    name_font      = load_font("gg sans Bold.ttf",   22)
    msg_font       = load_font("gg sans Regular.ttf",20)
    timestamp_font = load_font("gg sans Regular.ttf",16)
    poke_font      = load_font("gg sans Bold.ttf",   14)
    site_font      = load_font("gg sans Bold.ttf",   16)

    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            avatar_bytes = await resp.read()

    orig = Image.open(io.BytesIO(avatar_bytes)).convert("RGB")
    avatar = ImageOps.fit(orig, (avatar_size, avatar_size), centering=(0.5,0.5), resample=Image.LANCZOS).convert("RGBA")

    mask = Image.new("L", (avatar_size*3, avatar_size*3), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((0, 0, avatar_size*3, avatar_size*3), fill=255)
    mask = mask.resize((avatar_size, avatar_size), resample=Image.LANCZOS)
    avatar.putalpha(mask)

    if add_watermark:
        overlay = Image.new("RGBA", avatar.size, (0,0,0,0))
        odraw   = ImageDraw.Draw(overlay)
        text    = "POKIS"
        bbox    = odraw.textbbox((0,0), text, font=poke_font)
        pw = bbox[2] - bbox[0]; ph = bbox[3] - bbox[1]
        odraw.text(((avatar_size-pw)/2, (avatar_size-ph)/2), text, font=poke_font, fill=(*poke_color, poke_opacity))
        avatar = Image.alpha_composite(avatar, overlay)

    def wrap_text(draw, text, font, max_width):
        wrapped = []
        for line in text.splitlines():
            words = line.split()
            current = ""
            for word in words:
                test_line = f"{current} {word}".strip()
                if draw.textlength(test_line, font=font) <= max_width:
                    current = test_line
                else:
                    wrapped.append(current)
                    current = word
            wrapped.append(current)
        return wrapped

    dummy_img = Image.new("RGB", (width, 1000))
    dummy_draw = ImageDraw.Draw(dummy_img)
    wrapped_lines = wrap_text(dummy_draw, message, msg_font, max_text_width)
    line_h = msg_font.getbbox("Ay")[3] + 4
    total_text_height = line_h * len(wrapped_lines)
    final_height = max(height, padding + 30 + total_text_height + padding)

    img  = Image.new("RGB", (width, final_height), bg_color)
    draw = ImageDraw.Draw(img)
    img.paste(avatar, (padding, padding), avatar)

    draw.text((text_start_x, padding), username, font=name_font, fill=username_color)
    nw = draw.textlength(username, font=name_font)
    draw.text((text_start_x + nw + 8, padding + 3), timestamp, font=timestamp_font, fill=timestamp_color)

    for i, line in enumerate(wrapped_lines):
        try:
            draw.text((text_start_x, padding + 30 + i*line_h), line, font=msg_font, fill=message_color)
        except Exception:
            draw.text((text_start_x, padding + 30 + i*line_h), line, font=ImageFont.load_default(), fill=message_color)

    if add_watermark:
        site = "pokis.xyz"
        bbox = draw.textbbox((0,0), site, font=site_font)
        sw = bbox[2] - bbox[0]
        draw.text(((width-sw)/2, final_height-25), site, font=site_font, fill=poke_color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
