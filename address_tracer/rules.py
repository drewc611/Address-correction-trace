"""Correction rules and reference data for address standardization."""

# US state name to abbreviation mapping
STATE_ABBREVIATIONS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC",
}

# Valid two-letter state abbreviations (for validation)
VALID_STATE_ABBREVS = set(STATE_ABBREVIATIONS.values())

# Street suffix standardization (common abbreviations -> full USPS standard)
STREET_SUFFIXES = {
    "st": "Street", "st.": "Street", "str": "Street",
    "ave": "Avenue", "ave.": "Avenue", "av": "Avenue",
    "blvd": "Boulevard", "blvd.": "Boulevard",
    "dr": "Drive", "dr.": "Drive",
    "ln": "Lane", "ln.": "Lane",
    "rd": "Road", "rd.": "Road",
    "ct": "Court", "ct.": "Court",
    "cir": "Circle", "cir.": "Circle",
    "pl": "Place", "pl.": "Place",
    "pkwy": "Parkway", "pkwy.": "Parkway",
    "trl": "Trail", "trl.": "Trail",
    "way": "Way",
    "ter": "Terrace", "ter.": "Terrace",
    "hwy": "Highway", "hwy.": "Highway",
}

# Directional abbreviation expansion
DIRECTIONALS = {
    "n": "North", "n.": "North",
    "s": "South", "s.": "South",
    "e": "East", "e.": "East",
    "w": "West", "w.": "West",
    "ne": "Northeast", "ne.": "Northeast",
    "nw": "Northwest", "nw.": "Northwest",
    "se": "Southeast", "se.": "Southeast",
    "sw": "Southwest", "sw.": "Southwest",
}

# Secondary unit designators
UNIT_DESIGNATORS = {
    "apt": "Apartment", "apt.": "Apartment",
    "ste": "Suite", "ste.": "Suite",
    "unit": "Unit",
    "fl": "Floor", "fl.": "Floor",
    "rm": "Room", "rm.": "Room",
    "dept": "Department", "dept.": "Department",
    "bldg": "Building", "bldg.": "Building",
}
