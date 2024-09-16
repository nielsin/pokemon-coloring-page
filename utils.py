import random
from functools import cache
from io import BytesIO
from typing import Any, Dict, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFilter

import config


@cache
def get_pokedex() -> Tuple[Dict[int, Dict[str, Any]], Dict[str, int]]:
    """
    Retrieves the Pokedex data and returns it as a tuple.

    Returns:
        A tuple containing two dictionaries:
        - The first dictionary maps Pokemon IDs to their corresponding data.
        - The second dictionary maps English Pokemon names to their corresponding IDs.
    """

    url = config.POKEDEX_URL
    pokedex_data = httpx.get(url).json()
    pokedex = {pokemon["id"]: pokemon for pokemon in pokedex_data}
    pokedex_name = {pokemon["name"]["english"]: id for id, pokemon in pokedex.items()}
    return pokedex, pokedex_name


@cache
def get_image_by_id(pokemon_id: int) -> Image:
    """
    Retrieves the image of a Pokemon based on its ID.

    Args:
        pokemon_id (int): The ID of the Pokemon.

    Returns:
        Image: The image of the Pokemon.
    """

    pokemon_name = get_pokedex()[0][pokemon_id]["name"]["english"]
    pokemon_name = (
        pokemon_name.lower().replace(" ", "-").replace(".", "").replace("'", "")
    )
    img_url = f"{config.IMAGE_URL}/{pokemon_name}.jpg"

    # Get image and check response status
    response = httpx.get(img_url)

    if response.status_code != 200:
        print("Warning: Image not found. Trying another source.")
        img_url = get_pokedex()[0][pokemon_id]["image"]["hires"]
        response = httpx.get(img_url)

    return Image.open(BytesIO(response.content))


def get_image_by_name(pokemon_name: str) -> Image:
    """
    Retrieves the image of a Pokemon based on its name.

    Args:
        pokemon_name (str): The name of the Pokemon.

    Returns:
        Image: The image of the Pokemon.
    """

    pokemon_id = get_pokedex()[1][pokemon_name]
    return get_image_by_id(pokemon_id)


def create_coloring_page(image: Image, noise_threshold: float = 0.95) -> Image:
    """
    Creates a coloring page from the given image.

    Args:
        image (Image): The input image.
        noise_threshold (float, optional): The threshold value for noise removal. Defaults to 0.95.

    Returns:
        Image: The coloring page image.
    """

    # Create white background if image is RGBA
    if image.mode == "RGBA":
        image = Image.alpha_composite(Image.new("RGBA", image.size, "WHITE"), image)
    # Convert to grayscale
    image_gray = image.convert("L")
    # Smooth the image
    image_smooth = image_gray.filter(ImageFilter.SMOOTH)
    # Get contours
    image_contour = image_smooth.filter(ImageFilter.CONTOUR)
    # Remove noise
    image_clean = image_contour.point(lambda p: 255 if p > 255 * noise_threshold else p)

    return image_clean


def pokemon_coloring_page(
    pokemon_name: str = None, pokemon_id: int = None, stamp_name: bool = True
) -> Tuple[Image, Image, str, int]:
    """
    Generates a coloring page for a Pokemon.

    Args:
        pokemon_name (str, optional): The name of the Pokemon. Defaults to None.
        pokemon_id (int, optional): The ID of the Pokemon. Defaults to None.
        stamp_name (bool, optional): Whether to stamp the Pokemon name on the coloring page. Defaults to True.

    Returns:
        Tuple[Image, Image, str, int]: A tuple containing the coloring page image, the original image, the Pokemon name, and the Pokemon ID.
    """

    if pokemon_name:
        pokemon_id = get_pokedex()[1][pokemon_name]
    elif pokemon_id:
        pokemon_name = get_pokedex()[0][pokemon_id]["name"]["english"]
    else:
        # Get random pokemon
        pokedex, pokedex_name = get_pokedex()
        pokemon_id = random.choice(list(pokedex.keys()))
        pokemon_name = pokedex[pokemon_id]["name"]["english"]

    image = get_image_by_id(pokemon_id)
    coloring_page = create_coloring_page(image)

    if stamp_name:
        draw = ImageDraw.Draw(coloring_page)
        draw.text((0, 0), f"#{pokemon_id} - {pokemon_name}", fill="black")

    return coloring_page, image, pokemon_name, pokemon_id


