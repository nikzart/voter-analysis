#!/usr/bin/env python3
"""
Generate secure passwords for Kerala Election Insights Dashboard
- 1 master password for full access
- 56 ward-specific passwords for individual ward access
"""

import json
import secrets
import string
import bcrypt
from pathlib import Path


def generate_secure_password(length=12):
    """Generate a secure random password with letters, digits, and special chars"""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def load_ward_list():
    """Load ward names from polling_stations_map.json"""
    map_file = Path(__file__).parent.parent / 'polling_stations_map.json'
    with open(map_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    wards = []
    for ward in data['wards']:
        ward_text = ward['text']
        wards.append(ward_text)

    return wards


def main():
    print("Generating passwords for Kerala Election Insights Dashboard...")

    # Generate master password
    master_password = generate_secure_password(16)
    master_hash = hash_password(master_password)

    print(f"\nMaster Password: {master_password}")
    print("=" * 60)

    # Load wards
    wards = load_ward_list()
    print(f"\nGenerating passwords for {len(wards)} wards...")

    # Generate ward passwords
    ward_passwords = {}
    ward_passwords_plain = {}

    for ward_name in wards:
        password = generate_secure_password(12)
        hashed = hash_password(password)

        ward_passwords[ward_name] = {
            "hash": hashed
        }
        ward_passwords_plain[ward_name] = password

        print(f"  {ward_name}: {password}")

    # Create password data structure
    password_data = {
        "master": {
            "hash": master_hash
        },
        "wards": ward_passwords
    }

    # Create plain password data for distribution
    plain_password_data = {
        "master": master_password,
        "wards": ward_passwords_plain
    }

    # Save hashed passwords (for deployment)
    base_dir = Path(__file__).parent
    passwords_file = base_dir / 'reports' / 'passwords.json'
    with open(passwords_file, 'w', encoding='utf-8') as f:
        json.dump(password_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Hashed passwords saved to: {passwords_file}")

    # Save plain passwords (local only, for distribution)
    plain_file = base_dir / 'passwords_distribution.json'
    with open(plain_file, 'w', encoding='utf-8') as f:
        json.dump(plain_password_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Plain passwords saved to: {plain_file}")

    # Create text file for easy viewing
    txt_file = base_dir / 'passwords_distribution.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("KERALA ELECTION INSIGHTS - ACCESS CREDENTIALS\n")
        f.write("=" * 70 + "\n\n")
        f.write("MASTER PASSWORD (Full Access to All Wards)\n")
        f.write("-" * 70 + "\n")
        f.write(f"Password: {master_password}\n\n\n")
        f.write("WARD-SPECIFIC PASSWORDS\n")
        f.write("-" * 70 + "\n\n")

        for ward_name in sorted(wards):
            f.write(f"{ward_name}\n")
            f.write(f"  Password: {ward_passwords_plain[ward_name]}\n\n")

    print(f"✓ Text file saved to: {txt_file}")

    print("\n" + "=" * 60)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 60)
    print(f"1. passwords_distribution.json and passwords_distribution.txt contain")
    print(f"   PLAIN TEXT passwords - keep these files SECURE and LOCAL ONLY")
    print(f"2. Only reports/passwords.json should be deployed (contains hashes only)")
    print(f"3. Add passwords_distribution.* to .gitignore")
    print("=" * 60)


if __name__ == "__main__":
    main()
