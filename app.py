import os
import random

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter

import config
from utils import get_pokedex, pokemon_print_sheet

# Define a list of suggestions
pokedex, pokedex_name = get_pokedex()
suggestions = pokedex_name.keys()

# Create a prompt session with FuzzyCompleter
word_completer = WordCompleter(suggestions)
fuzzy_completer = FuzzyCompleter(word_completer)
session = PromptSession(completer=fuzzy_completer)


def select_n_random_pokemon(pokemon_list, n=6):
    return random.sample(pokemon_list, n)


# Step 7: Run the prompt session in a loop to continuously accept input
def main():
    rows = config.ROWS
    columns = config.COLUMNS
    page_width = config.PAPER_WIDTH_MM
    page_height = config.PAPER_HEIGHT_MM
    margin = config.MARGIN_MM
    font_size = config.FONT_SIZE_MM
    n_pokemon = rows * columns

    selected_pokemon = select_n_random_pokemon(list(pokedex_name.keys()), n=n_pokemon)
    user_selected_pokemon = 0
    messages = []
    while True:
        try:
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

            # print_formatted_text(HTML("<u><b>Pokémon Print CLI</b></u>"))
            print_formatted_text(HTML(""))
            print_formatted_text(HTML(f"Select {n_pokemon} Pokémon to print."))
            print_formatted_text(HTML("Adding more will replace the last one."))
            # print_formatted_text(HTML("Press <b>Enter</b> to print."))
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

            if user_input not in suggestions:
                messages.append(HTML("<red>Invalid input. Please try again.</red>"))
                continue

            if user_input in selected_pokemon:
                messages.append(
                    HTML("<red>Pokemon already selected. Please try again.</red>")
                )
                continue

            selected_pokemon.insert(0, user_input)
            selected_pokemon = selected_pokemon[:n_pokemon]
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


if __name__ == "__main__":
    main()
