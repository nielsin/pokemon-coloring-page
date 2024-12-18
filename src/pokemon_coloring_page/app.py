import os
import random
import sys
from functools import wraps
from string import capwords

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing_extensions import Annotated

from .config import Config as config
from .utils import (
    generate_pokemon_coloring_page,
    get_pokedex,
    get_types,
    memory,
    parallel_cache_pokeapi_calls,
    pokemon_id2name,
    pokemon_id2types,
    pokemon_name2id,
)


def command(
    command_name: str = None,
    command_help: str = None,
    command_arg_desc: str = None,
    command_short: str = None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.is_command = True
        wrapper.command_help = command_help
        wrapper.command_short = command_short
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
        self.console = Console()
        self.panel_width = None

    def _n_pokemon(self):
        return self.ROWS * self.COLUMNS

    def _add_message(self, message: str, custom_colors: bool = False):
        if custom_colors:
            self.MESSAGES.append(message)
        else:
            self.MESSAGES.append(Text(message, style=config.COLOR_MESSAGE))

    def _print_messages(self):
        for message in self.MESSAGES:
            self.console.print(message)
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
            new_pokemon = random.choice(list(self.pokedex.keys()))
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

        title = Text("Pokémon ")
        for letter in "COLORING":
            title.append(letter, style=f"color({random.randint(1, 15)})")
        title.append(" page CLI")
        title.style = "bold"

        page_setup = Table(show_header=False, box=None, style=config.COLOR_PAGE_SETUP)
        page_setup.add_column("Option", style=config.COLOR_PAGE_SETUP)
        page_setup.add_column("Value", style=config.COLOR_PAGE_SETUP)

        page_setup.add_row(
            "Page size",
            f"{self.PAGE_WIDTH_MM}x{self.PAGE_HEIGHT_MM}mm ({self._get_page_description()})",
        )
        page_setup.add_row("Outer margin", f"{self.OUTER_MARGIN_MM}mm")
        page_setup.add_row("Inner margin", f"{self.INNER_MARGIN_MM}mm")
        page_setup.add_row("Font size", f"{self.FONT_SIZE_MM}mm")
        page_setup.add_row("Grid", f"{self.COLUMNS}x{self.ROWS}")
        page_setup.add_row("Color", f"{self.COLOR}")
        page_setup.add_row("Crop", f"{self.CROP}")

        selected_text = Text("Selected Pokémon (")
        selected_text.append("auto", style=config.COLOR_UNSELECTED_POKEMON)
        selected_text.append("/")
        selected_text.append("manual", style=config.COLOR_SELECTED_POKEMON)
        selected_text.append("):")

        # Print selected pokemon
        cc = 0
        selected_pokemon = Table(show_header=False, box=None)
        selected_pokemon.add_column("Number")
        selected_pokemon.add_column("Name")
        selected_pokemon.add_column("Types")

        for pokemon_id in self.selected_pokemon:
            color = (
                config.COLOR_SELECTED_POKEMON
                if cc < self.user_selected_pokemon
                else config.COLOR_UNSELECTED_POKEMON
            )
            pokemon_name = capwords(pokemon_id2name(pokemon_id))
            pokemon_types = capwords(", ".join(pokemon_id2types(pokemon_id)))

            selected_pokemon.add_row(
                str(pokemon_id), pokemon_name, pokemon_types, style=color
            )

            cc += 1

        info_table = Table(
            show_header=False,
            show_lines=False,
            show_edge=False,
            caption_justify="left",
        )
        info_table.add_column("Selected Pokémon")
        info_table.add_column("Page setup")

        info_table.add_row(selected_text, "Page setup:")
        info_table.add_row(selected_pokemon, page_setup)

        info = [Padding(info_table, (1, 0))]

        # Filter
        if self.FILTER:
            info_table.caption = (
                f"Filter: [{config.COLOR_HIGHLIGHT}]{capwords(self.FILTER)}[/]"
            )

        info.append(f"Use [{config.COLOR_COMMAND}]:help[/] command for help.")

        info_panel = Panel(Group(*info), title=title, expand=False)

        self.panel_width = info_panel.__rich_measure__(
            self.console, self.console.options
        ).maximum

        self.console.print(info_panel)

    @command("help", command_help="Show help", command_short="h")
    def _help(self, _):
        # Build command description

        table = Table(
            show_header=False,
            box=None,
            title="Available commands:",
            title_justify="left",
        )
        table.add_column("Command")
        table.add_column("Short", style=config.COLOR_COMMAND)
        table.add_column("Description", style=config.COLOR_UNSELECTED_POKEMON)

        for command_name, command_info in self.commands.items():
            command = Text(f":{command_name}", style=config.COLOR_COMMAND)

            if command_info["arg_desc"]:
                command.append(
                    f" {command_info['arg_desc']}",
                    style=config.COLOR_UNSELECTED_POKEMON,
                )

            table.add_row(
                command,
                f":{command_info['short']}" if command_info["short"] else "",
                command_info.get("help", ""),
            )

        msg_list = [
            "The initial list of Pokémon is randomly selected.",
            "You can select others by typing in their name or id.",
            "Adding Pokémon will remove the last Pokémon in the list.",
            Padding(table, (1, 0)),
            f"Press [{config.COLOR_HIGHLIGHT}]Enter[/] with empty prompt to generate coloring page and open in preview window.",
            f"Use [{config.COLOR_COMMAND}]:write[/] to genereate coloring page and save directly to file.",
        ]

        self._add_message(
            Panel(
                Group(*msg_list),
                title="Help",
                width=self.panel_width,
            ),
            custom_colors=True,
        )

    @command("quit", command_help="Quit the CLI app", command_short="q")
    def _quit(self, _):
        sys.exit()

    @command("color", command_help="Toggle color mode")
    def _color(self, _):
        self.COLOR = not self.COLOR

    @command("crop", command_help="Toggle crop mode")
    def _crop(self, _):
        self.CROP = not self.CROP

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
        self.COLOR = self.INITIAL_COLOR
        self.CROP = self.INITIAL_CROP

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

    @command(
        "rows",
        command_arg_desc="number",
        command_help="Set number of rows",
        command_short="r",
    )
    def _set_rows(self, rows: str):
        try:
            self.ROWS = int(rows)
        except ValueError:
            self._add_message("Invalid number of rows. Please try again.")

    @command(
        "columns",
        command_arg_desc="number",
        command_help="Set number of columns",
        command_short="c",
    )
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

    @command("grid_orientation", command_help="Switch grid orientation (transpose)")
    def _rotate_grid(self, _):
        self.ROWS, self.COLUMNS = self.COLUMNS, self.ROWS

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

    @command("types", command_help="List all Pokémon types and their count")
    def _list_types(self, _):
        for type, pokemon in get_types().items():
            self._add_message(f"{capwords(type)} ({len(pokemon)})")

    @command(
        "type_filter",
        command_help="Only Pokémon with specific type. No argument to reset.",
        command_arg_desc="type",
    )
    def _type_filter(self, type_filter: str):
        self.FILTER = None

        if type_filter == "":
            self.pokedex = get_pokedex()
            self._add_prompt_suggestions()
            return

        if type_filter.lower() not in get_types().keys():
            self._add_message("Invalid type. Please try again.")
            return

        if len(get_types()[type_filter.lower()]) < self._n_pokemon():
            self._add_message(
                f"Not enough Pokémon with type: {type_filter}. Please try again."
            )
            return

        self.FILTER = type_filter

        for i in range(self.user_selected_pokemon):
            if type_filter.lower() not in pokemon_id2types(self.selected_pokemon[i]):
                self.user_selected_pokemon -= 1

        self.selected_pokemon = [
            pokemon_id
            for pokemon_id in self.selected_pokemon
            if type_filter.lower() in pokemon_id2types(pokemon_id)
        ]

        self.pokedex = get_pokedex(type_filter=type_filter)
        self._add_prompt_suggestions()

    @command(
        "write",
        command_help="Save the current coloring page to a file",
        command_arg_desc="filename",
        command_short="w",
    )
    def _save(self, filename: str):
        if not filename:
            filename = "pokemon-coloring-page.png"

        output_image = self._generate_coloring_page()
        output_image.save(filename)

        self._add_message(
            f"Coloring page saved to [{config.COLOR_HIGHLIGHT}]{filename}[/]",
            custom_colors=True,
        )

    @command(
        "grid",
        command_help="Set columns and rows in grid",
        command_short="g",
        command_arg_desc="columns rows",
    )
    def _set_grid(self, grid: str):
        try:
            columns, rows = map(int, grid.split(" "))
            self.COLUMNS = columns
            self.ROWS = rows
        except ValueError:
            self._add_message("Invalid grid. Please try again.")

    def _get_commands(self):
        commands = {}
        for name in dir(self):
            attr = getattr(self, name)
            if callable(attr) and hasattr(attr, "is_command"):
                commands[attr.command_name] = {
                    "func": attr,
                    "help": attr.command_help,
                    "arg_desc": attr.command_arg_desc,
                    "short": attr.command_short,
                }
        return commands

    def _add_prompt_suggestions(self):
        # Define a list of suggestions
        suggestions = [capwords(pokemon) for pokemon in self.pokedex.values()]

        # Add commands to suggestions
        suggestions += [f":{command}" for command in self.commands.keys()]

        # List page sizes
        page_sizes = []
        for page_size in config.STANDARD_PAGE_SIZES_MM.keys():
            for orientation in ["Portrait", "Landscape"]:
                page_sizes.append(f":page_size {page_size} {orientation}")

        # List types
        suggestions += [f":type_filter {capwords(type)}" for type in get_types().keys()]

        # Add page sizes to suggestions
        suggestions += page_sizes

        # Create FuzzyCompleter
        word_completer = WordCompleter(suggestions)
        fuzzy_completer = FuzzyCompleter(word_completer)

        # Add fuzzy completer to session
        self.session.completer = fuzzy_completer

    def _generate_coloring_page(self):
        parallel_cache_pokeapi_calls(self.selected_pokemon)
        output_image = generate_pokemon_coloring_page(
            include_list=self.selected_pokemon,
            exclude_list=[],
            rows=self.ROWS,
            columns=self.COLUMNS,
            page_width_mm=self.PAGE_WIDTH_MM,
            page_height_mm=self.PAGE_HEIGHT_MM,
            outer_margin_mm=self.OUTER_MARGIN_MM,
            inner_margin_mm=self.INNER_MARGIN_MM,
            font_size_mm=self.FONT_SIZE_MM,
            color=self.COLOR,
            crop=self.CROP,
        )
        return output_image

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
        color: Annotated[bool, typer.Option(help="Color images")] = config.COLOR,
        crop: Annotated[bool, typer.Option(help="Crop images")] = config.CROP,
        clear_cache: Annotated[bool, typer.Option(help="Clear PokeAPI cache")] = False,
    ):
        """
        Run the Pokémon Coloring Page CLI.
        """

        # Clear cache
        if clear_cache:
            memory.clear()

        # Store initial values
        self.INITIAL_PAGE_WIDTH_MM = page_width
        self.INITIAL_PAGE_HEIGHT_MM = page_height
        self.INITIAL_OUTER_MARGIN_MM = outer_margin
        self.INITIAL_INNER_MARGIN_MM = inner_margin
        self.INITIAL_FONT_SIZE_MM = font_size
        self.INITIAL_ROWS = rows
        self.INITIAL_COLUMNS = columns
        self.INITIAL_COLOR = color
        self.INITIAL_CROP = crop

        # Store values
        self.PAGE_WIDTH_MM = page_width
        self.PAGE_HEIGHT_MM = page_height
        self.OUTER_MARGIN_MM = outer_margin
        self.INNER_MARGIN_MM = inner_margin
        self.FONT_SIZE_MM = font_size
        self.ROWS = rows
        self.COLUMNS = columns
        self.COLOR = color
        self.CROP = crop

        # Other variables
        self.MESSAGES = []
        self.FILTER = None

        # Initialize selected pokemon
        self.selected_pokemon = []
        self.user_selected_pokemon = 0

        # Get commands
        self.commands = self._get_commands()

        # Get pokedex
        self.pokedex = get_pokedex()

        # Create a prompt session
        self.session = PromptSession()
        self._add_prompt_suggestions()

        while True:
            try:
                self._random_select_pokemon()

                self._print_info()
                self._print_messages()

                user_input = self.session.prompt("> ")

                if not user_input:
                    self.console.print(
                        f"[{config.COLOR_HIGHLIGHT}]Generating coloring page...[/]"
                    )

                    output_image = self._generate_coloring_page()
                    output_image.show()

                    self._add_message(
                        f"[{config.COLOR_HIGHLIGHT}]Coloring page generated.[/]",
                        custom_colors=True,
                    )

                    continue

                if user_input.startswith(":"):
                    command_name = user_input[1:].split(" ")[0]
                    command_args = user_input[1 + len(command_name) :].strip()

                    if command_name in self.commands:
                        self.commands[command_name]["func"](command_args)
                    elif command_name in [
                        command["short"] for command in self.commands.values()
                    ]:
                        {
                            command["short"]: command["func"]
                            for command in self.commands.values()
                        }[command_name](command_args)
                    else:
                        self._add_message("Invalid command. Please try again.")
                    continue

                pokemon_id = pokemon_name2id(user_input)

                if not pokemon_id:
                    try:
                        pokemon_id = int(user_input)
                    except ValueError:
                        pass

                if pokemon_id not in self.pokedex.keys():
                    self._add_message("Pokémon not found. Please try again.")
                    continue

                if not pokemon_id:
                    self._add_message("Invalid input. Please try again.")
                    continue

                if pokemon_id in self.selected_pokemon:
                    self._add_message("Pokémon already selected. Please try again.")
                    continue

                self.selected_pokemon.insert(0, pokemon_id)
                self.user_selected_pokemon += 1

            except (KeyboardInterrupt, EOFError):
                break


def main():
    app = PokemonColoringPageCLI()
    typer.run(app.run)