def img_resize(image: Image, max_width: int, max_height: int) -> Image:
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


def pokemon_print_sheet(
    paper_height_mm: float = config.PAPER_HEIGHT_MM,
    paper_width_mm: float = config.PAPER_WIDTH_MM,
    margin_mm: float = config.MARGIN_MM,
    font_size_mm: float = config.FONT_SIZE_MM,
    dpi: int = config.DPI,
    rows: int = config.ROWS,
    columns: int = config.COLUMNS,
    include_list: list = [],
    exclude_list: list = [],
) -> Tuple[Image, list]:
    """
    Generate a sheet of Pokemon coloring pages.

    Args:
        paper_height_mm (float): The height of the paper in millimeters. Defaults to config.PAPER_HEIGHT_MM.
        paper_width_mm (float): The width of the paper in millimeters. Defaults to config.PAPER_WIDTH_MM.
        margin_mm (float): The margin size in millimeters. Defaults to config.MARGIN_MM.
        font_size_mm (float): The font size in millimeters. Defaults to config.FONT_SIZE_MM.
        dpi (int): The dots per inch. Defaults to config.DPI.
        rows (int): The number of rows in the sheet. Defaults to config.ROWS.
        columns (int): The number of columns in the sheet. Defaults to config.COLUMNS.
        include_list (list): A list of Pokemon IDs to include in the sheet. Defaults to an empty list.
        exclude_list (list): A list of Pokemon IDs to exclude from the sheet. Defaults to an empty list.

    Returns:
        Tuple[Image, list]: A tuple containing the output image and the updated exclude list.
    """
    # Convert mm to pixels
    PAPER_WIDTH = int(paper_width_mm * dpi / 25.4)
    PAPER_HEIGHT = int(paper_height_mm * dpi / 25.4)
    MARGIN = int(margin_mm * dpi / 25.4)
    FONT_SIZE = int(font_size_mm * dpi / 25.4)

    # Create a new image for the paper
    output_image = Image.new("RGB", (PAPER_WIDTH, PAPER_HEIGHT), "white")

    # Set the maximum image size
    MAX_IMAGE_WIDTH = PAPER_WIDTH // columns - 2 * MARGIN
    MAX_IMAGE_HEIGHT = PAPER_HEIGHT // rows - 2 * MARGIN

    for i in range(rows):
        for j in range(columns):
            while True:
                try:
                    if len(include_list) > 0:
                        pokemon_id = include_list[0]
                    else:
                        pokemon_id = None

                    coloring_page, image, pokemon_name, pokemon_id = (
                        pokemon_coloring_page(pokemon_id=pokemon_id, stamp_name=False)
                    )

                except Exception as e:
                    print(f"Error: {e}")
                    continue

                # Remove the pokemon from the include list
                if pokemon_id in include_list:
                    include_list.remove(pokemon_id)

                if pokemon_id not in exclude_list:
                    exclude_list.append(pokemon_id)
                    break

            coloring_page = img_resize(coloring_page, MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT)

            x = j * (PAPER_WIDTH // columns) + MARGIN
            y = i * (PAPER_HEIGHT // rows) + MARGIN

            dx = (MAX_IMAGE_WIDTH - coloring_page.width) // 2
            dy = (MAX_IMAGE_HEIGHT - coloring_page.height) // 2

            output_image.paste(coloring_page, (x + dx, y + dy))

            draw = ImageDraw.Draw(output_image)
            draw.text(
                (x, y),
                f"#{pokemon_id} - {pokemon_name}",
                fill="black",
                font_size=FONT_SIZE,
            )

    draw = ImageDraw.Draw(output_image)

    # Draw horizontal lines
    for i in range(rows - 1):
        y = (PAPER_HEIGHT // rows) * (i + 1)
        draw.line((MARGIN, y, PAPER_WIDTH - MARGIN, y), fill="black", width=1)

    # Draw vertical lines
    for i in range(columns - 1):
        x = (PAPER_WIDTH // columns) * (i + 1)
        draw.line((x, MARGIN, x, PAPER_HEIGHT - MARGIN), fill="black", width=1)

    return output_image, exclude_list
