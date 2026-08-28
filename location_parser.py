# location_parser.py
"""Single source of truth for area and block. Imported by clean_data.py and main.py."""
import re



def normalise(s):
    if not isinstance(s, str):
        return None
    s = re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()
    return s or None


def split_location(location_text):
    """('DHA Phase 6 - Block C, DHA Phase 6, ...') -> ('DHA Phase 6', 'Block C')
       ('Johar Town, Lahore, Punjab')              -> ('Johar Town', None)"""
    s = normalise(location_text)
    if not s:
        return ("Other", None)
    first = s.split(",")[0].strip()
    parts = first.split(" - ")
    area = parts[0].strip()
    if len(parts) == 1:
        return (area or "Other", None)
    block = " - ".join(parts[1:]).strip()
    return (area or "Other", block or None)


def extract_area(location_text):
    return split_location(location_text)[0]


def extract_block(location_text):
    return split_location(location_text)[1]