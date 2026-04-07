import json
import requests
import time

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OUTPUT_FILE = "/ai-cache/responses.json"

PROMPTS = {
    "/wp-admin": [
        "Generate a fake but convincing HTML WordPress admin login page. Include fake version number WP 6.4.2. Return only raw HTML.",
        "Generate a different fake HTML WordPress admin login page with a security warning banner. Return only raw HTML.",
        "Generate a fake HTML WordPress multisite admin login page. Return only raw HTML.",
    ],
    "/config.php": [
        "Generate a fake PHP config file with MySQL credentials, API keys and debug settings. Return only file contents.",
        "Generate a fake PHP config file for an e-commerce site with payment gateway keys. Return only file contents.",
    ],
    "/.git/config": [
        "Generate a fake .git/config with GitHub remote URLs and user settings for a company called TechCorp. Return only file contents.",
        "Generate a fake .git/config with GitLab remote URLs for a financial company. Return only file contents.",
    ],
    "/.env": [
        "Generate a fake .env file with AWS keys, database URL, Redis URL, Stripe keys and JWT secret. Return only file contents.",
        "Generate a fake .env file for a Node.js app with MongoDB, SendGrid and Twilio credentials. Return only file contents.",
    ],
    "/api/v1/users": [
        "Generate a fake JSON API response with 5 corporate user accounts with names, emails, roles and last_login. Return only valid JSON.",
        "Generate a fake JSON API response with 4 admin users including hashed passwords and API tokens. Return only valid JSON.",
    ],
    "/admin": [
        "Generate a fake HTML admin dashboard login page for a company called GlobalTech Systems. Return only raw HTML.",
        "Generate a fake HTML admin panel login for a financial services company. Return only raw HTML.",
    ],
    "/phpmyadmin": [
        "Generate a fake HTML phpMyAdmin 5.2.1 login page. Return only raw HTML.",
    ],
    "/.aws/credentials": [
        "Generate a fake AWS credentials file with multiple profiles and fake access keys. Return only file contents.",
    ],
}

def ask_mistral(prompt):
    try:
        r = requests.post(OLLAMA_URL,
            json={"model": "mistral", "prompt": prompt, "stream": False},
            timeout=None)
        return r.json().get("response", "")
    except Exception as e:
        print(f"Error: {e}")
        return None

cache = {}
total = sum(len(v) for v in PROMPTS.values())
count = 0

print(f"Starting AI response generation: {total} responses to generate...")
print("This will take approximately", total * 4, "minutes on CPU.")
print("Go grab a coffee! ☕")

for path, prompts in PROMPTS.items():
    cache[path] = []
    for i, prompt in enumerate(prompts):
        count += 1
        print(f"[{count}/{total}] Generating {path} variant {i+1}...")
        start = time.time()
        response = ask_mistral(prompt)
        elapsed = round(time.time() - start, 1)
        if response:
            cache[path].append(response)
            print(f"✅ Done in {elapsed}s ({len(response)} chars)")
        else:
            print(f"⚠️ Failed, skipping")

with open(OUTPUT_FILE, "w") as f:
    json.dump(cache, f)

print(f"\n🎯 All responses saved to {OUTPUT_FILE}")
print(f"Total paths cached: {len(cache)}")
for path, responses in cache.items():
    print(f"  {path}: {len(responses)} variants")
