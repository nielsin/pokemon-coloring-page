from datetime import timedelta
from pathlib import Path


class Config:
    # Cache
    CACHE_DIR = Path.home() / ".cache" / "pokemon-coloring-page"
    CACHE_AGE_LIMIT = timedelta(days=7)

    # Attribution
    ATTRIBUTION = "Data source: pokeapi.co"

    # Pokédex
    POKEAPI_URL = "https://pokeapi.co/api/v2/"
    SPRITES_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/"

    # Default sheet settings
    PAGE_WIDTH_MM = 297
    PAGE_HEIGHT_MM = 210
    OUTER_MARGIN_MM = 10
    INNER_MARGIN_MM = 2
    FONT_SIZE_MM = 2.5
    DPI = 200
    ROWS = 2
    COLUMNS = 3
    COLOR = False
    CROP = True

    # Page element colors
    COLOR_LINES = "gray"
    COLOR_NAMES = "gray"
    COLOR_TYPES = "gray"
    COLOR_ATTRIBUTION = "gray"

    COLOR_PAGE_SETUP = "#808080"
    COLOR_SELECTED_POKEMON = "#008000"
    COLOR_UNSELECTED_POKEMON = "#808080"
    COLOR_MESSAGE = "#ff0000"
    COLOR_HIGHLIGHT = "#ffaf00"
    COLOR_COMMAND = "#00afff"

    # Standard page sizes in mm (width, height) in portrait orientation
    STANDARD_PAGE_SIZES_MM = {
        "A0": (841, 1189),
        "A1": (594, 841),
        "A2": (420, 594),
        "A3": (297, 420),
        "A4": (210, 297),
        "A5": (148, 210),
        "Letter": (215.9, 279.4),
        "Legal": (215.9, 355.6),
        "Tabloid": (279.4, 431.8),
        "Ledger": (279.4, 431.8),
        "Junior Legal": (127, 203.2),
        "Half Letter": (139.7, 215.9),
        "Government Letter": (203.2, 266.7),
        "Government Legal": (215.9, 330.2),
        "ANSI A": (216, 279),
        "ANSI B": (279, 432),
        "ANSI C": (432, 559),
        "ANSI D": (559, 864),
    }
