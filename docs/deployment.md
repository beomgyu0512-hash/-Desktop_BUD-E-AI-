# Deployment Guide

## Local network sharing

If other devices on your Wi-Fi cannot open Buddy after starting:

```sh
BUD_E_WEB_HOST=0.0.0.0 python web_app.py
```

check these points first:

- The other device must be on the same local network.
- Use your actual LAN IP, not `127.0.0.1`.
- On macOS, allow Python to accept incoming connections if the firewall prompts you.
- Some campus networks, company networks, VPNs, and guest Wi-Fi setups block device-to-device access even on the same IP range.

Useful commands on macOS:

```sh
ipconfig getifaddr en0
ipconfig getifaddr en1
```

Then try:

```text
http://YOUR_LAN_IP:8000
```

## Render deployment

This repository includes `render.yaml` for a simple Render web service deployment.

### What you need

- A GitHub repository containing this project
- A Render account
- Your Kimi and Deepgram API keys

### Steps

1. Push this repository to GitHub.
2. In Render, create a new Blueprint or Web Service from the repo.
3. If you use Blueprint mode, Render will read `render.yaml`.
4. Set these environment variables in Render:
   - `MOONSHOT_API_KEY`
   - `DEEPGRAM_API_KEY`
5. Deploy the service.
6. After the first successful deploy, open the generated Render URL.

### Start command

The service runs with:

```sh
gunicorn web_app:app --bind 0.0.0.0:$PORT
```

### Custom domain

After deployment, you can add your own domain inside the Render dashboard and point DNS records to Render.
