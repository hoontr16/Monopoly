from monopoly_command import Command
from monopoly_boardstate import BoardState
from monopoly_basic_exp import advprint
from jsonsaver import save
                            
def main(pdef=[]):
    current_state = BoardState(pdef)
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
                command = Command(current_state, 'turn', f'\nWhat would {current_state.cp.name} like to do? note: only [roll, jail, build, info, trade, exit, debug, load] are currently implemented ')
                try:
                    a = command.action()
                except (ValueError, TypeError, FileNotFoundError) as e:
                    advprint(e)
                    #command = Command(current_state, 'turn', f'\nWhat would {current_state.cp.name} like to do? note: only [roll, jail, build, exit, debug] are currently implemented ')
                    #a = 'loop'
                    continue
            if a == 'exit':
                break
        if command.text == 'load':
            current_state = a
            continue
        current_state.turntotal += 1
        current_state.turn += 1
        current_state.turn %= len(current_state.players)
        #print(current_state.turn)
        
        
        
        
if __name__ == '__main__':
    #pdef = [Player('hoontr', 0, location=10, deeds={'Brown': [], 'Light Blue': [], 'Pink': [], 'Orange': [], 'Red': [], 'Yellow': [], 'Green': [], 'Dark Blue': [], 'Railroads': [], 'Utilities': []}), Player('ariadne', 1)]
    #pdef[0].inJail = True
    #main(pdef=pdef)
    main()