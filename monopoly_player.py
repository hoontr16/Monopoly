from monopoly_exceptions import LoserError
from monopoly_property import Property
from random import shuffle
from monopoly_basic_exp import advprint

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
            self.deeds[other.set].append(other)
            other.owner = self
            return self
            
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
                a = self.game.raise_money(self, self.creditor, other)
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
            
    def __mul__(self, setname):
        if isinstance(setname, str):
            for i in self.deeds[setname]:
                i.pcount = len(self.deeds[setname])        
            return self
        else:
            raise TypeError(f"Property objects do not support multiplication with objects of type {type(setname)}")
        
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