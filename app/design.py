import re


FONT_FAMILIES = {
    "system": "Arial, sans-serif",
    "arial": "Arial, sans-serif",
    "verdana": "Verdana, sans-serif",
    "georgia": "Georgia, serif",
    "trebuchet": "Trebuchet MS, sans-serif",
}

SECTION_DEFAULTS = (
    {"key": "search", "label": "Product search", "visible": True, "order": 1},
    {"key": "hero", "label": "Hero banner", "visible": True, "order": 2},
    {"key": "categories", "label": "Categories", "visible": True, "order": 3},
    {"key": "featured", "label": "Featured products", "visible": True, "order": 4},
    {"key": "new_arrivals", "label": "New arrivals", "visible": True, "order": 5},
    {"key": "promotion", "label": "Installment promotion", "visible": True, "order": 6},
    {"key": "newsletter", "label": "Email updates signup", "visible": True, "order": 7},
)

DEFAULT_DESIGN_SETTINGS = {
    "primary_color": "#17385e",
    "accent_color": "#168bff",
    "background_color": "#f6f7f9",
    "surface_color": "#ffffff",
    "text_color": "#101d31",
    "muted_color": "#748093",
    "border_color": "#e7ebf0",
    "font_family": "system",
    "button_radius": 10,
    "card_radius": 14,
    "section_spacing": 56,
    "hero_title": "",
    "hero_subtitle": "Shop TVs, speakers, phones and more, with trusted advice and flexible installment options.",
    "hero_button_text": "Shop",
    "hero_image": "",
    "homepage_sections": [
        {
            "key": section["key"],
            "label": section["label"],
            "visible": section["visible"],
            "order": section["order"],
        }
        for section in SECTION_DEFAULTS
    ],
}

_COLOR_FIELDS = (
    "primary_color",
    "accent_color",
    "background_color",
    "surface_color",
    "text_color",
    "muted_color",
    "border_color",
)
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def normalize_design_settings(settings):
    source = settings if isinstance(settings, dict) else {}
    result = dict(DEFAULT_DESIGN_SETTINGS)

    for field in _COLOR_FIELDS:
        value = source.get(field, result[field])
        result[field] = value if isinstance(value, str) and _HEX_COLOR.fullmatch(value) else result[field]

    font_family = source.get("font_family")
    if isinstance(font_family, str) and font_family in FONT_FAMILIES:
        result["font_family"] = font_family

    for field, lower, upper in (
        ("button_radius", 0, 32),
        ("card_radius", 0, 40),
        ("section_spacing", 24, 128),
    ):
        value = source.get(field)
        if isinstance(value, int) and lower <= value <= upper:
            result[field] = value

    for field, limit in (
        ("hero_title", 100),
        ("hero_subtitle", 240),
        ("hero_button_text", 40),
    ):
        value = source.get(field)
        if isinstance(value, str):
            result[field] = value.strip()[:limit]

    hero_image = source.get("hero_image")
    if isinstance(hero_image, str):
        result["hero_image"] = hero_image

    sections = source.get("homepage_sections")
    if isinstance(sections, list):
        normalized_sections = []
        for default in SECTION_DEFAULTS:
            saved = next(
                (
                    section
                    for section in sections
                    if isinstance(section, dict) and section.get("key") == default["key"]
                ),
                {},
            )
            order = saved.get("order", default["order"])
            visible = saved.get("visible", default["visible"])
            normalized_sections.append(
                {
                    "key": default["key"],
                    "label": default["label"],
                    "visible": visible if isinstance(visible, bool) else default["visible"],
                    "order": order if isinstance(order, int) and 1 <= order <= len(SECTION_DEFAULTS) else default["order"],
                }
            )
        result["homepage_sections"] = normalized_sections

    return result


def parse_design_form(form, current_settings):
    current = normalize_design_settings(current_settings)
    values = {}
    errors = []

    for field in _COLOR_FIELDS:
        value = form.get(field, "").strip()
        if not _HEX_COLOR.fullmatch(value):
            errors.append(f"Enter a valid 6-digit hex color for {field.replace('_', ' ')}.")
        else:
            values[field] = value.lower()

    font_family = form.get("font_family", "")
    if font_family not in FONT_FAMILIES:
        errors.append("Choose a supported font.")
    else:
        values["font_family"] = font_family

    for field, lower, upper in (
        ("button_radius", 0, 32),
        ("card_radius", 0, 40),
        ("section_spacing", 24, 128),
    ):
        raw_value = form.get(field, "")
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            errors.append(f"Enter a whole number for {field.replace('_', ' ')}.")
            continue
        if not lower <= value <= upper:
            errors.append(f"{field.replace('_', ' ').capitalize()} must be between {lower} and {upper}.")
        else:
            values[field] = value

    for field, limit in (
        ("hero_title", 100),
        ("hero_subtitle", 240),
        ("hero_button_text", 40),
    ):
        value = form.get(field, "").strip()
        if len(value) > limit:
            errors.append(f"{field.replace('_', ' ').capitalize()} must be {limit} characters or fewer.")
        else:
            values[field] = value

    sections = []
    for default in SECTION_DEFAULTS:
        order_field = f"section_order_{default['key']}"
        try:
            order = int(form.get(order_field, ""))
        except (TypeError, ValueError):
            errors.append(f"Choose an order for {default['label']}.")
            continue
        if order not in range(1, len(SECTION_DEFAULTS) + 1):
            errors.append(f"{default['label']} order must be between 1 and {len(SECTION_DEFAULTS)}.")
            continue
        sections.append(
            {
                "key": default["key"],
                "label": default["label"],
                "visible": form.get(f"show_section_{default['key']}") == "on",
                "order": order,
            }
        )

    if len(sections) == len(SECTION_DEFAULTS) and sorted(section["order"] for section in sections) != list(
        range(1, len(SECTION_DEFAULTS) + 1)
    ):
        errors.append(
            f"Each homepage section must have a different order from 1 to {len(SECTION_DEFAULTS)}."
        )

    values["homepage_sections"] = sections if len(sections) == len(SECTION_DEFAULTS) else current["homepage_sections"]
    values["hero_image"] = current["hero_image"]
    return values, errors


def build_design_css(settings):
    design = normalize_design_settings(settings)
    font_family = FONT_FAMILIES[design["font_family"]]
    primary_red, primary_green, primary_blue = (
        int(design["primary_color"][index : index + 2], 16) for index in (1, 3, 5)
    )
    primary_hover = "#{:02x}{:02x}{:02x}".format(
        round(primary_red * 0.82),
        round(primary_green * 0.82),
        round(primary_blue * 0.82),
    )
    return (
        ":root{"
        f"--design-primary:{design['primary_color']};"
        f"--design-primary-hover:{primary_hover};"
        f"--design-button-gradient-start:{design['primary_color']};"
        f"--design-button-gradient-end:{design['accent_color']};"
        f"--design-button-gradient-hover-start:{primary_hover};"
        f"--design-button-gradient-hover-end:{design['accent_color']};"
        f"--design-accent:{design['accent_color']};"
        f"--design-background:{design['background_color']};"
        f"--design-surface:{design['surface_color']};"
        f"--design-text:{design['text_color']};"
        f"--design-muted:{design['muted_color']};"
        f"--design-border:{design['border_color']};"
        f"--design-font-family:{font_family};"
        f"--design-button-radius:{design['button_radius']}px;"
        f"--design-input-radius:{design['button_radius']}px;"
        f"--design-card-radius:{design['card_radius']}px;"
        f"--design-compact-card-radius:{design['card_radius']}px;"
        f"--design-spacing-section:{design['section_spacing']}px;"
        "}"
    )
