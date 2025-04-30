# app.py
from flask import Flask, request, render_template, send_file
from fakegen import generate_fake_msg
import asyncio
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    user_id = request.form.get('user_id', 'Unknown User')
    message = request.form.get('message', 'Hello world!')
    color   = request.form.get('color', '1A1A1E')

    bg_rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/avatar.png"

    try:
        buf = asyncio.run(generate_fake_msg(
            username=user_id,
            avatar_url=avatar_url,
            message=message,
            bg_color=bg_rgb,
            custom_time=None,
            add_watermark=False
        ))
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return f"Failed to generate: {e}"
