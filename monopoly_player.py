from monopoly_exceptions import LoserError
from monopoly_property import Property
from random import shuffle
from monopoly_basic_exp import advprint
from monopoly_command import Command

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
    def __init__(self, name, turn_order, gamestate, location=0, chance=0, cc=0, wallet=1500, deeds = {}):
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
        self.name = name
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
        else:
            raise TypeError(f'Addition is not supported between instances of Player and {type(other)}')
        
    def __iadd__(self, other):
        #t = type(other)
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
        else:
            raise TypeError(f'Subtraction is not supported between instances of Player and {type(other)}')
        
    def __isub__(self, other):
        #t = type(other)
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
        else:
            raise TypeError(f"Property objects do not support multiplication with objects of type {type(setname)}")
        
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
        a = Command(self, 'choice', "Would you like to buy it?\n")
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
                elif self.wallet < prop.mprice // 10:
                    choice = ''
                    while choice.text not in ('y', 'n'):
                        choice = Command(self.game, 'choice', "You don't have enough money to pay the interest. Would you like to raise money for this? y or n ")
                    if choice.action():
                        advprint(f'You pay the ${prop.mprice // 10} interest')
                        self -= prop.mprice // 10
                    else:
                        prop.owner = None
                        return False
                else:
                    advprint(f'You pay ${prop.mprice // 10} in interest instead')
                    self -= prop.mprice // 10
                    return True
            else:
                return True
        elif self.wallet < prop.mprice // 10:
            choice = ''
            while choice not in ('y', 'n'):
                choice = Command(self.game, 'choice', "You don't have enough money to pay the interest. Would you like to raise money for this? y or n ").text
            if choice.action():
                advprint(f'You pay the ${prop.mprice // 10} interest')
                self -= prop.mprice // 10
            else:
                prop.owner = None
                return False
        else:
            self -= prop.mprice // 10
        return True

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
    players = []
    try:
        p_input = input('Player 1, enter your name: ')
    except:
        advprint('Something went wrong! Please enter a valid string as your name')
    while p_input.lower() != 'stop':
        p_input = p_input.replace(' ', '_')
        p_det = Player(p_input, 0, state)
        if p_input.lower() in protected_words:
            advprint("Invald name")
            continue
        else:
            protected_words.append(p_input.lower())
        players.append(p_det)
        p_input = input(f'Player {len(players) + 1}, enter your name: ')
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