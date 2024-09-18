import os
import random

import typer
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from typing_extensions import Annotated

import config
from utils import get_pokedex, pokemon_print_sheet


class PokemonColoringPageCLI:
    """Class for the Pokémon Coloring Page CLI."""

    def n_pokemon(self):
        return self.ROWS * self.COLUMNS

    def get_page_description(self):
        description = "Custom"

        # Find page size description
        for page_size, (width, height) in config.STANDARD_PAGE_SIZES_MM.items():
            if width in (self.PAGE_WIDTH_MM, self.PAGE_HEIGHT_MM):
                if height in (self.PAGE_WIDTH_MM, self.PAGE_HEIGHT_MM):
                    description = page_size
                    break

        # Get orientation
        if self.PAGE_WIDTH_MM > self.PAGE_HEIGHT_MM:
            description += " Landscape"
        elif self.PAGE_WIDTH_MM < self.PAGE_HEIGHT_MM:
            description += " Portrait"

        return description

    def run(
        self,
        page_width: Annotated[
            int, typer.Option(help="Page width in mm")
        ] = config.PAGE_WIDTH_MM,
        page_height: Annotated[
            int, typer.Option(help="Page height in mm")
        ] = config.PAGE_HEIGHT_MM,
        outer_margin: Annotated[
            int, typer.Option(help="Outer margin in mm")
        ] = config.OUTER_MARGIN_MM,
        inner_margin: Annotated[
            int, typer.Option(help="Inner margin in mm")
        ] = config.INNER_MARGIN_MM,
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
        self.OUTER_MARGIN_MM = outer_margin
        self.INNER_MARGIN_MM = inner_margin
        self.FONT_SIZE_MM = font_size
        self.ROWS = rows
        self.COLUMNS = columns
        self.MESSAGES = []

        # Define a list of suggestions
        pokedex, pokedex_name = get_pokedex()
        suggestions = list(pokedex_name.keys())

        # Create a prompt session with FuzzyCompleter
        word_completer = WordCompleter(suggestions)
        fuzzy_completer = FuzzyCompleter(word_completer)
        session = PromptSession(completer=fuzzy_completer)

        # Some variables
        selected_pokemon = []
        user_selected_pokemon = 0

        while True:
            try:
                # Add missing pokemon to list
                while len(selected_pokemon) < self.n_pokemon():
                    new_pokemon = random.choice(list(pokedex_name.keys()))
                    if new_pokemon not in selected_pokemon:
                        selected_pokemon.append(new_pokemon)

                # Remove pokemon if list is full
                selected_pokemon = selected_pokemon[: self.n_pokemon()]

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
                        f"<{page_setup_color}>Page size:\t{self.PAGE_WIDTH_MM}x{self.PAGE_HEIGHT_MM}mm ({self.get_page_description()})</{page_setup_color}>"
                    )
                )
                print_formatted_text(
                    HTML(
                        f"<{page_setup_color}>Outer margin:\t{self.OUTER_MARGIN_MM}mm</{page_setup_color}>"
                    )
                )
                print_formatted_text(
                    HTML(
                        f"<{page_setup_color}>Inner margin:\t{self.INNER_MARGIN_MM}mm</{page_setup_color}>"
                    )
                )
                print_formatted_text(
                    HTML(
                        f"<{page_setup_color}>Font size:\t{self.FONT_SIZE_MM}mm</{page_setup_color}>"
                    )
                )
                print_formatted_text(
                    HTML(
                        f"<{page_setup_color}>Grid:\t\t{self.COLUMNS}x{self.ROWS}</{page_setup_color}>"
                    )
                )

                print_formatted_text(HTML(""))
                print_formatted_text(
                    HTML(f"Select {self.n_pokemon()} Pokémon to print.")
                )
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

                # Print MESSAGES
                for message in self.MESSAGES:
                    print_formatted_text(message)
                self.MESSAGES = []

                user_input = session.prompt("> ")

                if not user_input:
                    break

                if user_input not in pokedex_name.keys():
                    self.MESSAGES.append(
                        HTML("<red>Invalid input. Please try again.</red>")
                    )
                    continue

                if user_input in selected_pokemon:
                    self.MESSAGES.append(
                        HTML("<red>Pokemon already selected. Please try again.</red>")
                    )
                    continue

                selected_pokemon.insert(0, user_input)
                user_selected_pokemon += 1

            except (KeyboardInterrupt, EOFError):
                break

        output_image, exclude_list = pokemon_print_sheet(
            include_list=[pokedex_name[pokemon] for pokemon in selected_pokemon],
            rows=self.ROWS,
            columns=self.COLUMNS,
            page_width_mm=self.PAGE_WIDTH_MM,
            page_height_mm=self.PAGE_HEIGHT_MM,
            outer_margin_mm=self.OUTER_MARGIN_MM,
            inner_margin_mm=self.INNER_MARGIN_MM,
            font_size_mm=self.FONT_SIZE_MM,
        )
        output_image.show()


if __name__ == "__main__":
    app = PokemonColoringPageCLI()
    typer.run(app.run)
