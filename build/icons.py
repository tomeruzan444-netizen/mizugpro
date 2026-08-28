# -*- coding: utf-8 -*-
"""
Icon set — 24×24 grid, 1.8 stroke, round caps and joins.

Drawn from primitives (rect / circle / line) wherever a shape allows it, so the
geometry stays exact instead of drifting the way hand-written bezier data does.
The HVAC icons come first: on an air-conditioning site the split unit, the
snowflake and the gauge carry more meaning than a generic toolbox.
"""

_W = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')
_F = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{}</svg>'

PATHS = {
    # ---- the trade ---------------------------------------------------------
    # wall-mounted split unit with air moving out of it
    "ac-unit": (
        '<rect x="2.6" y="4.4" width="18.8" height="7.2" rx="2.2"/>'
        '<path d="M6 8.6h12"/>'
        '<path d="M6.4 15.6c1.1-1.5 2.5-1.5 3.6 0s2.5 1.5 3.6 0 2.5-1.5 3.6 0"/>'
        '<path d="M6.4 19.6c1.1-1.5 2.5-1.5 3.6 0s2.5 1.5 3.6 0 2.5-1.5 3.6 0"/>'
    ),
    # outdoor condenser: housing, fan circle, blade
    "condenser": (
        '<rect x="3" y="4.5" width="18" height="15" rx="2.2"/>'
        '<circle cx="12" cy="12" r="4.6"/>'
        '<path d="M12 7.4c1.9 1.3 1.9 3.3 0 4.6-1.9-1.3-4-.6-4.6 1.2"/>'
    ),
    # ---- the four homepage services ----------------------------------------
    # One family so the tiles read as a set: the same wall unit sits at the top
    # of three of them and only what happens beneath it changes. At 30px there
    # is room for one idea per icon, so each gets exactly one — an arrow up, an
    # arrow down, a wrench. Put up, taken down, opened.
    "ac-install": (
        '<rect x="2.8" y="2.8" width="18.4" height="6.6" rx="2.1"/>'
        '<path d="M6.2 6.4h8.8"/>'
        '<path d="M12 21.4v-9.2"/><path d="m8.4 15.6 3.6-3.6 3.6 3.6"/>'
    ),
    "ac-remove": (
        '<rect x="2.8" y="2.8" width="18.4" height="6.6" rx="2.1"/>'
        '<path d="M6.2 6.4h8.8"/>'
        '<path d="M12 12.2v9.2"/><path d="m8.4 17.8 3.6 3.6 3.6-3.6"/>'
    ),
    # the wrench is the existing one reused at its exact geometry rather than
    # redrawn small; the scale is undone on the stroke so the weight matches
    "ac-repair": (
        '<rect x="2.8" y="2.8" width="18.4" height="6.6" rx="2.1"/>'
        '<path d="M6.2 6.4h8.8"/>'
        '<g transform="translate(6.8 11) scale(.52)" stroke-width="3.46">'
        '<path d="M13.9 10.1 4.5 19.5a2.1 2.1 0 0 1-3-3l9.4-9.4"/>'
        '<path d="M13.9 10.1a4.9 4.9 0 0 0 6.7-6.2l-3 3-2.7-.7-.7-2.7 3-3a4.9 4.9 0 0 0-6.2 6.7"/>'
        '</g>'
    ),
    # a printed price list, not a unit: the tile is about what it costs
    "ac-price": (
        '<path d="M4.6 2.8h14.8v18.6l-2.46-1.5-2.47 1.5-2.47-1.5'
        '-2.46 1.5-2.47-1.5-2.47 1.5Z"/>'
        '<path d="M8.4 7.6h7.2"/><path d="M8.4 11.2h7.2"/><path d="M8.4 14.8h4.4"/>'
    ),

    "snowflake": (
        '<path d="M12 2.6v18.8M3.9 7.3l16.2 9.4M20.1 7.3 3.9 16.7"/>'
        '<path d="m9.5 5.1 2.5-2.5 2.5 2.5M9.5 18.9l2.5 2.5 2.5-2.5"/>'
        '<path d="m3.9 7.3 3.4.1.2 3.4M20.1 16.7l-3.4-.1-.2-3.4"/>'
        '<path d="m20.1 7.3-3.4.1-.2 3.4M3.9 16.7l3.4-.1.2-3.4"/>'
    ),
    "flame": (
        '<path d="M12 21.4c3.4 0 6-2.4 6-5.7 0-4.4-4.3-5.9-3.4-11.1-2.6.9-5 3.6-5 7 '
        '0 1.5.6 2.4-.5 2.4-1 0-1.6-1-1.6-2.4C6 13 6 14.3 6 15.7c0 3.3 2.6 5.7 6 5.7Z"/>'
    ),
    "gauge": (
        '<path d="M4 17.5a8.6 8.6 0 1 1 16 0"/>'
        '<path d="M12 17.5 16 11"/>'
        '<circle cx="12" cy="17.5" r="1.5"/>'
        '<path d="M4.6 13.4h1.8M12 8.9V7.1M19.4 13.4h-1.8"/>'
    ),
    "droplet": (
        '<path d="M12 3.2c3.4 4 6 6.9 6 9.9a6 6 0 0 1-12 0c0-3 2.6-5.9 6-9.9Z"/>'
    ),
    "filter": (
        '<rect x="3.4" y="4.2" width="17.2" height="15.6" rx="2.2"/>'
        '<path d="M8.2 4.2v15.6M15.8 4.2v15.6M3.4 9.4h17.2M3.4 14.6h17.2"/>'
    ),
    "wrench": (
        '<path d="M13.9 10.1 4.5 19.5a2.1 2.1 0 0 1-3-3l9.4-9.4"/>'
        '<path d="M13.9 10.1a4.9 4.9 0 0 0 6.7-6.2l-3 3-2.7-.7-.7-2.7 3-3a4.9 4.9 0 0 0-6.2 6.7"/>'
    ),
    "tools": (
        '<path d="M14.4 3.9a4.4 4.4 0 0 1 5.7 5.7l-2.6-2.6-3.1 3.1 2.6 2.6a4.4 4.4 0 0 1-5.7-5.7"/>'
        '<path d="m11.3 7 -7.6 7.6a2 2 0 0 0 0 2.8l2.4 2.4a2 2 0 0 0 2.8 0L16.5 12"/>'
    ),
    "thermometer": (
        '<path d="M14 14.9V5.2a2 2 0 1 0-4 0v9.7a4.1 4.1 0 1 0 4 0Z"/>'
        '<path d="M12 9.2v6.4"/>'
    ),

    # ---- commerce and trust ------------------------------------------------
    "tag": (
        '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0l-7.2-7.2A2 2 0 0 1 2.8 12V4.8'
        'A2 2 0 0 1 4.8 2.8H12a2 2 0 0 1 1.4.6l7.2 7.2a2 2 0 0 1 0 2.8Z"/>'
        '<circle cx="8" cy="8" r="1.5"/>'
    ),
    "price": (
        '<rect x="2.4" y="5.4" width="19.2" height="13.2" rx="2.2"/>'
        '<circle cx="12" cy="12" r="3.1"/>'
        '<path d="M5.6 9.4v5.2M18.4 9.4v5.2"/>'
    ),
    "shield": (
        '<path d="M12 21.6s7.6-3.4 7.6-9.4V5.6L12 2.6 4.4 5.6v6.6c0 6 7.6 9.4 7.6 9.4Z"/>'
        '<path d="m8.9 11.8 2.2 2.2 4-4.2"/>'
    ),
    "award": (
        '<circle cx="12" cy="9.1" r="5.7"/>'
        '<path d="m9 13.9-1.6 7 4.6-2.6 4.6 2.6-1.6-7"/>'
        '<path d="m12 6.6.9 1.9 2 .3-1.5 1.5.4 2.1-1.8-1-1.8 1 .4-2.1-1.5-1.5 2-.3Z"/>'
    ),
    "star": '<path d="m12 2.4 2.9 6.1 6.7.9-4.9 4.7 1.2 6.6L12 17.5l-5.9 3.2 1.2-6.6-4.9-4.7 6.7-.9Z"/>',
    "quote": (
        '<path d="M9.9 5.4C6.6 7 4.9 9.7 4.9 13.5V19h6.4v-6.7H8.5c.2-1.7 1.1-2.9 2.7-3.7Z"/>'
        '<path d="M19.1 5.4c-3.3 1.6-5 4.3-5 8.1V19h6.4v-6.7h-2.8c.2-1.7 1.1-2.9 2.7-3.7Z"/>'
    ),
    "users": (
        '<circle cx="9.2" cy="8.1" r="3.5"/>'
        '<path d="M2.8 20a6.4 6.4 0 0 1 12.8 0"/>'
        '<path d="M16.6 5.1a3.5 3.5 0 0 1 0 6M17.8 14.5A6.4 6.4 0 0 1 21.4 20"/>'
    ),
    "check": '<path d="m20 6.4-11 11-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="9.2"/><path d="m8.4 12.2 2.4 2.4 4.8-5.1"/>',
    "bolt": '<path d="M13.4 2 4 13.6h6L9.4 22 20 10.4h-6.6L13.4 2Z"/>',
    "sparkles": (
        '<path d="m11 2.8 1.7 4.2 4.2 1.7-4.2 1.7-1.7 4.2-1.7-4.2L5.1 8.7l4.2-1.7Z"/>'
        '<path d="m18 14.4 1 2.4 2.4 1-2.4 1-1 2.4-1-2.4-2.4-1 2.4-1Z"/>'
    ),

    # ---- interface ---------------------------------------------------------
    "phone": (
        '<path d="M21.4 16.9v2.9a2 2 0 0 1-2.2 2 19.6 19.6 0 0 1-8.5-3 19.3 19.3 0 0 1-6-6'
        'A19.6 19.6 0 0 1 1.7 4.2 2 2 0 0 1 3.7 2h2.9a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8'
        'a2 2 0 0 1-.5 2.1L7.7 9.9a15.8 15.8 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>'
    ),
    "mail": '<rect x="2.4" y="4.6" width="19.2" height="14.8" rx="2.2"/><path d="m2.8 7.4 9.2 5.6 9.2-5.6"/>',
    "pin": '<path d="M20 10.2c0 5.9-8 11.8-8 11.8s-8-5.9-8-11.8a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10.1" r="3"/>',
    "map": '<path d="m9 3.2-6.2 3v14.6l6.2-3 6 3 6.2-3V3.2l-6.2 3Z"/><path d="M9 3.2v14.6M15 6.2v14.6"/>',
    "clock": '<circle cx="12" cy="12" r="9.2"/><path d="M12 6.9V12l3.5 2.1"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2.2"/><path d="M8 3v4M16 3v4M3 10.2h18"/>',
    "doc": (
        '<path d="M14.2 2.8H7a2 2 0 0 0-2 2v14.4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7.6Z"/>'
        '<path d="M14.2 2.8v4.8H19M9 13h6M9 16.6h4"/>'
    ),
    "list": '<path d="M8.6 6.2h12.6M8.6 12h12.6M8.6 17.8h12.6"/><path d="M3.4 6.2h.02M3.4 12h.02M3.4 17.8h.02"/>',
    "home": '<path d="m3 10.4 9-7.2 9 7.2V20a1.6 1.6 0 0 1-1.6 1.6H4.6A1.6 1.6 0 0 1 3 20Z"/><path d="M9.4 21.6v-7.2h5.2v7.2"/>',
    "info": '<circle cx="12" cy="12" r="9.2"/><path d="M12 11.2v5.4M12 7.6h.02"/>',
    "truck": (
        '<path d="M14.4 16.4V5.6H2.6v10.8h1.8"/><path d="M14.4 9.2h3.8l3.2 3.7v3.5h-2"/>'
        '<circle cx="7" cy="17.6" r="2"/><circle cx="17" cy="17.6" r="2"/><path d="M9 17.6h6"/>'
    ),
    "arrow": '<path d="M19.2 12H4.8"/><path d="m11.6 19.2-7.2-7.2 7.2-7.2"/>',
    "chevron": '<path d="m6 9.2 6 6 6-6"/>',
    "up": '<path d="m6 15 6-6 6 6"/>',

    # ---- social ------------------------------------------------------------
    "facebook": (
        '<path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.8 3.7-3.8'
        '1.1 0 2.2.2 2.2.2v2.4h-1.2c-1.2 0-1.6.8-1.6 1.6V12h2.7l-.4 2.9h-2.3v7A10 10 0 0 0 22 12Z"/>'
    ),
    "youtube": (
        '<path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2'
        ' 26 26 0 0 0 2 12c0 1.6.1 3.2.4 4.8a2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4'
        'a2.5 2.5 0 0 0 1.8-1.8c.3-1.6.4-3.2.4-4.8s-.1-3.2-.4-4.8ZM10 15V9l5.2 3Z"/>'
    ),
    "whatsapp": '<path d="M12.04 2a9.9 9.9 0 0 0-8.5 14.9L2 22l5.3-1.4A9.9 9.9 0 1 0 12.04 2Zm5.7 14.1c-.24.68-1.4 1.3-1.94 1.35-.5.05-1.13.07-1.82-.11a16.6 16.6 0 0 1-1.65-.61c-2.9-1.25-4.8-4.17-4.95-4.37-.14-.2-1.18-1.57-1.18-3s.75-2.12 1.02-2.41c.27-.3.58-.37.78-.37h.56c.18 0 .42-.07.66.5.24.58.82 2 .89 2.15.07.14.12.31.02.5-.1.2-.15.32-.29.49-.14.17-.3.38-.43.5-.14.15-.29.3-.12.6.17.28.75 1.24 1.61 2 1.11 1 2.05 1.3 2.34 1.45.29.14.46.12.63-.07.17-.2.73-.85.92-1.15.2-.29.39-.24.66-.14.27.1 1.69.8 1.98.94.29.15.48.22.55.34.07.12.07.7-.17 1.38Z"/>',
}

FILLED = {"star", "quote", "whatsapp", "facebook", "youtube", "bolt", "sparkles", "flame", "droplet"}


def icon(name, cls=""):
    body = PATHS.get(name)
    if not body:
        return ""
    svg = (_F if name in FILLED else _W).format(body)
    if cls:
        svg = svg.replace("<svg ", '<svg class="%s" ' % cls, 1)
    return svg
