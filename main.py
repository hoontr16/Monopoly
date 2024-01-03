from argparse import ArgumentParser
from time import localtime, time, asctime
import json

if __name__ == '__main__':
    with open('log.txt', 'w') as f:
        f.write(asctime(localtime(time())))
        f.write('\n')
    parser = ArgumentParser()
    parser.add_argument("humans", type=int, help="the number of human players to make")
    parser.add_argument("computers", type=int, help="the number of computer players to make")
    parser.add_argument("-n", type=bool, help="whether to start a new game or ask first", default=True)
    args = parser.parse_args()
    settings = {'printmode': 0, 'humans': args.humans, 'computers': args.computers, 'newgame': args.n}
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)

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
    with open('config.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    if not settings['newgame']:
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
    else:
        current_state = BoardState(pdef)
    #current_state.players = [Player('hoontr', 0, current_state, location=10, deeds={'Brown': [], 'Light Blue': [], 'Pink': [], 'Orange': [], 'Red': [], 'Yellow': [], 'Green': [], 'Dark Blue': [], 'Railroads': [], 'Utilities': []}), Player('ariadne', 1, current_state)]
    #current_state.players[0].inJail = True
    while True:
        current_state.cp = current_state.whose_turn()
        save(current_state)
        if current_state.turntotal / len(current_state.players) > 500:
            print('too long')
            break
        if current_state.cp not in current_state.plost:
            if len(current_state.players) - len(current_state.plost) == 1:
                advprint(f'{current_state.cp} wins!')
                break
            t = 'loop'
            while t not in (None, 'exit'):
                t = current_state.cp.do_turn()
                if t[0] == 'save':
                    try:
                        advprint(f"saving to {t[1]}.json")
                        save(current_state, t[1])
                    except IndexError:
                        advprint("Please enter the word 'save' followed by the file name to save to")
                    continue
                elif t[0] == 'load':
                    break
            if t[0] == 'exit':
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