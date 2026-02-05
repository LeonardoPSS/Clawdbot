# 🌊 DigitalOcean Deployment Guide - Nexara

## Quick Start (5 minutes)

### Step 1: Create Droplet
1. Login to [DigitalOcean](https://cloud.digitalocean.com)
2. Click **Create** → **Droplets**
3. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($6/mo - 1GB RAM, 1 CPU)
   - **Datacenter**: Choose closest to you
   - **Authentication**: SSH Key (recommended) or Password
4. Click **Create Droplet**
5. Note the IP address

### Step 2: Connect via SSH
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Install Docker
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y
```

### Step 4: Upload Bot Code
From your local machine (Windows PowerShell):
```powershell
# Compress the bot folder
Compress-Archive -Path "C:\Users\leona\Downloads\AntigravityJobBot" -DestinationPath "C:\Users\leona\Downloads\nexara.zip"

# Upload to server (replace YOUR_DROPLET_IP)
scp "C:\Users\leona\Downloads\nexara.zip" root@YOUR_DROPLET_IP:/root/
```

Back on the server:
```bash
# Extract
cd /root
apt install unzip -y
unzip nexara.zip
cd AntigravityJobBot
```

### Step 5: Configure Secrets
Create environment file:
```bash
cd deployment
nano .env
```

Add your secrets (paste these values):
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
OPENAI_API_KEY=your_openai_api_key
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Launch 🚀
```bash
docker-compose up -d --build
```

This will:
- Build the Docker image (~3-5 minutes)
- Install all dependencies
- Start Nexara in the background

### Step 7: Verify
Check logs:
```bash
docker logs -f clawdbot_vps
```

You should see:
- `INFO:AntigravityMaster:Starting Antigravity Job Bot 🚀`
- `INFO:src.telegram_bot:Telegram Chatbot started`
- `INFO:src.desktop_automation:Autonomous Loop Started`

Press `Ctrl+C` to exit logs (bot keeps running).

---

## Management Commands

```bash
# View logs
docker logs -f clawdbot_vps

# Restart bot
docker-compose restart

# Stop bot
docker-compose down

# Update bot code
git pull  # if using git
docker-compose up -d --build

# Check if running
docker ps
```

---

## Cloud Mode Features

### ✅ What Works
- Telegram bot (all commands)
- Autonomous learning (AI-based, no browser)
- Knowledge accumulation
- Entrepreneur mode
- **Self-Evolution (God Mode)**: Can write new skills and update itself
- 24/7 uptime

### ❌ What's Disabled
- Desktop automation (`/pc` commands)
- Browser-based learning
- Screenshots
- LinkedIn automation (already disabled)
- Room Control (IoT - unless you setup VPN for OpenRGB)

---

## Troubleshooting

### Bot not responding to Telegram
```bash
# Check if container is running
docker ps

# Check logs for errors
docker logs clawdbot_vps

# Verify environment variables
docker exec clawdbot_vps env | grep TELEGRAM
```

### Out of memory
Upgrade to $12/mo droplet (2GB RAM):
```bash
# From DigitalOcean dashboard: Resize droplet
```

### Update secrets
```bash
cd /root/AntigravityJobBot/deployment
nano .env
# Make changes
docker-compose down
docker-compose up -d
```

---

## Cost Optimization

**Current**: $6/month
- Basic Droplet: $6/mo

**If you need more power**:
- Regular Droplet (2GB): $12/mo
- CPU-Optimized: $24/mo

**Free alternative**: Use AWS Free Tier (12 months free)

---

## Next Steps

1. ✅ Deploy to DigitalOcean
2. Monitor for 24 hours
3. Check `data/autonomous_knowledge.md` for learning entries
4. Enjoy 24/7 autonomous Nexara! 🎉
