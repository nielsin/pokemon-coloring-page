import os
import random

import typer
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from typing_extensions import Annotated

import config
from utils import get_pokedex, pokemon_print_sheet


def main(
    page_width: float = config.PAPER_WIDTH_MM,
    page_height: float = config.PAPER_HEIGHT_MM,
    margin: float = config.MARGIN_MM,
    font_size: float = config.FONT_SIZE_MM,
    rows: int = config.ROWS,
    columns: int = config.COLUMNS,
):
    """
    Pokémon Coloring Page CLI.
    """

    # Define a list of suggestions
    pokedex, pokedex_name = get_pokedex()
    suggestions = list(pokedex_name.keys())

    # Create a prompt session with FuzzyCompleter
    word_completer = WordCompleter(suggestions)
    fuzzy_completer = FuzzyCompleter(word_completer)
    session = PromptSession(completer=fuzzy_completer)

    # Total number of pokemon to select
    n_pokemon = rows * columns

    # Select n random pokemon
    selected_pokemon = []
    user_selected_pokemon = 0
    messages = []

    while True:
        try:
            # Add missing pokemon to list
            while len(selected_pokemon) < n_pokemon:
                new_pokemon = random.choice(list(pokedex_name.keys()))
                if new_pokemon not in selected_pokemon:
                    selected_pokemon.append(new_pokemon)

            # Remove pokemon if list is full
            selected_pokemon = selected_pokemon[:n_pokemon]

            # Clear the screen
            os.system("cls" if os.name == "nt" else "clear")

            print_formatted_text(
                HTML(
                    "<white>Pokémon </white><red>C</red><green>O</green><yellow>L</yellow><blue>O</blue><magenta>R</magenta><cyan>I</cyan><red>N</red><green>G</green><white> page CLI</white>"
                )
            )

            # Print page setup
            page_setup_color = "gray"
            print_formatted_text(HTML(""))
            print_formatted_text(
                HTML(
                    f"<{page_setup_color}>Page size:\t{page_width}x{page_height}mm</{page_setup_color}>"
                )
            )
            print_formatted_text(
                HTML(f"<{page_setup_color}>Margin:\t\t{margin}mm</{page_setup_color}>")
            )
            print_formatted_text(
                HTML(
                    f"<{page_setup_color}>Font size:\t{font_size}mm</{page_setup_color}>"
                )
            )
            print_formatted_text(
                HTML(
                    f"<{page_setup_color}>Grid:\t\t{columns}x{rows}</{page_setup_color}>"
                )
            )

            print_formatted_text(HTML(""))
            print_formatted_text(HTML(f"Select {n_pokemon} Pokémon to print."))
            print_formatted_text(HTML("Adding more will replace the last one."))
            print_formatted_text(HTML(""))
            print_formatted_text(
                HTML("Selected Pokémon (<gray>auto</gray>/<green>manual</green>):")
            )

            cc = 0
            for pokemon in selected_pokemon:
                color = "green" if cc < user_selected_pokemon else "gray"
                print_formatted_text(
                    HTML(
                        f"<{color}> >> #{pokedex_name[pokemon]:<4} {pokemon}</{color}>"
                    )
                )
                cc += 1

            # Print messages
            for message in messages:
                print_formatted_text(message)
            messages = []

            user_input = session.prompt("> ")

            if not user_input:
                break

            if user_input not in pokedex_name.keys():
                messages.append(HTML("<red>Invalid input. Please try again.</red>"))
                continue

            if user_input in selected_pokemon:
                messages.append(
                    HTML("<red>Pokemon already selected. Please try again.</red>")
                )
                continue

            selected_pokemon.insert(0, user_input)
            user_selected_pokemon += 1

        except (KeyboardInterrupt, EOFError):
            break

    output_image, exclude_list = pokemon_print_sheet(
        include_list=[pokedex_name[pokemon] for pokemon in selected_pokemon],
        rows=rows,
        columns=columns,
        paper_width_mm=page_width,
        paper_height_mm=page_height,
        margin_mm=margin,
        font_size_mm=font_size,
    )
    output_image.show()


class PokemonColoringPageCLI:
    # Get default values from config.py
    PAGE_WIDTH_MM = config.PAPER_WIDTH_MM
    PAGE_HEIGHT_MM = config.PAPER_HEIGHT_MM
    MARGIN_MM = config.MARGIN_MM
    FONT_SIZE_MM = config.FONT_SIZE_MM
    ROWS = config.ROWS
    COLUMNS = config.COLUMNS

    def __init__(self):
        pass

    def n_pokemon(self):
        return self.ROWS * self.COLUMNS

    def run(
        self,
        page_width: Annotated[
            int, typer.Option(help="Page width in mm")
        ] = config.PAPER_WIDTH_MM,
        page_height: Annotated[
            int, typer.Option(help="Page height in mm")
        ] = config.PAPER_HEIGHT_MM,
        margin: Annotated[int, typer.Option(help="Margin in mm")] = config.MARGIN_MM,
        font_size: Annotated[
            int, typer.Option(help="Font size in mm")
        ] = config.FONT_SIZE_MM,
        rows: Annotated[int, typer.Option(help="Number of rows")] = config.ROWS,
        columns: Annotated[
            int, typer.Option(help="Number of columns")
        ] = config.COLUMNS,
    ):
        """
        Run the Pokémon Coloring Page CLI.
        """

        self.PAGE_WIDTH_MM = page_width
        self.PAGE_HEIGHT_MM = page_height
        self.MARGIN_MM = margin
        self.FONT_SIZE_MM = font_size
        self.ROWS = rows
        self.COLUMNS = columns

        main(
            page_width=self.PAGE_WIDTH_MM,
            page_height=self.PAGE_HEIGHT_MM,
            margin=self.MARGIN_MM,
            font_size=self.FONT_SIZE_MM,
            rows=self.ROWS,
            columns=self.COLUMNS,
        )


if __name__ == "__main__":
    app = PokemonColoringPageCLI()
    typer.run(app.run)
    # typer.run(main)
