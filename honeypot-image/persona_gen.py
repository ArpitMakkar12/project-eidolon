from faker import Faker
import random
import os

fake = Faker()

PERSONAS = [
    "HR-Workstation", "Dev-Database", "Finance-SMB",
    "IT-Admin-Box", "Prod-WebServer", "Backup-NAS",
    "DevOps-Jenkins", "Mail-Relay", "VPN-Gateway", "Git-Repo"
]

def generate_aws_key():
    import string
    key_id = "AKIA" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    secret = ''.join(random.choices(string.ascii_letters + string.digits + '/+', k=40))
    return key_id, secret

persona_type = random.choice(PERSONAS)
hostname     = f"{persona_type}-{fake.numerify('##')}"
user         = fake.user_name()
company      = fake.company()
email        = fake.company_email()
project      = fake.bs().replace(" ", "_")
db_ip        = fake.ipv4_private()
db_pass      = fake.password()
aws_id, aws_secret = generate_aws_key()
region       = random.choice(["us-east-1","us-west-2","eu-west-1","ap-southeast-1"])

# 1. Hostname
with open("/etc/hostname", "w") as f:
    f.write(hostname + "\n")

# 2. Fake user in /etc/passwd
with open("/etc/passwd", "a") as f:
    f.write(f"{user}:x:1001:1001:,,,:/home/{user}:/bin/bash\n")

# 3. Homepage
os.makedirs("/usr/share/nginx/html", exist_ok=True)
with open("/usr/share/nginx/html/index.html", "w") as f:
    f.write(f"""<!-- {company} Internal Portal -->
<!-- Project: {project} -->
<!-- Admin: {email} -->
<!-- Server: {hostname} ({db_ip}) -->
<html><body><h1>403 Forbidden</h1></body></html>""")

# 4. Config bait
with open("/usr/share/nginx/html/config.bak", "w") as f:
    f.write(f"""[database]
host = {db_ip}
port = 5432
name = {project}_db
user = {user}
password = {db_pass}

[smtp]
host = mail.{fake.domain_name()}
user = {email}
""")

# 5. AWS Honeytoken
os.makedirs("/root/.aws", exist_ok=True)
with open("/root/.aws/credentials", "w") as f:
    f.write(f"""[default]
aws_access_key_id = {aws_id}
aws_secret_access_key = {aws_secret}
region = {region}
""")

# 6. Fake SSH key
os.makedirs("/root/.ssh", exist_ok=True)
with open("/root/.ssh/id_rsa", "w") as f:
    f.write(f"""-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA{fake.md5()}{fake.md5()}{fake.md5()}
{fake.md5()}{fake.md5()}{fake.md5()}{fake.md5()}
-----END RSA PRIVATE KEY-----""")
os.chmod("/root/.ssh/id_rsa", 0o600)

print(f"[EIDOLON] Persona ready: {hostname} | {company} | {user}")
