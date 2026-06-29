from validator import fix_date, apply_known_fixes


def autofix(data: dict, errors: list) -> dict:
    """
    Apply all fixes from explained errors back to the resource
    """
    fixed = data.copy()

    for error in errors:
        field = error.get("field")
        fix = error.get("fix")

        if not fix or not field:
            continue

        # Handle nested fields like "name → 0 → family"
        if "→" in field:
            parts = [p.strip() for p in field.split("→")]
            apply_nested_fix(fixed, parts, fix)
        else:
            fixed[field] = fix

    # Final cleanup pass with known rules
    fixed = apply_known_fixes(fixed)

    return fixed


def apply_nested_fix(data: dict, parts: list, fix):
    """Apply fix to nested field"""
    try:
        ref = data
        for part in parts[:-1]:
            if part.isdigit():
                ref = ref[int(part)]
            else:
                ref = ref[part]
        last = parts[-1]
        if last.isdigit():
            ref[int(last)] = fix
        else:
            ref[last] = fix
    except (KeyError, IndexError, TypeError):
        pass


def generate_fix_summary(original: dict, fixed: dict, errors: list) -> dict:
    """Generate a human readable summary of what was fixed"""
    changes = []

    for error in errors:
        field = error.get("field")
        fix = error.get("fix")
        received = error.get("received")

        if fix and received and fix != received:
            changes.append({
                "field": field,
                "from": received,
                "to": fix,
                "explanation": error.get("explanation", "")
            })

    return {
        "total_fixes_applied": len(changes),
        "changes": changes,
        "fixed_resource": fixed
    }