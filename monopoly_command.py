from monopoly_basic_exp import roll_dice, advprint
from monopoly_exceptions import LoserError

class Command:
    def __init__(self, state, mytype, prompt):
        self.text = input(f'{prompt}').lower()
        self.state = state
        self.type = mytype
        self.oldtype = None
        if self.text == 'trade':
            self.oldtype = self.type
            self.type = 'trade'
        self.prompt = prompt
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{prompt}: {self.text}")
        
    def action(self):
        if self.text == 'info':
            t = Command(self.state, 'com_int', "Properties, positions, or wallets?")
            if t.text in ('property', 'properties', 'wallet', 'wallets'):
                c = Command(self.state, 'com_int', "Of yourself or all players? Enter either 'self' or 'all'")
                if c.text == 'self':
                    if t.text in ('property', 'properties'):
                        advprint(self.state.cp.deeds)
                    elif t.text in ('wallet', 'wallets'):
                        advprint(f'${self.state.cp.wallet}')
                    else:
                        raise ValueError('unrecognized command')
                elif t.text in ('property', 'properties'):
                    for p in self.state.players:
                        advprint(f"{p}: {p.deeds}\n")
                elif t.text in ('wallet', 'wallets'):
                    for p in self.state.players:
                        advprint(f"{p}: ${p.wallet}\n")
                else:
                    raise ValueError('unrecognized command')
            elif t.text in ('position', 'positions', 'location', 'locations'):
                for p in self.state.players:
                    advprint(f"{p} is on {self.state.board[p.loc]}\n")
            else:
                raise ValueError('unrecognized command')
        elif self.type == 'choice':
            if self.text in ('yes', 'y'):
                return True
            elif self.text in ('no', 'n'):
                return False
        elif self.type == 'jail':
            if self.text == 'roll':
                return roll_dice()
            elif self.text == 'card':
                if self.state.cp.chance or self.state.cp.cc:
                    return True
                else:
                    return False
            elif self.text == 'pay':
                return '$'
            else:
                raise ValueError('unrecognized command')
        elif self.type == 'poor':
            if self.text in ('mortgage', 'sell'):
                return self.text.strip().split(maxsplit=1)
            else:
                raise ValueError('unrecognized command')
        elif self.type == 'rich':
            if self.text == 'unmortgage':
                return True
            elif self.text == 'interest':
                return False
            else:
                raise ValueError('unrecognized command')
        elif self.type == 'money':
            try:
                return int(self.text)
            except:
                raise ValueError('unrecognized command')
        elif self.type == 'turn':
            if self.text in ('roll', 'jail', 'build', 'exit', 'debug', 'unmortgage'):
                if self.text == 'jail':
                    if not self.state.cp.inJail:
                        advprint("You aren't in Jail!")
                    else:
                        self.text = 'roll'
                        #return self.action()
                if self.text == 'roll':
                    self.state.cp.dcount = 0
                    x = self.state.move()
                    while x.doubles == 'doubles':
                        advprint('doubles!')
                        #current_state.cp.dcount += 1
                        x = self.state.move()
                elif self.text[:5] == 'build':
                    bcomm = self.text.split(', ')
                    if len(bcomm) == 1:
                        advprint("To improve a property, use this format: 'build', property, # of buildings")
                        return 'loop'
                    current_prop = self.state.find_prop(bcomm[1])
                    z = self.state.cp.improve_property(current_prop, bcomm[2])
                    if z == False:
                        choice = ''
                        while choice not in ('y', 'n'):
                            choice = Command(self.state, 'choice', 'Would you like to raise money for this? y or n\n').text
                        if choice.action():
                            self.state.raise_money(self.state.cp, 'the Bank', current_prop.bprice)
                            self.state.cp.improve_property(current_prop, bcomm[2])
                    return 'loop'
                elif self.text == 'exit':
                    if Command(self.state, 'choice', 'Are you sure you want to exit? y or n ').text == 'y':
                        return self.text
                    else:
                        return 'loop'
                elif self.text == 'debug':
                    while True:
                        x = input('what to debug?').strip().split(maxsplit=1)
                        if x[0] == 'player':
                            for i in self.state.players:
                                if i.name.lower() == x[1].lower():
                                    advprint(i.name, i.turn, i.loc, i.wallet, i.deeds, i.chance, i.cc, i.inJail, i.jailTurn)
                                    break
                        elif x[0] == 'property':
                            cs = self.state.find_prop(x[1])
                            if cs:
                                advprint(cs.name, cs.set, cs.stot, cs.price, cs.mprice, cs.mstatus, cs.rent, cs.bprice, cs.bnum)
                        elif x[0] == 'exit':
                            break
                        else:
                            continue
                    return 'loop'
                elif self.text == 'unmortgage':
                    x = input("What property would you like to unmortgage?")
                    prop = self.state.find_prop(x)
                    self.state.get_mortgaged_prop(self.state.cp, prop)
                    new = Command(self.state, self.type, self.prompt)
                    return new.action()
                else:
                    raise ValueError("Unrecognized command")
            else:
                raise ValueError('unrecognized command')
        elif self.type == 'trade':
            p_input = Command(self.state, '', 'Who wants to trade?\n')
            pnames = p_input.text.strip().split()
            if len(pnames) == 1:
                if pnames[0].lower() == 'help':
                    for i in self.state.players:
                        advprint(i.name, i.wallet, i.deeds, f'GOJF cards: {i.chance + i.cc}')
                elif pnames[0].lower() in ('stop', 'exit'):
                    advprint('Exiting')
                    return 'loop'
                else:
                    advprint('Please enter the players in this format: {player1} {player2}')
                return 'loop'
            for i in self.state.players:
                if i.name.lower() == pnames[0].lower():
                    p1 = i
                elif i.name.lower() == pnames[1].lower():
                    p2 = i
            p1.trade(p2)
            if self.oldtype:
                new = Command(self.state, self.oldtype, self.prompt)
                return new.action()
        else:
            raise TypeError(f"Commands of type {self.type} do not support the action() method")