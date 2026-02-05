# ☁️ Clawdbot Cloud Deployment Guide

This guide explains how to run Clawdbot 24/7 on a VPS (Virtual Private Server).

## 1. Rent a Cheap Server (VPS)
You can use any provider. Recommended for cost ($4-6/mo):
- **DigitalOcean** (Basic Droplet)
- **Hetzner Cloud** (CPX11)
- **AWS Lightsail**

**OS Requirement**: Ubuntu 22.04 LTS (or higher).

## 2. Install Docker
Connect to your server via SSH and run:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y
```

## 3. Upload the Bot
You can use `scp` or FileZilla to upload the `AntigravityJobBot` folder to the server.
```bash
scp -r "C:\Users\leona\Downloads\AntigravityJobBot" root@<YOUR_SERVER_IP>:/root/bot
```

## 4. Configure Secrets
Create a `.env` file inside the `deployment` folder on the server:
```bash
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_id_here
OPENAI_API_KEY=your_key_here
```

## 5. Launch 🚀
Navigate to the deployment folder and fire it up:
```bash
cd /root/bot/deployment
docker-compose up -d --build
```

The bot will build, install everything, and start running in the background.

## Commands
- **Check logs**: `docker logs -f clawdbot_vps`
- **Stop bot**: `docker-compose down`
- **Restart**: `docker-compose restart`

## ⚠️ Notes
- **Desktop Control**: Since there is no screen, `/pc` commands (mouse/keyboard) are disabled.
- **Visuals**: Browser automation will run in `headless` mode (invisible).
