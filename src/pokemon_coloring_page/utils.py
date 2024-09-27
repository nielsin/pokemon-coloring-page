import random
from functools import cache
from io import BytesIO
from string import capwords
from typing import Tuple

import httpx
from joblib import Memory, Parallel, delayed
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .config import Config as config

# Create a cache object
memory = Memory(location=config.CACHE_DIR, verbose=0)
# Clear old cache entries
memory.reduce_size(age_limit=config.CACHE_AGE_LIMIT)


@memory.cache
def get_types():
    """
    Retrieves the types of Pokemon from the PokeAPI.
    Store everything in lowercase.
    """

    url = f"{config.POKEAPI_URL}type"

    types = {}

    with httpx.Client() as client:
        response = client.get(url)
        results = response.json()["results"]
        for type in [client.get(type["url"]).json() for type in results]:
            type_name = type["name"].lower()
            types[type_name] = []
            for pokemon in type["pokemon"]:
                name = pokemon["pokemon"]["name"].lower()
                id = int(pokemon["pokemon"]["url"].split("/")[-2])
                types[type_name].append({"name": name, "id": id})

    return types


@cache
def get_pokedex_types():
    pokedex = {}
    for type, pokemon_list in get_types().items():
        for pokemon in pokemon_list:
            if pokemon["id"] not in pokedex:
                pokedex[pokemon["id"]] = {
                    "name": pokemon["name"],
                    "types": [type],
                }
            else:
                pokedex[pokemon["id"]]["types"].append(type)
    return pokedex


@cache
def get_pokedex(type_filter: str = None):
    if type_filter:
        type_filter = type_filter.lower()
        if type_filter in get_types().keys():
            return {
                k: v["name"]
                for k, v in get_pokedex_types().items()
                if type_filter in v["types"]
            }
    return {k: v["name"] for k, v in get_pokedex_types().items()}


def pokemon_id2name(pokemon_id: int) -> str:
    """
    Converts a Pokemon ID to its name.

    Args:
        pokemon_id (int): The ID of the Pokemon.

    Returns:
        str: The name of the Pokemon.
    """

    return get_pokedex().get(pokemon_id, None)


@cache
def _pokedex_names():
    return {v: k for k, v in get_pokedex().items()}


def pokemon_name2id(pokemon_name: str) -> int:
    """
    Converts a Pokemon name to its ID.

    Args:
        pokemon_name (str): The name of the Pokemon.

    Returns:
        int: The ID of the Pokemon.
    """

    return _pokedex_names().get(pokemon_name.lower(), None)


def pokemon_id2types(pokemon_id: int) -> list:
    """
    Retrieves the types of a Pokemon based on its ID.

    Args:
        pokemon_id (int): The ID of the Pokemon.

    Returns:
        list: The types of the Pokemon.
    """

    return get_pokedex_types().get(pokemon_id, {}).get("types", [])


@memory.cache
def get_image_by_id(pokemon_id: int) -> Image.Image:
    """
    Retrieves the image of a Pokemon based on its ID.

    Args:
        pokemon_id (int): The ID of the Pokemon.

    Returns:
        Image: The image of the Pokemon.
    """

    with httpx.Client() as client:
        # Check Pokemon ID: 10270
        # Pokemon ID: 10267

        try:
            im = client.get(
                f"{config.SPRITES_URL}pokemon/other/official-artwork/{pokemon_id}.png"
            ).content
            return Image.open(BytesIO(im))
        except Exception:
            pass

        try:
            im = client.get(
                f"{config.SPRITES_URL}pokemon/other/home/{pokemon_id}.png"
            ).content
            return Image.open(BytesIO(im))
        except Exception:
            pass

        try:
            im = client.get(f"{config.SPRITES_URL}pokemon/{pokemon_id}.png").content
            return Image.open(BytesIO(im))
        except Exception:
            pass


def get_image_by_name(pokemon_name: str) -> Image.Image:
    """
    Retrieves the image of a Pokemon based on its name.

    Args:
        pokemon_name (str): The name of the Pokemon.

    Returns:
        Image: The image of the Pokemon.
    """

    pokemon_id = pokemon_name2id(pokemon_name)
    return get_image_by_id(pokemon_id)


