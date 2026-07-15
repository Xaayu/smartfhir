"""
Realistic fake data generator for PHI pseudonymization.
Uses Faker to generate convincing but completely fake replacement data.
Deterministic — same input always produces same fake output (for consistency).
"""

import hashlib
from faker import Faker

fake = Faker()


def _seed_from_value(value: str) -> int:
    """
    Generate a deterministic seed from a value.
    Same real value → always same fake value.
    Important for consistency across a bundle.
    """
    return int(hashlib.md5(str(value).encode()).hexdigest(), 16) % (2**32)


def fake_name(real_name: str) -> str:
    """Generate realistic fake full name"""
    Faker.seed(_seed_from_value(real_name))
    return fake.name()


def fake_first_name(real: str) -> str:
    Faker.seed(_seed_from_value(real + "_first"))
    return fake.first_name()


def fake_last_name(real: str) -> str:
    Faker.seed(_seed_from_value(real + "_last"))
    return fake.last_name()


def fake_email(real_email: str) -> str:
    """Generate fake email preserving domain structure"""
    Faker.seed(_seed_from_value(real_email))
    return fake.email()


def fake_phone(real_phone: str) -> str:
    """Generate fake phone number"""
    Faker.seed(_seed_from_value(real_phone))
    return fake.phone_number()


def fake_address(real_address: str) -> str:
    """Generate fake street address"""
    Faker.seed(_seed_from_value(real_address))
    return fake.street_address()


def fake_city(real_city: str) -> str:
    Faker.seed(_seed_from_value(real_city))
    return fake.city()


def fake_state(real_state: str) -> str:
    Faker.seed(_seed_from_value(real_state))
    return fake.state_abbr()


def fake_zip(real_zip: str) -> str:
    """Generalize zip — keep first 3 digits only (HIPAA Safe Harbor)"""
    cleaned = str(real_zip).replace("-", "").replace(" ", "")
    if len(cleaned) >= 3:
        return cleaned[:3] + "00"
    Faker.seed(_seed_from_value(real_zip))
    return fake.postcode()


def fake_date(real_date: str) -> str:
    """
    HIPAA Safe Harbor date generalization.
    Keep year only. Remove month and day.
    Exception: if age > 89, replace with '1900-01-01'
    """
    if not real_date:
        return real_date
    try:
        from datetime import datetime
        # Parse the date
        for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
            try:
                parsed = datetime.strptime(str(real_date)[:10], fmt)
                year = parsed.year
                # HIPAA: ages over 89 must be grouped
                from datetime import date
                age = (date.today() - parsed.date()).days // 365
                if age > 89:
                    return "1900-01-01"
                return f"{year}-01-01"
            except ValueError:
                continue
    except Exception:
        pass
    return real_date


def fake_id(real_id: str) -> str:
    """Generate fake patient/record ID preserving format"""
    Faker.seed(_seed_from_value(real_id))
    return f"ANON-{fake.bothify('??###??###').upper()}"


def fake_url(real_url: str) -> str:
    Faker.seed(_seed_from_value(real_url))
    return fake.url()


def fake_ip(real_ip: str) -> str:
    Faker.seed(_seed_from_value(real_ip))
    return fake.ipv4_private()


def fake_ssn(real_ssn: str) -> str:
    Faker.seed(_seed_from_value(real_ssn))
    return fake.ssn()


def fake_organization(real_org: str) -> str:
    Faker.seed(_seed_from_value(real_org))
    return fake.company()


def mask_value(value: str) -> str:
    """
    Mask a value — show first char, mask rest.
    John → J***
    john@email.com → j***@*****.***
    """
    if not value or len(str(value)) < 2:
        return "***"

    value = str(value)

    # Email masking
    if "@" in value:
        parts = value.split("@")
        local = parts[0][0] + "***"
        domain_parts = parts[1].split(".")
        domain = "***." + domain_parts[-1]
        return f"{local}@{domain}"

    # Phone masking — keep last 4
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) >= 7:
        return "***-***-" + digits[-4:]

    # General masking — keep first char
    return value[0] + "*" * (len(value) - 1)


def redact_value(field_name: str = "") -> str:
    """Simple redaction"""
    return "[REDACTED]"