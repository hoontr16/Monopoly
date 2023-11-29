from monopoly_command import Command
from monopoly_boardstate import BoardState
from monopoly_basic_exp import advprint
from jsonsaver import save, SaveState, LoadError
                            
def main(pdef=[]):
    """ Runs the actual game.
    
    Arguments:
        pdef(list, defaults to empty): an optional predefined list of players.
        
    Side effects:
        calls functions, prints messages, and asks for player input
    """
    mychoice = input("Start a new game, or load an existing save? ").lower()
    t = mychoice.split(maxsplit=1)
    try:
        if t[0] == 'load':
            print("loading")
            while True:
                try:
                    current_state = load_file(t[1])
                except (FileNotFoundError, LoadError) as e:
                    advprint(e)
                    mychoice = input("Start a new game, or load an existing save?").lower()
                    t = mychoice.split(maxsplit=1)   
                    if t[0] != 'load':
                        current_state = BoardState(pdef)
                break
        else:
            current_state = BoardState(pdef)
    except IndexError:
        advprint("exiting")
        return
    #current_state.players = [Player('hoontr', 0, current_state, location=10, deeds={'Brown': [], 'Light Blue': [], 'Pink': [], 'Orange': [], 'Red': [], 'Yellow': [], 'Green': [], 'Dark Blue': [], 'Railroads': [], 'Utilities': []}), Player('ariadne', 1, current_state)]
    #current_state.players[0].inJail = True
    while True:
        current_state.cp = current_state.whose_turn()
        save(current_state)
        if current_state.cp not in current_state.plost:
            if len(current_state.players) - len(current_state.plost) == 1:
                advprint(f'{current_state.cp} wins!')
                break
            a = 'loop'
            while a not in (None, 'exit'):
                command = Command(current_state, 'turn', f'\nWhat would {current_state.cp.name} like to do? note: only [roll, jail, build, info, trade, exit, debug, save, load, unmortgage] are currently implemented ')
                t = command.text.split(maxsplit=1)
                if t[0] == 'save':
                    advprint(f"saving to {t[1]}.json")
                    save(current_state, t[1])
                    continue
                elif t[0] == 'load':
                    break
                try:
                    a = command.action()
                except (ValueError, TypeError) as e:
                    advprint(e)
                    #command = Command(current_state, 'turn', f'\nWhat would {current_state.cp.name} like to do? note: only [roll, jail, build, exit, debug] are currently implemented ')
                    #a = 'loop'
                    continue
            if a == 'exit':
                break
        if t[0] == 'load':
            try:
                current_state = load_file(t[1])
            except FileNotFoundError as e:
                advprint(e)
            continue
        current_state.turntotal += 1
        current_state.turn += 1
        current_state.turn %= len(current_state.players)
        #print(current_state.turn)
        
def load_file(path):
    """ Return the GameState object from loading a save.
    
    Arguments:
        path(str): the path to the file to load from. include file designator
    
    Side effects:
        prints a message if successful
        
    Raises:
        FileNotFoundError if raised by load() method
    
    Returns:
        GameState: the loaded save state
    """
    try:
        cs = SaveState(path)
        lstate = cs.load()
        advprint('load successful')
        return lstate
    except FileNotFoundError as e:
        raise e
        
        
if __name__ == '__main__':
    #pdef = [Player('hoontr', 0, location=10, deeds={'Brown': [], 'Light Blue': [], 'Pink': [], 'Orange': [], 'Red': [], 'Yellow': [], 'Green': [], 'Dark Blue': [], 'Railroads': [], 'Utilities': []}), Player('ariadne', 1)]
    #pdef[0].inJail = True
    #main(pdef=pdef)
    main()