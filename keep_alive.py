"""
keep_alive.py — Add this file to your repo root.
Handles 24/7 uptime on Koyeb by self-pinging + proper health endpoint.
Does NOT modify any main bot code.

USAGE: Import and call start_keep_alive() anywhere in your bot startup,
       OR just run:  python3 -m keep_alive  (standalone)
"""

import asyncio
import os
import time
import logging
import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)

# ─── Config (reads from your existing env vars) ───────────────────────────────
FQDN       = os.environ.get("FQDN", "")
PORT       = int(os.environ.get("PORT", 8080))
PING_INTERVAL = int(os.environ.get("PING_INTERVAL", 240))   # seconds (4 min)
BOT_NAME   = os.environ.get("BOT_NAME", "File-To-Link Bot")

# ─── Uptime tracker ───────────────────────────────────────────────────────────
START_TIME = time.time()

def get_uptime() -> str:
    seconds = int(time.time() - START_TIME)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days:  parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if mins:  parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)

# ─── Self-Ping Task ───────────────────────────────────────────────────────────
async def self_ping_task():
    """Pings the bot's own health endpoint every PING_INTERVAL seconds."""
    if not FQDN:
        logger.warning("⚠️  FQDN not set — self-ping disabled. Set FQDN env var!")
        return

    # Auto-detect URL scheme
    url = FQDN if FQDN.startswith("http") else f"https://{FQDN}"
    ping_url = f"{url}/health"

    logger.info(f"🔁 Self-ping started → {ping_url} every {PING_INTERVAL}s")

    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            try:
                async with session.get(ping_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        logger.debug(f"✅ Self-ping OK ({resp.status})")
                    else:
                        logger.warning(f"⚠️  Self-ping returned {resp.status}")
            except Exception as e:
                logger.warning(f"⚠️  Self-ping failed: {e}")

# ─── Health Endpoint (/health) ────────────────────────────────────────────────
async def health_handler(request: web.Request) -> web.Response:
    """
    Koyeb health check endpoint.
    Returns 200 JSON so Koyeb knows the service is alive.
    """
    return web.json_response({
        "status": "ok",
        "uptime": get_uptime(),
        "bot": BOT_NAME,
    })

# ─── Status Dashboard (/status) ───────────────────────────────────────────────
async def status_handler(request: web.Request) -> web.Response:
    """
    A human-readable HTML status page.
    Visit: https://your-koyeb-url.koyeb.app/status
    """
    import psutil, platform
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <meta http-equiv="refresh" content="30"/>
  <title>{BOT_NAME} — Status</title>
  <style>
    :root {{
      --bg: #0f0f17; --card: #1a1a2e; --accent: #7c3aed;
      --green: #22c55e; --yellow: #eab308; --red: #ef4444;
      --text: #e2e8f0; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg); color: var(--text);
      font-family: 'Segoe UI', system-ui, sans-serif;
      min-height: 100vh; padding: 2rem 1rem;
    }}
    .container {{ max-width: 700px; margin: 0 auto; }}
    h1 {{
      font-size: 1.8rem; font-weight: 700; margin-bottom: 0.3rem;
      background: linear-gradient(135deg, #7c3aed, #06b6d4);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .subtitle {{ color: var(--muted); margin-bottom: 2rem; font-size: 0.9rem; }}
    .badge {{
      display: inline-block; padding: 0.25rem 0.75rem;
      border-radius: 999px; font-size: 0.8rem; font-weight: 600;
      background: #16a34a22; color: var(--green);
      border: 1px solid var(--green); margin-bottom: 2rem;
    }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); }}
    .card {{
      background: var(--card); border-radius: 12px; padding: 1.2rem;
      border: 1px solid #ffffff12;
    }}
    .card-label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
    .card-value {{ font-size: 1.6rem; font-weight: 700; margin-top: 0.3rem; }}
    .bar-wrap {{ background: #ffffff15; border-radius: 999px; height: 6px; margin-top: 0.6rem; }}
    .bar {{ height: 6px; border-radius: 999px; transition: width 0.3s; }}
    .bar.green {{ background: var(--green); }}
    .bar.yellow {{ background: var(--yellow); }}
    .bar.red {{ background: var(--red); }}
    footer {{ text-align: center; margin-top: 2.5rem; color: var(--muted); font-size: 0.8rem; }}
    footer a {{ color: var(--accent); text-decoration: none; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 {BOT_NAME}</h1>
    <p class="subtitle">Real-time status · Auto-refreshes every 30 seconds</p>
    <span class="badge">● ONLINE</span>

    <div class="grid">
      <div class="card">
        <div class="card-label">⏱ Uptime</div>
        <div class="card-value" style="font-size:1.2rem">{get_uptime()}</div>
      </div>

      <div class="card">
        <div class="card-label">🖥 CPU Usage</div>
        <div class="card-value" style="color:{'var(--green)' if cpu < 70 else 'var(--red)'}">{cpu:.1f}%</div>
        <div class="bar-wrap">
          <div class="bar {'green' if cpu < 70 else 'red'}" style="width:{min(cpu,100):.0f}%"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-label">💾 RAM Usage</div>
        <div class="card-value" style="color:{'var(--green)' if ram.percent < 80 else 'var(--red)'}">{ram.percent:.1f}%</div>
        <div class="bar-wrap">
          <div class="bar {'green' if ram.percent < 80 else 'red'}" style="width:{ram.percent:.0f}%"></div>
        </div>
        <div style="color:var(--muted);font-size:0.75rem;margin-top:0.4rem">
          {ram.used // 1024**2} MB / {ram.total // 1024**2} MB
        </div>
      </div>

      <div class="card">
        <div class="card-label">💿 Disk Usage</div>
        <div class="card-value">{disk.percent:.1f}%</div>
        <div class="bar-wrap">
          <div class="bar {'green' if disk.percent < 80 else 'yellow'}" style="width:{disk.percent:.0f}%"></div>
        </div>
        <div style="color:var(--muted);font-size:0.75rem;margin-top:0.4rem">
          {disk.used // 1024**3} GB / {disk.total // 1024**3} GB
        </div>
      </div>

      <div class="card">
        <div class="card-label">🐍 Python</div>
        <div class="card-value" style="font-size:1rem">{platform.python_version()}</div>
      </div>

      <div class="card">
        <div class="card-label">🖧 Platform</div>
        <div class="card-value" style="font-size:0.95rem">{platform.system()} {platform.machine()}</div>
      </div>
    </div>

    <footer>
      <p>Powered by <a href="https://koyeb.com">Koyeb</a> · Keep-alive by keep_alive.py</p>
    </footer>
  </div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")

# ─── Public API ───────────────────────────────────────────────────────────────
def register_routes(app: web.Application):
    """
    Call this with your existing aiohttp app to add /health and /status routes.
    Example (in your bot startup):
        from keep_alive import register_routes
        register_routes(app)
    """
    app.router.add_get("/health", health_handler)
    app.router.add_get("/status", status_handler)
    logger.info("✅ keep_alive routes registered: /health  /status")

async def start_keep_alive(app: web.Application = None, loop=None):
    """
    Full start: registers routes + starts self-ping background task.
    Call once during bot startup:
        asyncio.get_event_loop().create_task(start_keep_alive(app))
    """
    if app:
        register_routes(app)
    asyncio.ensure_future(self_ping_task())
    logger.info("🔁 keep_alive started successfully")

# ─── Standalone run (optional) ────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = web.Application()
    register_routes(app)

    async def main():
        asyncio.ensure_future(self_ping_task())
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        logger.info(f"🌐 keep_alive server running on port {PORT}")
        await asyncio.sleep(3600 * 24 * 365)  # Run forever

    asyncio.run(main())
