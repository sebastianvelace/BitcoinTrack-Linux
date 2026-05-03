# BitcoinTrack-Linux

A lightweight, always-on-top Bitcoin price ticker for Linux desktops.  
Displays real-time BTC/USDT price and 24h change from Binance — with zero chrome.

![demo gif here]

## Features
- Live BTC price via Binance public API (no API key needed)
- 24h percentage change with color coding (green/red)
- Frameless, transparent window — sits on top of everything
- X11 and Wayland compatible
- Auto-retry on connection loss (every 5s)
- Updates every 60 seconds

## Requirements
- Linux (X11 or Wayland)
- Python 3.10+

## Installation
git clone https://github.com/sebastianvelace/BitcoinTrack-Linux
cd BitcoinTrack-Linux
pip install -r requirements.txt
python main.py

## Run on startup
Add to your window manager autostart or create a systemd user service.
