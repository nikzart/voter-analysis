#!/usr/bin/env python3
"""
Generate secure passwords for Kerala Election Insights Dashboard using SHA-256
Compatible with both Python and JavaScript
"""

import json
import secrets
import string
import hashlib
from pathlib import Path


def generate_secure_password(length=12):
    """Generate a secure random password with letters and digits"""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def hash_password_sha256(password):
    """Hash password using SHA-256 (works in both Python and JS)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


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
    print("Generating passwords with SHA-256 hashing...")

    # Generate master password
    master_password = generate_secure_password(16)
    master_hash = hash_password_sha256(master_password)

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
        hashed = hash_password_sha256(password)

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
    print(f"1. Using SHA-256 hashing (browser-compatible)")
    print(f"2. passwords_distribution.* files contain plain text passwords")
    print(f"3. Keep these files SECURE and LOCAL ONLY")
    print(f"4. Only reports/passwords.json should be deployed")
    print("=" * 60)


if __name__ == "__main__":
    main()
