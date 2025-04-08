
from flask import Flask
from threading import Thread
import time
import discord

app = Flask('')
start_time = time.time()

@app.route('/')
def home():
    uptime = time.time() - start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>GeoAdmin Bot Status</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #2c2f33;
                color: white;
                margin: 0;
                padding: 20px;
                text-align: center;
            }}
            .status-card {{
                background-color: #36393f;
                border-radius: 10px;
                padding: 20px;
                margin: 20px auto;
                max-width: 500px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            .title {{
                color: #7289da;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .status {{
                color: #43b581;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="status-card">
            <div class="title">GeoAdmin Bot Status</div>
            <p class="status">🟢 ONLINE</p>
            <p>Tiempo activo: {hours}h {minutes}m {seconds}s</p>
        </div>
        <script>
            setInterval(function() {{
                window.location.reload();
            }}, 5000);
        </script>
    </body>
    </html>
    '''

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
