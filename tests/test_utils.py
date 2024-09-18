from PIL import Image

import utils


def test_get_pokedex():
    pokedex, pokedex_name = utils.get_pokedex()

    assert len(pokedex) != 0
    assert len(pokedex_name) != 0

    assert isinstance(pokedex, dict)
    assert isinstance(pokedex_name, dict)


def test_get_image_by_id():
    image = utils.get_image_by_id(1)

    assert isinstance(image, Image.Image)

    assert image is not None
    assert image.size != (0, 0)


def test_create_coloring_page():
    image = utils.get_image_by_id(1)
    coloring_page = utils.create_coloring_page(image)

    assert isinstance(coloring_page, Image.Image)

    assert coloring_page is not None
    assert coloring_page.size != (0, 0)
