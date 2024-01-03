from monopoly_exceptions import LoserError
from monopoly_property import Property
from random import shuffle, randrange, choice
from monopoly_basic_exp import advprint
from monopoly_command import Command
import json

class Player:
    """ An object for a Player's current state.
    
    Attributes:
        name (str): the player's chosen name.
        turn (int): what order the player's turn happens per round, as an int from 0 to the amount of players - 1
        loc (int): the player's current location, as an int from 0-39, representing a key in the board_spaces dictionary. defaults to 0
        wallet (int): how much money the player has. Defaults to 1500
        deeds (dict): what properties the player owns. a dict with lists of properties as values and the names of sets as the keys. defaults to a key for every set, with empty lists
        chance (int): the player's current amount of chance Get Out of Jail Free cards. Defaults to 0, should be either 0 or 1
        cc (int): the players' current amount of Community Chest GOJF cards. Defaults to 0, should be either 0 or 1
        inJail (bool): whether the player is in Jail. defaults to False
        jailTurn (int): how many turns the player has spent in Jail. defaults to 0, should be an int from 0-3
        dcount (int): how many doubles the player has rolled in a row. defaults to 0, should be an int from 0-3
        game (GameState): the current game object
    """
    def __init__(self, gamestate, name=None, turn_order=0, location=0, chance=0, cc=0, wallet=1500, deeds = {}, pnum=0):
        """ Initialize a Player object.
        
        Arguments:
        name (str): the player's chosen name.
        turn_order (int): what order the player's turn happens per round, as an int from 0 to the amount of players - 1
        gamestate (GameState): the current game object
        location (int): the player's current location, as an int from 0-39, representing a key in the board_spaces dictionary. defaults to 0
        wallet (int): how much money the player has. Defaults to 1500
        deeds (dict): what properties the player owns. a dict with lists of properties as values and the names of sets as the keys. defaults to a key for every set, with empty lists
        chance (int): the player's current amount of chance Get Out of Jail Free cards. Defaults to 0, should be either 0 or 1
        cc (int): the players' current amount of Community Chest GOJF cards. Defaults to 0, should be either 0 or 1
        
        Side effects:
            sets the Player's attributes.
        """
        self.turn = turn_order
        self.loc = location
        self.wallet = wallet
        self.deeds = {'Brown': [], 'Light Blue': [], 'Pink': [], 'Orange': [], 'Red': [], 'Yellow': [], 'Green': [], 'Dark Blue': [], 'Railroads': [], 'Utilities': []}
        if len(deeds) > 0:
            self.deeds = deeds
        self.chance = chance
        self.cc = cc
        self.inJail = False
        self.jailTurn = 0
        self.dcount = 0
        self.game = gamestate
        self.creditor = 'the Bank'
        
    def count_set(self, setname=None):
        """ Counts how many properties the player owns per set.
        
        Arguments:
            setname (str or None): which set to count, or counts all sets if None. Defaults to None
            
        Returns:
            if setname is not None, returns the len of the appropriate self.deeds value.
            else, returns a dict with set names as keys and the lengths of their lists as values.
        """
        if not setname:
            setcount = {}
            for i in self.deeds:
                setcount[i] = len(self.deeds[i])
            return setcount
        else:
            return len(self.deeds[setname])
        
    def check_full(self, prop):
        if self.count_set(setname=prop.set) == prop.stot:
            return True
        return False
    
    def __repr__(self):
        """ How to represent a Player object.
        
        Returns:
            str: 'Player ' followed by the Player's name attribute.
        """
        return f"Player {self.name}"
    
    def check_lost(self, debt):
        """ Determines whether the Player has any money or available assets.
        
        Arguments:
            Debt (int): how much money the Player owes.
            
        Returns:
            if Player has more money than debt, or can mortgage a property or 
                sell a house, returns None
            else, the Player has lost, returning 1
        """
        for aset in self.deeds.values():
            for p in aset:
                if not p.mstatus or p.bnum:
                    return
        if self.wallet >= debt:
            return 
        return 1

    def __add__(self, other):
        #t = type(other)
        if isinstance(other, int):
            return self.wallet + other
        raise TypeError(f'Addition is not supported between instances of Player and {type(other)}')
        
    def __iadd__(self, other):
        if isinstance(other, int):
            self.wallet += other
            advprint(f"{self.name}'s current balance: ${self.wallet}")
            return self
        elif isinstance(other, Property):
            if other.mstatus:
                advprint("This property is mortgaged.")
                a = self.game.get_mortgaged_prop(self, other)
                if not a:
                    return self
            self.deeds[other.set].append(other)
            other.owner = self
            return self
        else:
            raise TypeError(f"Invalid type: {type(other)}")
            
    def __sub__(self, other):
        #t = type(other)
        if isinstance(other, int):
            return self.wallet - other
        raise TypeError(f'Subtraction is not supported between instances of Player and {type(other)}')
        
    def __isub__(self, other):
        if isinstance(other, int):
            if self - other < 0:
                a = self.raise_money(self.creditor, other)
                if not a:
                    self.game.lose(self, self.creditor)
                    raise LoserError()
                else:
                    self.wallet -= other
            else:
                self.wallet -= other
            advprint(f"{self.name}'s current balance: ${self.wallet}")
            return self
        elif isinstance(other, Property):
            self.deeds[other.set].remove(other)
            return self
        else:
            raise TypeError(f"Invalid type: {type(other)}")
            
    def __mul__(self, setname):
        if isinstance(setname, str):
            for i in self.deeds[setname]:
                i.pcount = len(self.deeds[setname])        
            return self
        raise TypeError(f"Property objects do not support multiplication with objects of type {type(setname)}")
    
    def count_props(self):
        ans = 0
        for i in self.deeds:
            ans += len(self.deeds[i])
        return ans
    
    def process_trade(self, other, gain, loss):
        try:
            other -= gain['money']
            self += gain['money']
            self -= loss['money']
            other += loss['money']
        except LoserError:
            return
        if gain['cards']:
            if gain['cards'] == 2:
                other.chance -= 1
                other.cc -= 1
                self.chance += 1
                self.cc += 1
            elif other.chance:
                other.chance -= 1
                self.chance += 1
            elif other.cc:
                other.cc -= 1
                self.cc += 1
            else:
                advprint('oops!')
        if loss['cards']:
            if loss['cards'] == 2:
                other.chance += 1
                other.cc += 1
                self.chance -= 1
                self.cc -= 1
            elif self.chance:
                other.chance += 1
                self.chance -= 1
            elif self.cc:
                other.cc += 1
                self.cc -= 1
            else:
                advprint('oops!')
        for prop in gain['properties']:
            other -= prop
            self += prop
        for r in loss['properties']:
            self -= r
            other += r
    
class HumanPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'human'
        if not kwargs.get('name', False):
            while True:
                try:
                    p_input = input(f"Player {kwargs.get('pnum', 0)}, enter your name: ")
                    p_input = p_input.replace(' ', '_')
                    if p_input.lower() in protected_words:
                        advprint("Invald name")
                        continue
                    self.name = p_input
                    break
                except:
                    advprint('Something went wrong! Please enter a valid string as your name')
        else:
            self.name = kwargs['name']
            
    def jail_turn(self):
        while True:
            pchoice = Command(self.game, 'jail', "You're in Jail. Would you like to roll, use a GOJF card, or pay the fine?\n")
            while pchoice.text not in ('roll', 'card', 'pay'):
                advprint("Please enter either 'roll', 'card', or 'pay'")
                pchoice = Command(self.game, 'jail', "You're in Jail. Would you like to roll, use a GOJF card, or pay the fine?\n")
                continue
            if pchoice.text == 'roll':
                return 'roll'
            elif pchoice == 'card':
                if self.chance:
                    return 'chance'
                elif self.cc:
                    return 'cc'
                else:
                    advprint(f"{self} does not have an GOJF cards")
                    continue
            else:
                advprint("You pay the $50 fine and leave Jail.")
                return 'pay'
    
    def bid(self, auc):
        x = Command(auc.state, 'money', f"{self.name}, what is your bid? Current bid: ${auc.cbid}\n")
        try:
            return x.action()
        except ValueError:
            return x.text
        
    def buy_choice(self, prop):
        a = Command(self.game, 'choice', "Would you like to buy it?\n")
        return a.action()

    def raise_money(self, other_p, debt):
        """ Handle the liquidation of player assets. 
        
        Arguments:
            p (Player): the player who's raising money
            other_p (Player, str): the entity owed. either another player or the Bank
            debt (int): how much money p owes.
        
        Side effects:
            asks for player input on what to sell/mortgage
            prints error messages if applicable
            calls functions, or adds money to p's wallet after a sell/mortgage
            
        Returns:
            None: if p has no more assets to liquidate and cannot pay their debt
            Int: otherwise, returns debt
        """
        advprint(f"{self} owes {other_p} ${debt}")
        def check_options():
            """ Display the player's assets.
            
            Arguments:
                p (Player): the player raising money.
                
            Side effects:
                prints p's available assets and their sell/mortgage price
            """
            advprint('Here are your assets:')
            advprint()
            advprint(f"Your current balance: ${self.wallet}")
            for s in self.deeds:
                for prop in s:
                    if prop.bnum:
                        advprint(f"{prop} : {'hotel' if prop.bnum == 5 else f'{prop.bnum} houses'}, sell price: ${prop.bprice // 2}")
                    else:
                        advprint(f"{prop} : {'Mortgaged' if prop.mstatus else f'Unmortgaged, mortgage price: ${prop.mprice}'}")
        while self.wallet < debt:
            if self.check_lost(debt):
                advprint("You lose!")
                return
            check_options()
            c = Command(self.game, 'poor', "What would you like to do?\n")
            ctype, pname = c.action()
            if ctype not in ('mortgage', 'sell'):
                advprint("Please enter either 'mortgage' or 'sell', followed by the property you choose")
                continue
            cprop = self.game.find_prop(pname)
            if cprop == None:
                continue
            if ctype == 'mortgage':
                cprop.mortgage()
            else:
                n = 0
                for i in self.deeds[cprop.set]:
                    if i.bnum > cprop.bnum:
                        if i.bnum == 5:
                            advprint(f'Houses must be sold evenly across a set. {i} has a hotel, while {cprop} has {cprop.bnum} houses')
                        else:
                            advprint(f'Houses must be sold evenly across a set. {i} has {i.bnum} houses, while {cprop} has {cprop.bnum}')
                        n += 1
                if not n:
                    try:
                        self += cprop.sell_house()
                    except:
                        continue
        return debt

    def get_mortgaged_prop(self, prop):
        if not prop.mstatus:
            raise ValueError("This property is not mortgaged")
        prop.owner = self
        c = Command(self.game, 'rich', f"{self.name}, would you like to unmortgage {prop}, or pay 10% interest? Enter either 'unmortgage' or 'interest': ")
        while True:
            try:
                c1 = c.action()
                break
            except:
                advprint("Please enter either 'unmortgage' or 'interest'")
                c = Command(self.game, 'rich', f"{self.name}, would you like to unmortgage {prop}, or pay 10% interest? Enter either 'unmortgage' or 'interest': ")
        if c1:
            mstat = prop.unmortgage()
            if not mstat:
                choice = ''
                while choice.text not in ('y', 'n'):
                    choice = Command(self.game, 'choice', 'Would you like to raise money for this? y or n ')
                choice = choice.action()
                if choice:
                    self.raise_money('the Bank', prop.mprice)
                    prop.unmortgage()
                elif self.wallet < prop.iprice:
                    choice = ''
                    while choice.text not in ('y', 'n'):
                        choice = Command(self.game, 'choice', "You don't have enough money to pay the interest. Would you like to raise money for this? y or n ")
                    if choice.action():
                        advprint(f'You pay the ${prop.iprice} interest')
                        self -= prop.iprice
                    else:
                        prop.owner = None
                        return False
                else:
                    advprint(f'You pay ${prop.iprice} in interest instead')
                    self -= prop.iprice
                    return True
            else:
                return True
        elif self.wallet < prop.iprice:
            choice = ''
            while choice not in ('y', 'n'):
                choice = Command(self.game, 'choice', "You don't have enough money to pay the interest. Would you like to raise money for this? y or n ").text
            if choice.action():
                advprint(f'You pay the ${prop.iprice} interest')
                self -= prop.mprice // 10
            else:
                prop.owner = None
                return False
        else:
            self -= prop.iprice
        return True    

    def trade(self, other):
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
                        x = self.game.findprop(i)
                        if x:
                            props.append(x)
                        else:
                            advprint("There was an error entering your properties.")
                            error += 1
            return props, cards, money, error
        request = input(f"What does {self} want to trade for?\n")
        rlist = request.strip().split(', ')
        while not rlist:
            request = input('Please enter your request, like this: {property1, property2, ...}, ${money}, {GOJF card(s)}\n')
            rlist = request.strip().split(', ')
        rprops, rcards, rmoney, rerror = parse_offer(request)
        for r in rprops:
            if r not in other.deeds[r.set]:
                advprint(f"{other} does not own {r}")
                rerror += 1
        if rerror:
            return
        offer = input(f"What does {self} offer?\n")
        olist = offer.strip().split(', ')
        while not olist:
            offer = input('Please enter your offer, like this: {property1, property2, ...}, ${money}, {GOJF card(s)}\n')
            olist = offer.strip().split(', ')
        oprops, ocards, omoney, oerror = parse_offer(olist)
        for o in oprops:
            if o not in self.deeds[o.set]:
                advprint(f"You do not own {o}")
                oerror += 1
        if oerror:
            return         
        rtotal = {'properties': rprops, 'money': rmoney, 'cards': rcards}
        ototal = {'properties': oprops, 'money': omoney, 'cards': ocards}                
        other.evaluate_offer(self, rtotal, ototal)

    def evaluate_offer(self, other, request, offer):
        advprint(f"Trade offer from {other}!")
        advprint(f"{other}'s request:")
        advprint(f"GOJF cards: {request['cards']}")
        advprint(f"Money: ${request['money']}")
        for prop in request['properties']:
            advprint(prop)
        print()
        advprint(f"{other}'s offerings:")
        advprint(f"GOJF cards: {offer['cards']}")
        advprint(f"Money: ${offer['money']}")
        for prop in offer['properties']:
            advprint(prop)        
        c = input("Do you accept this offer? Yes, no, or counter\n").lower()
        while c not in ('yes', 'no', 'counter'):
            c = input("Do you accept this offer? Yes, no, or counter\n").lower()
        if c == 'yes':
            self.process_trade(other, offer, request)
        elif c == 'no':
            print("Trade cancelled")
        else:
            self.trade(other)
        
    def do_turn(self):
        command = Command(self.game, 'turn', f'\nWhat would {self} like to do? note: only [roll, jail, build, info, trade, exit, debug, save, load, unmortgage] are currently implemented ')
        t = command.text.split(maxsplit=1)
        if t[0] == 'save':
            return t
        elif t[0] == 'load':
            return t
        try:
            command.action()
            while command.text in ('info', 'debug'):
                command = Command(self.game, 'turn', f'\nWhat would {self} like to do? note: only [roll, jail, build, info, trade, exit, debug, save, load, unmortgage] are currently implemented ')
                command.action()
            return 'exit'
            #return command.text.split(maxsplit=1)
        except (ValueError, TypeError) as e:
            advprint(e)
    

    def improve_property(self, bprop, bcount:str):
        """ Handles the logic for improving properties.
            Args:
                builder (player): the player trying to improve their property.
                bprop (property): the property being improved.
                bcount (str, either '1' or '2'): how many buildings to build.
            Side effects:
                Prints error messages if the player cannot improve this property
                Prints how much this purchase costs
                Updates bprop.bnum appropriately, and subtracts the build cost from 
                    builder's balance
                Prints builder's new balance
            Returns:
                None: If one of the following is True:
                    bprop is a railroad or utility
                    bcount is not a number
                    bprop already has the max number of buildings
                    builder doesn't have enough money
                    builder doesn't own the full color set
                    any property in the set is mortgaged
                    this property would have two improvements more than the member
                        of its set with the least number of improvements
                str: If the purchase is successful
        """
        if bprop.set in ['Railroads', 'Utilities']:
            advprint("That property can't be improved")
            return
        try:
            bcount1 = int(bcount)
        except:
            advprint("Please enter an integer for the number of buildings")
            return
        if bprop.bnum == 5:
            advprint(f"{bprop.name} already has a hotel!")
            return
        if self.wallet < bprop.bprice * bcount1:
            advprint("You don't have enough money!")
            return False
        if self.count_set(setname=bprop.set) != bprop.stot:
            advprint("You don't own the full set!")
            return
        else:
            for i in self.deeds[bprop.set]:
                if i.mstatus == True:
                    advprint("One of the properties in this set is mortgaged.")
                    return
                if bprop.bnum + bcount1 > i.bnum + 1 and bprop != i:
                    advprint(f"You must build evenly across a set. {bprop.name} has {bprop.bnum} houses, while {i.name} only has {i.bnum}. You cannot build {bcount1} houses on {bprop.name}")
                    return
        choice = Command(self, 'choice', f"This will cost ${bprop.bprice * bcount1}. Are you sure? Enter y or n\n")
        if not choice.action():
            advprint('Purchase cancelled')
            return
        x = bprop.build_house(num=bcount1)
        self -= x
        return 'yay'    

class ComputerPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mort_priority = ('Utilities', 'Brown', 'Dark Blue', 'Light Blue', 'Pink', 'Green', 'Railroads', 'Yellow', 'Orange', 'Red')
        self.house_sell_priority = ('Brown', 'Light Blue', 'Yellow', 'Dark Blue', 'Green', 'Pink', 'Orange', 'Red')
        self.build_priority = ('Red', 'Orange', 'Yellow', 'Pink', 'Light Blue', 'Dark Blue', 'Green', 'Brown')
        self.name = f"Computer {kwargs.get('pnum', 0)}"
        self.type = 'ai'
    
    def jail_turn(self):
        if self.chance:
            return 'chance'
        elif self.cc:
            return 'cc'
        elif (self.game.turntotal / len(self.game.players) < 5\
            or sum(self.count_set().values()) < 5) and self.game.turntotal / len(self.game.players) < 15:
            return 'pay'
        else:
            return 'roll'
        
    def calc_high_bid(self, prop):
        bal_lim = int(self.wallet / 10)
        setfactor = 1
        minbaladjust = 200
        if self.wallet < minbaladjust:
            setfactor *= 0.75
        if len(self.deeds[prop.set]):
            setfactor *= 4/3
        if len(self.deeds[prop.set]) + 1 == prop.stot:
            setfactor *= 2
        pricefactor = prop.price * setfactor
        price_lim = min(self.wallet - 50, pricefactor)
        maxbid = round(max(bal_lim, price_lim), ndigits=-1)
        return randrange(maxbid - 30, maxbid + 40, step=10)

    def bid(self, auc):
        maxbid = self.calc_high_bid(auc.prop)
        for i in range(10, maxbid + 1, 10):
            if i > auc.cbid:
                return i
        return 'exit'
    
    def buy_choice(self, prop):
        if prop.price < self.wallet - 50:
            return True
        return False
    
    def get_assets(self):
        mlist = []
        for s in self.mort_priority:
            for p in self.deeds[s]:
                mlist.append(p) if p.bnum == 0 else None
        mlist.sort(key=lambda c: self.mort_priority.index(c.set))
        mlist.sort(key=lambda c: (c.stot - c.pcount) / c.stot, reverse=True)
        hlist = []
        for s in self.house_sell_priority:
            if len(self.deeds[s]) == 0:
                continue
            if self.deeds[s][0].bnum:
                hlist.append(s)
        hlist.sort(key=lambda c: self.deeds[c][0].bnum)
        return mlist, hlist
    
    def raise_money(self, creditor, debt):
        mlist, hlist = self.get_assets()
        while self.wallet < debt:
            if mlist:
                mlist.pop(0).mortgage()
            elif hlist:
                h = hlist.pop(0)
                for i in self.deeds[h]:
                    i.sell_house()
            else:
                advprint(f"{self} has lost!")
                return
        return debt
    
    def to_unmortgage(self):        
        mlist = []
        for s in self.mort_priority[::-1]:
            for p in self.deeds[s]:
                mlist.append(p) if p.mstatus == True else None
        mlist.sort()
        for p in mlist:
            if self.wallet > p.mprice * 2.5:
                p.unmortgage()
                
    def get_mortgaged_prop(self, prop):
        if not prop.mstatus:
            raise ValueError("This property is not mortgaged")
        prop.owner = self
        if self.count_set(setname=prop.set) + 1 == prop.pcount:
            target = prop.mprice * 2
        else:
            target = prop.mprice * 2.5
        if self.wallet >= target:
            prop.unmortgage()
        else:
            try:
                self -= prop.iprice
            except LoserError:
                return
    
    def to_build(self):
        #add check for incompleteness
        adjustments = {}
        check = False
        for i in self.build_priority:
            try:
                prop = self.deeds[i][0]
                adjustments[i] = prop.bnum
            except IndexError:
                continue
        priority_adj = sorted(self.build_priority, key=lambda c: adjustments.get(c, 0), reverse=True)
        for j in priority_adj:
            try:
                prop = self.deeds[j][0]
                if self.count_set(setname=prop.set) != prop.stot or prop.bnum == 5:
                    continue
                for i in self.deeds[prop.set]:
                    if i.mstatus == True:
                        continue
                    if prop.bnum > i.bnum and prop != i:
                        continue           
                if self.wallet > 2 * prop.bprice * prop.stot:
                    for i in self.deeds[prop.set]:
                        i.build_house()
                    check = True
            except IndexError:
                continue
        return check
                
    def get_interest(self, prop):
        if prop.set in ('red', 'orange'):
            return 'yes'
        if len(self.deeds[prop.set]):
            return True
    
    def evaluate_offer(self, other, request, offer):
        if self.game.turntotal / self.game.players < 10:
            return False
        if not offer.get('properties', 0):
            return False
        if not offer.a.get('properties', 0):
            for i in offer['properties']:
                if self.get_interest(i):
                    self.eval_trade(other, request, offer)
                    return
        else:
            self.evaluate_offer(offer)
    
    def eval_trade(self, other, request, offer):
        def count_set(o, setname):
            ans = 0
            for i in o:
                if i.set == setname:
                    ans += 1
            return ans
        if self.count_props - len(request['properties']) + len(offer['properties']) < 6:
            return False
        oval_raw = offer['money']
        oval_raw += offer['cards'] * 40
        offer_value = oval_raw
        offer_value *= 1.2 if self.count_props() < 6 else 1
        for prop in offer['properties']:
            pval = prop.price
            if self.count_set(setname=prop.set) + count_set(offer, prop.set) == prop.stot:
                pval *= 1.5
            if self.count_set(setname=prop.set) + count_set(offer, prop.set) > 1:
                pval *= 1.1
            if prop.set in ('Utilities', 'Green'):
                pval *= 0.9
            if prop.set in ('Red', 'Orange'):
                pval *= 1.05
            if prop.mstatus:
                pval *= 0.5
            offer_value += pval
        if offer_value < 1.5 * oval_raw:
            return False
        rval_raw = request['money']
        rval_raw += request['cards'] * 40
        request_value = rval_raw
        request_value *= 1.2 if self.count_props() < 6 else 1
        for prop in request['properties']:
            if prop.pcount == prop.stot:
                return False
            pval = prop.price
            if self.count_set(setname=prop.set) > 1:
                pval *= 1.1
            if prop.set in ('Utilities', 'Green'):
                pval *= 0.9
            if prop.set in ('Red', 'Orange'):
                pval *= 1.05
            if prop.mstatus:
                pval *= 0.5
            request_value += pval
        if offer_value > request_value:
            advprint("Trade accepted")
            self.process_trade(other, offer, request)
        else:
            advprint("Trade cancelled")

    def choose_target(self):
        candidates = []
        for s in self.deeds:
            for p in self.deeds[s]:
                if p.stot - p.pcount == 1 and p.set not in candidates:
                    candidates.append(p)
        if len(candidates) == 0:
            return False
        return candidates

    def trade(self, other=None):
        candidates = self.choose_target()
        if not candidates:
            return
        shuffle(candidates)
        for k in candidates:
            for i in self.game.players:
                if i != self and i.count_set(setname=k.set):
                    target = i.deeds[k.set][0]
                    for j in i.deeds:
                        ocount = i.count_set(setname=j)
                        scount = self.count_set(setname=j)
                        if ocount >= scount and scount != 0 and ocount + scount == self.deeds[j][0].stot:
                            offer = self.deeds[j][0]
                            break
                    try:
                        money = 0
                        if target.price > offer.price * 1.5:
                            money = target.price - (offer.price * 1.5) + 20
                        elif offer.price > target.price * 1.5:
                            money = offer.price - (target.price * 1.5) + 20
                        ototal = {'properties': [offer], 'money': money}
                        rtotal = {'properties': [target], 'money': money}
                        target.owner.evaluate_offer(self, rtotal, ototal)
                        return
                    except:
                        break

    def to_trade(self):
        for i in self.deeds:
            if self.count_set(setname=i):
                for p in self.game.players:
                    if p.count_set(setname=i):
                        return True
        
    def move(self):
        self.game.cp.dcount = 0
        x = self.game.move()
        while x.doubles == 'doubles':
            x = self.game.move()        
    
    def do_turn(self):
        if self.to_trade():
            self.trade()
        self.to_build()
        self.to_unmortgage()
        self.move()
        return 'exit'

def make_players(state):
    """ Makes player objects for however many players there are, and determines
    turn order.
    
    Arguments:
        state (GameState): the current game
    
    Side effects:
        prints messages asking for player input.
        
    Returns:
        players (list): a list of every player object, in their turn order
    """
    with open('config.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    players = []
    for i in range(settings['humans']):
        p_det = HumanPlayer(state, pnum=i + 1)
        protected_words.append(p_det.name)
        players.append(p_det)
    for i in range(settings['computers']):
        c = ComputerPlayer(state, pnum=i + 1) # add args
        players.append(c)
    shuffle(players)
    x = 0
    for i in players:
        i.turn = x
        x += 1
        advprint(i.name, i.turn)
    return players

protected_words = ['player', 'property', 'railroad', 'utility', 'input', 'print',
                   'advprint', 'players', 'self', 'set', 'list', 'str', 'dict', 
                   'repr', 'copy', 'save', 'savestate']
