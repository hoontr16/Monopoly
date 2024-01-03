from monopoly_command import Command
from monopoly_property import board_spaces
from monopoly_cards_exp import chance, community_chest as cc
from random import shuffle
from monopoly_basic_exp import roll_dice, advprint

class Deck:
    """ A class for the decks of Chance & Community Chest cards.
    
    Attributes:
        deck (dict): a dictionary of the card's indices and their text
        type (str): whether self is a Chance or Community Chest deck
        order (list): a list of deck's keys, in their shuffled order.
    """
    def __init__(self, mytype, pdef=[]):
        """ Initialize a Deck object.
        
        Arguments:
            type (str): either Chance or Community Chest
            
        Side effects:
            shuffles the order of the deck, and sets attributes
        """
        if not pdef:
            if mytype == 'chance':
                k = list(chance.items())
                shuffle(k)
                self.deck = dict(k)
                self.type = 'chance'
            else:
                k = list(cc.items())
                shuffle(k)
                self.deck = dict(k)
                self.type = 'cc'
            self.order = list(self.deck.keys())
        else:
            if mytype == 'chance':
                self.deck = pdef
                self.type = 'chance'
            else:
                self.deck = pdef
                self.type = 'cc'
            self.order = list(self.deck.keys())            
        
    def __str__(self):
        return f"{'Chance' if self.type == 'chance' else 'Community Chest'} deck. Cards left: {len(self.order)}"
    
    def __repr__(self):
        return f"<{self.type} Deck object with cards {self.deck}>"
        
    def draw_card(self):
        """ Draw a card.
        
        Side effects:
            pops the first item off both the order and deck attributes
        
        Returns:
            int, str: the index and text of the drawn card.
        """
        ind = self.order.pop(0)
        text = self.deck.pop(ind)
        return ind, text
    
    def refresh(self, taken=None):
        """ Reshuffles the deck after all cards have been drawn.
        
        Arguments:
            taken (Bool, None): whether the deck's Get Out of Jail Free card is
                currently held by a player. defaults to None
                
        Side effects:
            creates a new deck and order attribute with a newly shuffled deck.
            if taken, removes the GOJF card from the deck
        """
        if self.type == 'chance':
            k = list(chance.items())
            shuffle(k)
            self.deck = dict(k)
            if taken:
                del k[7]            
        else:
            k = list(cc.items())
            shuffle(k)
            self.deck = dict(k)
            if taken:
                del k[4]
        self.order = list(self.deck.keys()) 
    
    def __len__(self):
        return len(self.deck)

class Movement:
    """ A class representing a player's roll and movement.
    
    Attributes:
        p (Player): the player moving
        doubles (None, bool): whether the player rolled doubles to move
        new (int): the index of the space the player is moving to
        nspace (str, Property): the space in the board_spaces dict, at the index
            of self.new
    """
    def __init__(self, player, new_loc = None):
        """ Initialize a Movement object and prepare the player's move.
        
        Arguments:
            player (Player): the player moving
            new_loc (int, None): the space the player is moving to. if None, 
                rolls dice to determine the space. defaults to None
                
        Side effects:
            sets attributes using the arguments and a dice roll
            if dice are rolled, prints a message
        """
        self.p = player
        self.doubles = None
        if new_loc == None:
            self.new, self.doubles = roll_dice()
            ending = ''
            if self.new in (8, 11):
                ending = 'n'
            if not player.inJail:
                advprint(f"{self.p.name} rolled a{ending} {self.new}")
            self.new = (self.new + self.p.loc) % 40
            #advprint(self.p.loc)
        else:
            self.new = new_loc
        self.nspace = board_spaces[self.new]
        #advprint(self.new, self.nspace)
    
    def check_go(self, old_space, new_space):
        """ Gives the player money for passing Go.
            Args:
                old_space (int): the index of the space the player was on before 
                    their last move
                new_space (int): the index of the player's current space
            Side effects:
                If the player's board position passed through position 0, gives the player $200
                prints a message saying so
        """
        if old_space > new_space and new_space - old_space != -3:
            advprint('You passed Go!') 
            ##sleep(0.5)
            self.p += 200

    def move(self):
        """ Move the player.
        
        Side effects:
            checks whether the player has passed Go
            changes the player's location to match self.new
            prints where the player landed
        """
        self.check_go(self.p.loc, self.new)        
        self.p.loc = self.new
        #self.p.loc %= 40
        advprint(f"{self.p.name} landed on {self.nspace}!")
        
class Auction:
    """ An auction.
    
    Attributes:
        prop (Property): the property being auctioned
        p (set): the Players participating in the auction
        done (set): the Players not participating in the auction
        cbid (int): the current highest bid
        cp (Player, None): the Player with the highest bid
    """
    def __init__(self, property, players, state):
        """ Initialize an Auction.
        
        Arguments:
            property (Property): the property being auctioned
            players (list): the Players currently in the game
            
        Side effects:
            sets Auction attributes
        """
        self.prop = property
        self.p = set(players)
        self.done = set()
        self.cbid = 0
        self.cp = None
        self.state = state
    
    def abid(self, player):
        """ Processes a bid during an auction.
        
        Arguments:
            player (Player): the player whose turn it is to bid.
            
        Side effects:
            prints messages relating to the bid
            asks for player input for their bid
            if their bid is valid and higher than the current bid, sets the cp
                and cbid attributes accordingly
        Returns:
            str: if the player doesn't input a number, returns their input
        """
        b = player.bid(self)
        if isinstance(b, str):
            return b
        if b <= self.cbid:
            advprint("You must bid higher than the current max bid")
            #sleep(0.5)
        else:
            self.cp = player
            self.cbid = b
        
    def turn(self):
        """ Processes a round of an auction.
        
        Side effects:
            calls self.bid for each remaining player
            prints a message
            if a player wants to exit the auction, adds them to self.done
        """
        for p in self.p:
            if p not in self.done and p != self.cp:
                mybid = self.abid(p)
                if mybid:
                    if mybid in ('exit', 'stop'):
                        self.done.add(p)
                    else:
                        advprint('bad input')
                        #sleep(0.5)
                    continue
    
    def auc(self):
        """ Handles the process of an auction.
        
        Side effects:
            prints messages indicating the start and end of the auction
            
        Returns:
            int: if a player placed a valid bid, returns 1
        """
        advprint('Starting auction')
        #sleep(0.5)
        while len(self.p) - len(self.done) > 1:
            self.turn()
        if self.cp and self.cbid:
            advprint(f"{self.prop} is sold to {self.cp} for {self.cbid}")
            #sleep(0.5)
            return 1
        else:
            advprint("No one gets it")  
            #sleep(0.5)

