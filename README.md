# Monopoly
My implementation of Monopoly in Python, without using Pygame

Arguments required to run:
    human_players (int): how many human players to start with
    computer_players (int): how many computer players to start with
Enter the desired integers after the path when running the program via the command line.

Guide to commands:

    NOT CAPS SENSITIVE

    Starting the game: either enter 'new' or 'load' followed by the filepath to load (see 'saving and loading')

    info: for viewing player positions, balances, and owned properties

        1. enter only 'info'

        2. enter any of (property, properties, position, positions, wallet, wallets)

        3. if asking for info on balances or properties, answer the next command

    choice: any time you are asked a yes or no question

        to accept, enter either 'yes' or 'y'

        to decline, enter either 'no' or 'n'

    when in Jail: enter either 'jail' or 'roll' to begin your jail turn.

        can still trade, just don't enter 'jail' or 'roll' before attempting

        options for escaping jail:
        
            'card': if you have a GOJF card, immediately consumes it and processes your movement.

            'pay': if you have at least $50, immediately charges you and processes your movement.

            'roll': attempt to roll doubles

            if it's your third turn in jail, after entering either 'roll' or 'jail', you will be immediately freed and your movement will be processed

    mortgaging properties:

        enter in this format: "mortgage {full property name}"

        can only mortgage properties to pay off a debt

    selling houses:

        enter in this format: "sell {full property name}"

        can only sell 1 house at a time, and only when the player is paying off a debt

    unmortgaging properties:
    
        1. enter 'unmortgage', either at the beginning of a turn or when recieving a mortgaged property

        2. if at the beginning of a turn: at the next prompt, enter what property to unmortgage

    paying interest: only when recieving a mortgaged property, as an alternative to unmortgaging

        enter 'interest'

        if you cannot afford to pay interest, the property returns to the bank

    entering a dollar amount: just enter an integer

    rolling:

        enter 'roll' to begin your turn

        if you roll doubles, the game will roll for you

    building houses and hotels: only at the start of your turn

        enter in this format: "build, {full name of property}, {number of buildings to build}"

    exiting the game: only at the start of your turn

        enter exit, then 'y' or 'yes' at the next prompt

    debug: for detailed, non-user-friendly information on a player or property's status

        first, enter 'debug'

        at the next prompt, enter either 'player' or 'property', followed by the name of the thing to debug

    trading: can be done at any time, between any two players

        first, enter 'trade'

        then, enter in this format: "{name of player initiating trade} {name of target player}

            entering 'help' instead will print relevant info for all players

            entering either 'stop' or 'exit' here will abort the trade

        then, enter the assets that player1 is asking for from player2, separated by commas and spaces

            IMPORTANT: type a dollar sign before dollar amounts

        then, enter the assets player 1 is offering, separated by commas and spaces

        after printing out the current offer, enter player2's decision. either yes, no, or counter

        if 'no' or 'n', the trade is aborted

        if 'counter': switches the player's positions, and starts over

            this can only happen up to 3 times per trade, so no infinite loops

    saving and loading: whenever the game asks you to roll, you can instead save or load the game

        type either 'save' or 'load', followed by the filepath to save to or load from
