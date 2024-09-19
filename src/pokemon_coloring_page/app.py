import os
import random
import sys
from functools import wraps

import typer
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from typing_extensions import Annotated

from .config import Config as config
from .utils import get_pokedex, pokemon_print_sheet


def command(
    command_name: str = None, command_help: str = None, command_arg_desc: str = None
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.is_command = True
        wrapper.command_help = command_help
        wrapper.command_arg_desc = command_arg_desc
        if command_name:
            wrapper.command_name = command_name
        else:
            wrapper.command_name = func.__name__
        return wrapper

    return decorator


class PokemonColoringPageCLI:
    """Class for the Pokémon Coloring Page CLI."""

    def __init__(self):
        self.color_page_setup = "gray"
        self.color_selected_pokemon = "green"
        self.color_unselected_pokemon = "gray"
        self.color_message = "red"
        self.color_highlight = "blue"

    def _n_pokemon(self):
        return self.ROWS * self.COLUMNS

    def _add_message(self, message: str, custom_colors: bool = False):
        if custom_colors:
            self.MESSAGES.append(message)
        else:
            self.MESSAGES.append(
                f"<{self.color_message}>{message}</{self.color_message}>"
            )

    def _print_messages(self):
        for message in self.MESSAGES:
            print_formatted_text(HTML(message))
        self.MESSAGES = []

    def _get_page_description(self):
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

    def _random_select_pokemon(self):
        # Add missing pokemon to list
        while len(self.selected_pokemon) < self._n_pokemon():
            new_pokemon = random.choice(list(self.pokedex_name.keys()))
            if new_pokemon not in self.selected_pokemon:
                self.selected_pokemon.append(new_pokemon)

        # Remove pokemon if list is full
        self.selected_pokemon = self.selected_pokemon[: self._n_pokemon()]

        # Reduce user selected pokemon if needed
        self.user_selected_pokemon = min(self.user_selected_pokemon, self._n_pokemon())

    def _print_info(self, clear_screen: bool = True):
        # Clear the screen
        if clear_screen:
            os.system("cls" if os.name == "nt" else "clear")

        # Print page setup
        for line in [
            "<white>Pokémon </white><red>C</red><green>O</green><yellow>L</yellow><blue>O</blue><magenta>R</magenta><cyan>I</cyan><red>N</red><green>G</green><white> page CLI</white>",
            "",
            f"<{self.color_page_setup}>Page size:\t{self.PAGE_WIDTH_MM}x{self.PAGE_HEIGHT_MM}mm ({self._get_page_description()})</{self.color_page_setup}>",
            f"<{self.color_page_setup}>Outer margin:\t{self.OUTER_MARGIN_MM}mm</{self.color_page_setup}>",
            f"<{self.color_page_setup}>Inner margin:\t{self.INNER_MARGIN_MM}mm</{self.color_page_setup}>",
            f"<{self.color_page_setup}>Font size:\t{self.FONT_SIZE_MM}mm</{self.color_page_setup}>",
            f"<{self.color_page_setup}>Grid:\t\t{self.COLUMNS}x{self.ROWS}</{self.color_page_setup}>",
            "",
            f"Use <{self.color_highlight}>:help</{self.color_highlight}> command for help.",
            "",
            f"Selected Pokémon (<{self.color_unselected_pokemon}>auto</{self.color_unselected_pokemon}>/<{self.color_selected_pokemon}>manual</{self.color_selected_pokemon}>):",
        ]:
            print_formatted_text(HTML(line))

        # Print selected pokemon
        cc = 0
        for pokemon in self.selected_pokemon:
            color = (
                self.color_selected_pokemon
                if cc < self.user_selected_pokemon
                else self.color_unselected_pokemon
            )
            print_formatted_text(
                HTML(
                    f"<{color}> >> #{self.pokedex_name[pokemon]:<4} {pokemon}</{color}>"
                )
            )
            cc += 1

    @command("help", command_help="Show help")
    def _help(self, _):
        # Build command description
        command_desc = []
        for command_name, command_info in self.commands.items():
            command_arg_desc = (
                command_info["arg_desc"] if command_info["arg_desc"] else ""
            )
            c = f" <{self.color_selected_pokemon}>:{command_name}</{self.color_selected_pokemon}> <{self.color_unselected_pokemon}>{command_arg_desc}</{self.color_unselected_pokemon}>"

            command_help = command_info["help"] if command_info["help"] else ""
            command_desc.append([c, command_help])

        max_command_len = max([len(c) for c, i in command_desc])
        command_desc = [f"{c:<{max_command_len}}  {i}" for c, i in command_desc]

        msg_list = [
            "",
            "The initial list of Pokémon is randomly selected.",
            "You can select others by typing in their names.",
            "Adding Pokémon will remove the last Pokémon in the list.",
            "Selection is case sensitive, so use autocomplete.",
            "",
            "Available commands:",
            "\n".join(command_desc),
            "",
            f"Press <{self.color_highlight}>Enter</{self.color_highlight}> with empty prompt to generate the coloring page.",
            "",
        ]
        for msg in msg_list:
            self._add_message(msg, custom_colors=True)

    @command("quit", command_help="Quit the CLI app")
    def _quit(self, _):
        sys.exit()

    @command(
        "reset_selection",
        command_help="Clear selection and reselect random Pokémon",
    )
    def _clear(self, _):
        self.selected_pokemon = []
        self.user_selected_pokemon = 0

    @command("reset_page", command_help="Reset page setup")
    def _reset(self, _):
        self.PAGE_WIDTH_MM = self.INITIAL_PAGE_WIDTH_MM
        self.PAGE_HEIGHT_MM = self.INITIAL_PAGE_HEIGHT_MM
        self.OUTER_MARGIN_MM = self.INITIAL_OUTER_MARGIN_MM
        self.INNER_MARGIN_MM = self.INITIAL_INNER_MARGIN_MM
        self.FONT_SIZE_MM = self.INITIAL_FONT_SIZE_MM
        self.ROWS = self.INITIAL_ROWS
        self.COLUMNS = self.INITIAL_COLUMNS

    @command(
        "page_width", command_arg_desc="width", command_help="Set page width in mm"
    )
    def _set_page_width(self, page_width: str):
        try:
            self.PAGE_WIDTH_MM = float(page_width)
        except ValueError:
            self._add_message("Invalid page width. Please try again.")

    @command(
        "page_height", command_arg_desc="height", command_help="Set page height in mm"
    )
    def _set_page_height(self, page_height: str):
        try:
            self.PAGE_HEIGHT_MM = float(page_height)
        except ValueError:
            self._add_message("Invalid page height. Please try again.")

    @command(
        "outer_margin", command_arg_desc="margin", command_help="Set outer margin in mm"
    )
    def _set_outer_margin(self, outer_margin: str):
        try:
            self.OUTER_MARGIN_MM = float(outer_margin)
        except ValueError:
            self._add_message("Invalid outer margin. Please try again.")

    @command(
        "inner_margin", command_arg_desc="margin", command_help="Set inner margin in mm"
    )
    def _set_inner_margin(self, inner_margin: str):
        try:
            self.INNER_MARGIN_MM = float(inner_margin)
        except ValueError:
            self._add_message("Invalid inner margin. Please try again.")

    @command("font_size", command_arg_desc="size", command_help="Set font size in mm")
    def _set_font_size(self, font_size: str):
        try:
            self.FONT_SIZE_MM = float(font_size)
        except ValueError:
            self._add_message("Invalid font size. Please try again.")

    @command("rows", command_arg_desc="number", command_help="Set number of rows")
    def _set_rows(self, rows: str):
        try:
            self.ROWS = int(rows)
        except ValueError:
            self._add_message("Invalid number of rows. Please try again.")

    @command("columns", command_arg_desc="number", command_help="Set number of columns")
    def _set_columns(self, columns: str):
        try:
            self.COLUMNS = int(columns)
        except ValueError:
            self._add_message("Invalid number of columns. Please try again.")

    @command(
        "page_orientation",
        command_help="Switch page orientation between portrait and landscape",
    )
    def _rotate_page(self, _):
        self.PAGE_WIDTH_MM, self.PAGE_HEIGHT_MM = (
            self.PAGE_HEIGHT_MM,
            self.PAGE_WIDTH_MM,
        )

    @command(
        "page_size",
        command_arg_desc="size orientation",
        command_help="Set a standard page size and orientation",
    )
    def _set_page_size(self, page_size: str):
        try:
            orientation = page_size.split(" ")[-1]
            page_size_name = " ".join(page_size.split(" ")[:-1])

            width, height = config.STANDARD_PAGE_SIZES_MM[page_size_name]

            if orientation == "Landscape":
                width, height = height, width

            self.PAGE_WIDTH_MM = width
            self.PAGE_HEIGHT_MM = height

        except KeyError:
            self._add_message("Invalid page size. Please try again.")

    def _get_commands(self):
        commands = {}
        for name in dir(self):
            attr = getattr(self, name)
            if callable(attr) and hasattr(attr, "is_command"):
                commands[attr.command_name] = {
                    "func": attr,
                    "help": attr.command_help,
                    "arg_desc": attr.command_arg_desc,
                }
        return commands

    def _create_prompt_session(self):
        # Define a list of suggestions
        suggestions = list(self.pokedex_name.keys())

        # Add commands to suggestions
        suggestions += [f":{command}" for command in self.commands.keys()]

        # List page sizes
        page_sizes = []
        for page_size in config.STANDARD_PAGE_SIZES_MM.keys():
            for orientation in ["Portrait", "Landscape"]:
                page_sizes.append(f":page_size {page_size} {orientation}")

        # Add page sizes to suggestions
        suggestions += page_sizes

        # Create a prompt session with FuzzyCompleter
        word_completer = WordCompleter(suggestions)
        fuzzy_completer = FuzzyCompleter(word_completer)
        session = PromptSession(completer=fuzzy_completer)

        return session

    def run(
        self,
        page_width: Annotated[
            float, typer.Option(help="Page width in mm")
        ] = config.PAGE_WIDTH_MM,
        page_height: Annotated[
            float, typer.Option(help="Page height in mm")
        ] = config.PAGE_HEIGHT_MM,
        outer_margin: Annotated[
            float, typer.Option(help="Outer margin in mm")
        ] = config.OUTER_MARGIN_MM,
        inner_margin: Annotated[
            float, typer.Option(help="Inner margin in mm")
        ] = config.INNER_MARGIN_MM,
        font_size: Annotated[
            float, typer.Option(help="Font size in mm")
        ] = config.FONT_SIZE_MM,
        rows: Annotated[int, typer.Option(help="Number of rows")] = config.ROWS,
        columns: Annotated[
            int, typer.Option(help="Number of columns")
        ] = config.COLUMNS,
    ):
        """
        Run the Pokémon Coloring Page CLI.
        """

        # Store initial values
        self.INITIAL_PAGE_WIDTH_MM = page_width
        self.INITIAL_PAGE_HEIGHT_MM = page_height
        self.INITIAL_OUTER_MARGIN_MM = outer_margin
        self.INITIAL_INNER_MARGIN_MM = inner_margin
        self.INITIAL_FONT_SIZE_MM = font_size
        self.INITIAL_ROWS = rows
        self.INITIAL_COLUMNS = columns

        # Store values
        self.PAGE_WIDTH_MM = page_width
        self.PAGE_HEIGHT_MM = page_height
        self.OUTER_MARGIN_MM = outer_margin
        self.INNER_MARGIN_MM = inner_margin
        self.FONT_SIZE_MM = font_size
        self.ROWS = rows
        self.COLUMNS = columns
        self.MESSAGES = []

        # Initialize selected pokemon
        self.selected_pokemon = []
        self.user_selected_pokemon = 0

        # Get commands
        self.commands = self._get_commands()

        # Get pokedex
        self.pokedex, self.pokedex_name = get_pokedex()

        # Create a prompt session
        session = self._create_prompt_session()

        while True:
            try:
                self._random_select_pokemon()

                self._print_info()
                self._print_messages()

                user_input = session.prompt("> ")

                if not user_input:
                    print_formatted_text(
                        HTML(
                            f"<{self.color_highlight}>Generating coloring page...</{self.color_highlight}>"
                        )
                    )

                    output_image, exclude_list = pokemon_print_sheet(
                        include_list=[
                            self.pokedex_name[pokemon]
                            for pokemon in self.selected_pokemon
                        ],
                        exclude_list=[],
                        rows=self.ROWS,
                        columns=self.COLUMNS,
                        page_width_mm=self.PAGE_WIDTH_MM,
                        page_height_mm=self.PAGE_HEIGHT_MM,
                        outer_margin_mm=self.OUTER_MARGIN_MM,
                        inner_margin_mm=self.INNER_MARGIN_MM,
                        font_size_mm=self.FONT_SIZE_MM,
                    )
                    output_image.show()

                    self._add_message(
                        f"<{self.color_highlight}>Coloring page generated.</{self.color_highlight}>",
                        custom_colors=True,
                    )

                    continue

                if user_input.startswith(":"):
                    command_name = user_input[1:].split(" ")[0]
                    command_args = user_input[1 + len(command_name) :].strip()

                    if command_name in self.commands:
                        self.commands[command_name]["func"](command_args)
                    else:
                        self._add_message("Invalid command. Please try again.")
                    continue

                if user_input not in self.pokedex_name.keys():
                    self._add_message("Invalid input. Please try again.")
                    continue

                if user_input in self.selected_pokemon:
                    self._add_message("Pokémon already selected. Please try again.")
                    continue

                self.selected_pokemon.insert(0, user_input)
                self.user_selected_pokemon += 1

            except (KeyboardInterrupt, EOFError):
                break


def main():
    app = PokemonColoringPageCLI()
    typer.run(app.run)


if __name__ == "__main__":
    app = PokemonColoringPageCLI()
    typer.run(app.run)
