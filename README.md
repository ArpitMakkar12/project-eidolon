# Project Eidolon 🛡️
### AI-Powered Cyber Deception System — Automated Adaptive Minefield

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Docker](https://img.shields.io/badge/Docker-Swarm-blue)
![ELK](https://img.shields.io/badge/ELK-8.11.3-green)
![AI](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What is Project Eidolon?

In Greek mythology, an **Eidolon** is a phantom — something that looks completely real but isn't. Project Eidolon deploys **50 self-healing fake servers** that look exactly like real corporate machines. When attackers probe them, the system:

- 🎭 **Deceives** — AI generates unique convincing fake pages for every attacker
- 📊 **Logs** — Every attack captured in real-time via ELK Stack
- 🧠 **Classifies** — Automatically identifies attack type with confidence score
- 🌍 **Geolocates** — Maps attacker location and threat intelligence
- 🚨 **Alerts** — Instant notifications via Email, Telegram and Discord
- 🔨 **Blocks** — Auto-bans attacker IPs via Fail2Ban
- 👻 **Stealth** — eBPF makes each container appear as separate physical machine

---

## Architecture

**Attacker**
↓
**50 Honeypots (Docker Swarm)**
↓
**Groq Llama 3.3 70B** → Unique AI Response
↓
**Logstash** → Elasticsearch → Kibana Dashboard
↓
**Alert Engine** → Threat Intel → Attack Classification
↓
**Email + Telegram + Discord Alerts**
↓
**Fail2Ban** → IP Banned in Firewall

---

## Features

### 🤖 AI-Powered Deception
- **Groq Llama 3.3 70B** generates unique fake pages for every request
- No two honeypots ever show the same page
- Supports: WordPress admin, phpMyAdmin, .env files, AWS credentials, API endpoints

### 🎭 Active Deception Tarpit
- Accepts attacker credentials and serves fake WordPress dashboard
- Attacker browses fake posts, users, plugins pages
- Every action logged — credentials, navigation, time spent

### 🌍 Threat Intelligence
- **AbuseIPDB** integration — abuse score for every attacker IP
- **IPInfo** geolocation — country, city, organisation
- Tor exit node detection
- Known malicious IP identification

### 🧠 Attack Pattern Recognition
- Automatically classifies: WordPress Attack, Cloud Hunter, Credential Stuffer, Database Attack, API Scanner, Vulnerability Scanner, Reconnaissance
- Confidence scoring per classification
- Risk level assessment (CRITICAL/HIGH/MEDIUM/LOW)

### 👻 eBPF Network Stealth
- Each container gets unique TTL (64/128/255 — Linux/Windows/Cisco)
- Each container gets unique MAC address
- Network scanners see 50 different physical machines

### 📊 Real-Time Monitoring
- Kibana War Room dashboard
- Attack timeline, top targeted nodes, probed URLs
- Attacker IP table with threat scores

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Docker + Docker Swarm | 50 self-healing containers |
| Python 3.12 | Honeypot server + Alert engine |
| Groq API (Llama 3.3 70B) | AI response generation |
| Elasticsearch 8.11.3 | Attack data storage |
| Logstash 8.11.3 | Log processing pipeline |
| Kibana 8.11.3 | Visual dashboard |
| Fail2Ban | Automatic IP blocking |
| eBPF (bpftrace) | Network stealth |
| AbuseIPDB API | Threat intelligence |
| IPInfo API | Geolocation |
| Telegram Bot API | Mobile alerts |
| Discord Webhooks | Team alerts |
| Python Faker | Unique server identities |

---

## Quick Start

### Prerequisites
- Ubuntu 22.04+ with Docker installed
- Python 3.12+
- 8GB RAM minimum
- Groq API key (free at console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/ArpitMakkar12/project-eidolon.git
cd project-eidolon
```

### 2. Configure API keys
```bash
# Edit server.py
nano honeypot-image/server.py
# Set GROQ_API_KEY

# Edit eidolon_alert.py
nano eidolon_alert.py
# Set TELEGRAM_TOKEN, DISCORD_WEBHOOK, Gmail credentials
```

### 3. Start ELK Stack
```bash
docker compose -f elk-blueprint.yml up -d
sleep 90
```

### 4. Deploy Honeypots
```bash
docker swarm init
docker stack deploy -c swarm-blueprint.yml eidolon-stack
```

### 5. Start Alert Engine
```bash
sudo systemctl start eidolon-alert
```

### 6. Apply eBPF Stealth
```bash
python3 ebpf/ttl_stealth.py
```

### 7. Open Kibana Dashboard
```bash
http://localhost:5601
```

---

## Project Structure

```text
project-eidolon/
├── honeypot-image/
│   ├── Dockerfile
│   ├── server.py            # AI honeypot server with tarpit
│   ├── persona_gen.py       # Unique identity generator
│   └── entrypoint.sh        # Container startup
├── ebpf/
│   └── ttl_stealth.py       # eBPF network stealth engine
├── logstash/
│   └── logstash.conf        # Log processing pipeline
├── swarm-blueprint.yml      # 50 honeypot deployment
├── elk-blueprint.yml        # ELK stack deployment
├── eidolon_alert.py         # Alert engine (Email+Telegram+Discord)
├── threat_intel.py          # AbuseIPDB + IPInfo integration
├── attack_classifier.py     # Attack pattern recognition
└── README.md
```

## Demo

### Attack Detection
```text
[ALERT] 15 attacks from 1 new IPs!
[INTEL] 185.220.101.45 → Germany | Score: 100/100 | CRITICAL
[CLASSIFY] WORDPRESS_ATTACK | Risk: HIGH | Confidence: 100%
[FAIL2BAN] IP banned for 24 hours
[TELEGRAM] Alert sent
[DISCORD] Alert sent
[EMAIL] Alert sent
```

### eBPF Stealth

```text
Container 1 → TTL=64 (Linux)
Container 2 → TTL=128 (Windows)
Container 3 → TTL=255 (Cisco router)
50/50 unique MAC addresses applied
```
---

## Results

- **50** self-healing honeypots on a single laptop
- **< 2 seconds** AI response generation per request
- **60 seconds** maximum alert delivery time
- **100%** attack classification accuracy on test data
- **₹0** software licensing cost (100% open source)
```
---

## License
MIT License — Free to use, modify and distribute
```
---

## Author
**Arpit Makkar** | [GitHub](https://github.com/ArpitMakkar12)

*Built as part of cybersecurity research project — VIT-AP University, 2026*
