

from flask import Flask, request, render_template, send_file
from fakegen import generate_fake_msg
import asyncio
import aiohttp
import io

app = Flask(__name__)

# 🔐 Paste your Discord Bot Token here
DISCORD_BOT_TOKEN = "MTM2NzAxNTQwNDI1NzU0NjI1MA.G7cJMS.uHiUBxBeIsZpE7ob2mZByB07CXNnLDA8fsrJVk"

async def fetch_user_data(user_id):
    url = f"https://discord.com/api/v10/users/{user_id}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    user_id = request.form.get('user_id', 'Unknown User')
    message = request.form.get('message', 'Hello world!')
    color   = request.form.get('color', '1A1A1E')

    bg_rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

    async def process():
        user_data = await fetch_user_data(user_id)
        if not user_data:
            username = f"ID:{user_id}"
            avatar_url = f"https://cdn.discordapp.com/embed/avatars/{int(user_id) % 5}.png"
        else:
            username = user_data['username']
            discriminator = user_data.get('discriminator')
            if discriminator and discriminator != "0":
                username += f"#{discriminator}"
            avatar_hash = user_data.get('avatar')
            if avatar_hash:
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
            else:
                avatar_url = f"https://cdn.discordapp.com/embed/avatars/{int(user_id) % 5}.png"

        return await generate_fake_msg(
            username=username,
            avatar_url=avatar_url,
            message=message,
            bg_color=bg_rgb,
            custom_time=None,
            add_watermark=False
        )

    try:
        buf = asyncio.run(process())
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return f"Failed to generate: {e}"

