#!/usr/bin/env python3
import json
import bcrypt

# Load passwords
with open('reports/passwords.json', 'r') as f:
    data = json.load(f)

master_hash = data['master']['hash']
master_password = "MMVfV79L8Qh8Ps8C"

print(f"Testing master password: {master_password}")
print(f"Hash from file: {master_hash}")
print()

# Test verification
result = bcrypt.checkpw(master_password.encode('utf-8'), master_hash.encode('utf-8'))
print(f"Verification result: {result}")

if result:
    print("✓ Password verification successful!")
else:
    print("✗ Password verification failed!")
    print("\nRegenerating passwords to fix the issue...")