@memory.cache
def get_pokemon_print_name(pokemon_id, language="en"):
    with httpx.Client() as client:
        url = f"{config.POKEAPI_URL}pokemon-species/{pokemon_id}"
        response = client.get(url)
        if response.status_code == 200:
            data = response.json()
            for entry in data["names"]:
                if entry["language"]["name"] == language:
                    return entry["name"]

        url = f"{config.POKEAPI_URL}pokemon/{pokemon_id}"
        response = client.get(url)
        if response.status_code == 200:
            data = response.json()
            name = data["name"]
            for form in data["forms"]:
                if form["name"] == name:
                    response = client.get(form["url"])
                    if response.status_code == 200:
                        data = response.json()
                        for entry in data["names"]:
                            if entry["language"]["name"] == language:
                                return entry["name"]

        return capwords(pokemon_id2name(pokemon_id).replace("-", " "))  # Fallback


def img_resize(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """
    Resize the given image while maintaining its aspect ratio.

    Args:
        image (Image): The image to be resized.
        max_width (int): The maximum width of the resized image.
        max_height (int): The maximum height of the resized image.

    Returns:
        Image: The resized image.
    """

    w = max_width
    h = int(image.height * (w / image.width))

    if h > max_height:
        h = max_height
        w = int(image.width * (h / image.height))

    return image.resize((w, h), resample=Image.LANCZOS)


def create_coloring_image(
    pokemon_id: int,
    max_width: int,
    max_height: int,
    noise_threshold: float = 0.05,
    histogram_cutoff: float = 0.1,
    crop: bool = True,
    color: bool = False,
) -> Image.Image:
    """
    Creates a coloring page from the given image.

    Args:
        image (Image): The input image.
        noise_threshold (float, optional): The threshold value for noise removal. Defaults to 0.05.

    Returns:
        Image: The coloring page image.
    """

    # Get the image of the Pokemon
    image = get_image_by_id(pokemon_id)

    # Create white background if image is RGBA
    if image.mode == "RGBA":
        image = Image.alpha_composite(Image.new("RGBA", image.size, "WHITE"), image)

    # Crop the image
    if crop:
        inverted_image = ImageOps.invert(image.convert("L"))
        bbox = inverted_image.getbbox()
        if bbox:
            image = image.crop(bbox)
            # Add padding to prevent artifacts at the edges when resizing
            image = ImageOps.expand(image, border=1, fill="WHITE")

    # Resize the image
    image = img_resize(image, max_width, max_height)

    if not color:
        # Convert to grayscale
        image = image.convert("L")
        # Pad the image
        image = ImageOps.expand(image, border=10, fill=255)
        # Smooth the image
        image = image.filter(ImageFilter.SMOOTH)
        # Get contours
        image = image.filter(ImageFilter.CONTOUR)
        # Remove noise
        image = image.point(lambda p: 255 if p > 255 * (1 - noise_threshold) else p)
        image = image.point(lambda p: 0 if p < 255 * noise_threshold else p)
        # Stretch histogram
        image = ImageOps.autocontrast(image, cutoff=histogram_cutoff * 100, ignore=255)
        # Remove padding
        image = ImageOps.crop(image, border=10)

    return image


def parallel_cache_pokeapi_calls(ids):
    """
    Parallelize the cache calls to the PokeAPI.
    Will cache the image and print name of the Pokemon.
    """
    Parallel(n_jobs=-1, backend="threading")(
        [delayed(get_image_by_id)(i) for i in ids]
        + [delayed(get_pokemon_print_name)(i) for i in ids]
    )


def generate_pokemon_coloring_page(
    page_height_mm: float = config.PAGE_HEIGHT_MM,
    page_width_mm: float = config.PAGE_WIDTH_MM,
    outer_margin_mm: float = config.OUTER_MARGIN_MM,
    inner_margin_mm: float = config.INNER_MARGIN_MM,
    font_size_mm: float = config.FONT_SIZE_MM,
    dpi: int = config.DPI,
    rows: int = config.ROWS,
    columns: int = config.COLUMNS,
    include_list: list = [],
    exclude_list: list = [],
    color: bool = False,
    crop: bool = True,
) -> Tuple[Image.Image, list]:
    """
    Generate a sheet of Pokemon coloring pages.

    Args:
        page_height_mm (float): The height of the sheet in millimeters. Defaults to config.PAGE_HEIGHT_MM.
        page_width_mm (float): The width of the sheet in millimeters. Defaults to config.PAGE_WIDTH_MM.
        outer_margin_mm (float): The outer margin size in millimeters. Defaults to config.OUTER_MARGIN_MM.
        inner_margin_mm (float): The inner margin size in millimeters. Defaults to config.INNER_MARGIN_MM.
        font_size_mm (float): The font size in millimeters. Defaults to config.FONT_SIZE_MM.
        dpi (int): The dots per inch. Defaults to config.DPI.
        rows (int): The number of rows in the sheet. Defaults to config.ROWS.
        columns (int): The number of columns in the sheet. Defaults to config.COLUMNS.
        include_list (list): A list of Pokemon IDs to include in the sheet. Defaults to an empty list.
        exclude_list (list): A list of Pokemon IDs to exclude from the sheet. Defaults to an empty list.
        color (bool): Whether to generate a colored sheet. Defaults to False.
        crop (bool): Whether to crop the images. Defaults to True.

    Returns:
        Tuple[Image, list]: A tuple containing the output image and the updated exclude list.
    """
    # Convert mm to pixels
    PAGE_WIDTH = int(page_width_mm * dpi / 25.4)
    PAGE_HEIGHT = int(page_height_mm * dpi / 25.4)
    OUTER_MARGIN = int(outer_margin_mm * dpi / 25.4)
    INNER_MARGIN = int(inner_margin_mm * dpi / 25.4)
    FONT_SIZE = int(font_size_mm * dpi / 25.4)

    # Make a copy of the include and exclude lists
    include_list = include_list.copy()
    exclude_list = exclude_list.copy()

    # Create a new image for the paper
    output_image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")

    # Calculate the size of each image box
    IMAGE_BOX_WIDTH = (PAGE_WIDTH - 2 * OUTER_MARGIN) // columns
    IMAGE_BOX_HEIGHT = (PAGE_HEIGHT - 2 * OUTER_MARGIN) // rows

    # Set the maximum image size
    MAX_IMAGE_WIDTH = IMAGE_BOX_WIDTH - 2 * INNER_MARGIN
    MAX_IMAGE_HEIGHT = IMAGE_BOX_HEIGHT - 2 * INNER_MARGIN

    for i in range(rows):
        for j in range(columns):
            while True:
                try:
                    if len(include_list) > 0:
                        pokemon_id = include_list[0]
                    else:
                        pokemon_id = random.choice(list(get_pokedex().keys()))

                    coloring_image = create_coloring_image(
                        pokemon_id,
                        MAX_IMAGE_WIDTH,
                        MAX_IMAGE_HEIGHT,
                        color=color,
                        crop=crop,
                    )

                except Exception as e:
                    print(f"Error: {e}")
                    print(
                        f"Unable to generate coloring page for Pokemon ID: {pokemon_id}"
                    )
                    if pokemon_id in include_list:
                        include_list.remove(pokemon_id)
                    continue

                # Remove the pokemon from the include list
                if pokemon_id in include_list:
                    include_list.remove(pokemon_id)

                if pokemon_id not in exclude_list:
                    exclude_list.append(pokemon_id)
                    break

            x = j * IMAGE_BOX_WIDTH + OUTER_MARGIN
            y = i * IMAGE_BOX_HEIGHT + OUTER_MARGIN

            dx = (IMAGE_BOX_WIDTH - coloring_image.width) // 2
            dy = (IMAGE_BOX_HEIGHT - coloring_image.height) // 2

            output_image.paste(coloring_image, (x + dx, y + dy))

            draw = ImageDraw.Draw(output_image)

            draw.text(
                (x + INNER_MARGIN, y + INNER_MARGIN),
                f"#{pokemon_id} - {get_pokemon_print_name(pokemon_id)}\n{'\n'.join([capwords(t) for t in pokemon_id2types(pokemon_id)])}",
                fill="black",
                font_size=FONT_SIZE,
            )

    draw = ImageDraw.Draw(output_image)

    # Draw horizontal lines
    for i in range(rows - 1):
        y = IMAGE_BOX_HEIGHT * (i + 1) + OUTER_MARGIN
        draw.line(
            (OUTER_MARGIN, y, PAGE_WIDTH - OUTER_MARGIN, y), fill="black", width=1
        )

    # Draw vertical lines
    for i in range(columns - 1):
        x = IMAGE_BOX_WIDTH * (i + 1) + OUTER_MARGIN
        draw.line(
            (x, OUTER_MARGIN, x, PAGE_HEIGHT - OUTER_MARGIN), fill="black", width=1
        )

    return output_image
