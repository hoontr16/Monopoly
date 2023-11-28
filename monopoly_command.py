from monopoly_basic_exp import roll_dice, advprint
from monopoly_exceptions import LoserError
from jsonsaver import save, SaveState

class Command:
    def __init__(self, state, mytype, prompt):
        self.text = input(f'{prompt}').lower()
        self.state = state
        self.type = mytype
        self.oldtype = None
        if self.text == 'trade':
            self.oldtype = self.type
            self.type = 'trade'
        if self.text[:4] in ('load', 'save'):
            self.oldtype = self.type
            self.type = self.text[:4]
        self.prompt = prompt
        
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
                    z = self.state.improve_property(self.state.cp, current_prop, bcomm[2], self.state)
                    if z == False:
                        choice = ''
                        while choice not in ('y', 'n'):
                            choice = Command(self.state, 'choice', 'Would you like to raise money for this? y or n\n').text
                        if choice.action():
                            self.state.raise_money(self.state.cp, 'the Bank', current_prop.bprice)
                            self.state.improve_property(self.state.cp, current_prop, bcomm[2], self.state)
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
            def parse_offer(offer):
                props = []
                cards = 0
                money = 0
                error = 0
                for i in offer:
                    try:
                        cards = int(i)
                    except ValueError:
                        if i[0] == '$':
                            money = int(i[1:])
                        else:
                            x = self.state.findprop(i)
                            if x:
                                props.append(x)
                            else:
                                advprint("There was an error entering your properties.")
                                error += 1
                return props, cards, money, error
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
            turncount = 0
            while turncount < 3:
                request = Command(self.state, 'property', f"What does {p1} want to trade for?\n")
                rlist = request.text.strip().split(', ')
                while not rlist:
                    request = Command(self.state, 'request', 'Please enter your request, like this: {property1, property2, ...}, ${money}, {GOJF card(s)}\n')
                rprops, rcards, rmoney, rerror = parse_offer(request)
                for r in rprops:
                    if r not in p2.deeds[r.set]:
                        advprint(f"{p2} does not own {r}")
                        rerror += 1
                if rerror:
                    continue
                offer = Command(self.state, 'offering', f"What does {p1} offer?\n")
                olist = offer.text.strip().split(', ')
                while not olist:
                    offer = Command(self.state, 'offering', 'Please enter your offer, like this: {property1, property2, ...}, ${money}, {GOJF card(s)}\n')
                    olist = offer.text.strip().split(', ')
 
                oprops, ocards, omoney, oerror = parse_offer(olist)
                if oerror:
                    continue                
                advprint(f"{p1}'s request:")
                advprint(f"GOJF cards: {rcards}")
                advprint(f'Money: ${rmoney}')
                for prop in rprops:
                    advprint(prop)
                print()
                advprint(f"{p1}'s offerings:")
                advprint(f"GOJF cards: {ocards}")
                advprint(f"Money: ${omoney}")
                for prop in oprops:
                    advprint(prop)
                p2choice = input(f"{p2}, do you accept? Enter either yes, no, or counter\n").strip().lower()
                if p2choice in ('yes', 'y'):
                    try:
                        p1 -= omoney
                        p2 += omoney
                        p2 -= rmoney
                        p2 += omoney
                    except LoserError:
                        return
                    if rcards:
                        if rcards == 2:
                            p1.chance -= 1
                            p1.cc -= 1
                            p2.chance += 1
                            p2.cc += 1
                        elif p1.chance:
                            p1.chance -= 1
                            p2.chance += 1
                        elif p1.cc:
                            p1.cc -= 1
                            p2.cc += 1
                        else:
                            advprint('oops!')
                    if ocards:
                        if ocards == 2:
                            p1.chance += 1
                            p1.cc += 1
                            p2.chance -= 1
                            p2.cc -= 1
                        elif p1.chance:
                            p1.chance += 1
                            p2.chance -= 1
                        elif p1.cc:
                            p1.cc += 1
                            p2.cc -= 1
                        else:
                            advprint('oops!')
                    for prop in oprops:
                        p1 -= prop
                        p2 += prop
                    for r in rprops:
                        p2 -= r
                        p1 += r
                    break
                elif p2choice in ('no', 'n'):
                    advprint("Trade rejected")
                    break
                elif p2choice == 'counter':
                    advprint('Counter offer')
                    p1, p2 = p2, p1
                turncount += 1
            if self.oldtype:
                new = Command(self.state, self.oldtype, self.prompt)
                return new.action()
        elif self.type == 'save':
            t = self.text.split(maxsplit=1)
            advprint('saving state')
            save(self.state, path=t[1])
            if self.oldtype:
                new = Command(self.state, self.oldtype, self.prompt)
                return new.action()
        elif self.type == 'load':
            t = self.text.split()
            advprint('loading state')
            s = SaveState(t[1])
            return s.load()        
        else:
            raise TypeError(f"Commands of type {self.type} do not support the action() method")