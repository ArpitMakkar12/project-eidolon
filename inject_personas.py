from faker import Faker
import subprocess
import random

fake = Faker()

# Corporate persona types to make honeypots look like real servers
PERSONAS = [
    "HR-Workstation", "Dev-Database", "Finance-SMB",
    "IT-Admin-Box", "Prod-WebServer", "Backup-NAS",
    "DevOps-Jenkins", "Mail-Relay", "VPN-Gateway", "Git-Repo"
]

def inject_persona(container_name):
    persona_type = random.choice(PERSONAS)
    fake_hostname = f"{persona_type}-{fake.numerify('##')}"
    fake_user = fake.user_name()
    fake_password_hash = "$6$" + fake.md5()
    fake_project = fake.bs().replace(" ", "_")
    fake_ip = fake.ipv4_private()
    fake_email = fake.company_email()
    fake_company = fake.company()

    # 1. Set a unique hostname
    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', f'echo "{fake_hostname}" > /etc/hostname'], 
        capture_output=True)

    # 2. Inject a fake user into /etc/passwd
    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', f'echo "{fake_user}:x:1001:1001:,,,:/home/{fake_user}:/bin/bash" >> /etc/passwd'],
        capture_output=True)

    # 3. Create fake project files in web root
    fake_content = f"""<!-- {fake_company} Internal Portal -->
<!-- Project: {fake_project} -->
<!-- Admin: {fake_email} -->
<!-- Server: {fake_hostname} ({fake_ip}) -->
<html><body><h1>403 Forbidden</h1></body></html>"""

    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', f'echo \'{fake_content}\' > /usr/share/nginx/html/index.html'],
        capture_output=True)

    # 4. Plant a fake config file as bait
    fake_config = f"""[database]
host = {fake.ipv4_private()}
port = 5432
name = {fake_project}_db
user = {fake_user}
password = {fake.password()}

[smtp]
host = mail.{fake.domain_name()}
user = {fake_email}
"""
    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', f'echo \'{fake_config}\' > /usr/share/nginx/html/config.bak'],
        capture_output=True)

    print(f"✅ {container_name} → Persona: {fake_hostname} | User: {fake_user} | Company: {fake_company}")

# Get all decoy containers
result = subprocess.run(
    ['docker', 'ps', '--filter', 'name=eidolon-stack_web-farm-decoy', 
     '--format', '{{.Names}}'],
    capture_output=True, text=True
)

containers = result.stdout.strip().split('\n')
containers = [c for c in containers if c]

print(f"🎭 Injecting unique personas into {len(containers)} honeypot nodes...\n")

for container in containers:
    inject_persona(container)

print(f"\n🎯 Persona injection complete! All {len(containers)} nodes now have unique identities.")
