from monopoly_player import make_players
from monopoly_property import board_spaces
from monopoly_classes_exp import Auction, Deck, Movement
from monopoly_exceptions import LoserError
from monopoly_command import Command
from monopoly_basic_exp import advprint
from time import time, localtime

class BoardState:    
    """ The current game state, created once per game and modified as it goes on.
    
    Attributes:
        players (list): the players in the game.
        turn (int): the current index of the turn order. determines whose turn it is
        turntotal (int): how many total turns have happened this game
        board (dict): the board spaces
        special (set): the names of the non-property spaces on the board
        chance (Deck): the current deck of Chance cards
        cc (Deck): the current deck of Community Chest cards
        plost (list): the players that have lost
        cp (Player): the Player whose turn it is
    """
    def __init__(self, pdef=[]):
        """ Initialize the game.
        
        Arguments:
            pdef (list): a default list of players. allows for predefined player
                names, and custom scenarios for debugging. if empty, creates a
                list of players. defaults to an empty list
        
        Side effects:
            sets attributes to their default values
        """
        if pdef:
            self.players = pdef
        else:
            self.players = make_players(self)
        self.turn = 0
        self.board = board_spaces
        self.special = {'Go', 'Community Chest', 'Income Tax', 'Chance', 'Jail', 'Free Parking', 'Luxury Tax', 'Go To Jail'}
        self.turntotal = 0
        self.chance = Deck('chance')
        self.cc = Deck('cc')
        self.plost = []
        self.time = localtime(time)
        
    def __repr__(self):
        return f"<BoardState object saved at {self.time}>"
        
    def whose_turn(self):
        """ Determine whose turn it is.
        
        Returns:
            Player: the Player whose turn_order matches the current turn
        """
        return self.players[self.turn]

    def find_prop(self, name):
        """ Given the name of a property, find the corresponding Property object.
        
        Arguments:
            name (str): the name of the property
            
        Returns:
            None: if name corresponds to a valid board space, but isn't a Property
            Property: the Property object from self.board matching name.
        """
        for i in self.board:
            space = self.board[i]
            if name.lower() == str(space).lower():
                if isinstance(space, str):
                    return
                return space
    
    def buy_property(self, some_player, some_property, other_price=None):
        """ Buy a property.
        
            Args:
                some_player (player): the player buying the property
                some_property (property): the property being bought
                other_price (int, None): a custom price. if None, uses some_property's
                    price attribute instead. defaults to None
                    
            Side effects:
                Subtracts the property's price from the player's wallet
                Adds the property to the player's deeds attribute
                Updates the pcount attribute's for each property in some_property's
                    set that some_player owns
                Prints what the player bought, how much it cost, and their current
                    balance
                Updates the property's owner attribute to some_player
        """
        price = some_property.price
        if other_price:
            price = other_price
        try:
            some_player -= price
        except LoserError:
            return
        some_player += some_property
        some_player * some_property.set
        advprint(f'{some_player.name} bought {some_property.name} for ${price}!')
        #advprint(f"{some_player.name}'s wallet balance: ${some_player.wallet}") 
        #some_property.owner = some_player  
    
    def in_jail(self):
        """ Handles the logic for entering Jail, spending turns in Jail, and leaving.
            
            Side effects:
                increments the current player's inJail attribute
                if the player has spent 3 turns in Jail, prints a message and calls p_jail_reset()
                else, asks for input for the player's move
                prints messages related to their input and outcomes
                
            Returns:
                None: when failing to roll for doubles to escape
                False: when leaving Jail by any method except rolling
                list: after successfully rolling to escape
        """
        if self.cp.inJail:
            self.cp.jailTurn += 1
            
            def p_jail_reset(method):
                """ Processes the different methods of escaping Jail.
                    
                    Args:
                        method (str): how the player is escaping Jail. should be
                            one of: time, pay, roll, card
                            
                    Side effects:
                        subtracts the fine or GOJF card from the player, if applicable
                        sets player's Jail attributes back to the default
                            
                    Returns:
                        list: if the player rolled to escape, returns their roll,
                        but without the doubles
                """
                if method == 'time' or method == 'pay':
                    try:
                        self.cp.wallet -= 50
                    except:
                        return 
                elif method == 'roll':
                    advprint('You rolled doubles and escaped!')
                    c[1] = 'nope'
                    self.cp.inJail = False
                    self.cp.jailTurn = 0
                    return c
                else:
                    if self.cp.chance:
                        self.cp.chance -= 1
                    elif self.cp.cc:
                        self.cp.cc -= 1
                    else:
                        raise ValueError("You don't have any cards!")
                self.cp.inJail = False
                self.cp.jailTurn = 0
            
            if self.cp.jailTurn == 3:
                advprint("You've served your time. You pay $50 and leave Jail.")
                p_jail_reset('time')
                return False
            else:
                while True:
                    pchoice = Command(self, 'jail', "You're in Jail. Would you like to roll, use a GOJF card, or pay the fine?\n")
                    while True:
                        try:
                            c = pchoice.action()
                            break
                        except:
                            advprint("Please enter either 'roll', 'card', or 'pay'")
                            pchoice = Command(self, 'jail', "You're in Jail. Would you like to roll, use a GOJF card, or pay the fine?\n")
                            continue
                    if pchoice.text == 'roll':
                        if c[1] == 'doubles':
                            advprint(c)
                            p_jail_reset('roll')
                            return c
                        else:
                            advprint('No doubles this time')
                            return 
                    elif pchoice == 'card':
                        if self.cp.chance == 0 or self.cp.cc == 0:
                            advprint("You don't have any GOJF cards!")
                        else:
                            p_jail_reset('card')
                            return False
                    else:
                        p_jail_reset('pay')
                        advprint("You pay the $50 fine and leave Jail.")
                        return False
        else:
            advprint(f"{self.cp.name} is going to Jail!")
            self.cp.loc = 10
            self.cp.inJail = True

    def move(self, new_loc = None):
        """ Moves the current player, and the consequences of the move.
        
        Arguments:
            new_loc (int, None): a custom location to move to. defaults to None
            
        Side effects:
            creates and edits a Movement instance
            prints a successful move
            if landing on a property, asks the player if they want to buy it
            calls various functions depending on input and the player's location
        """
        my_move = Movement(self.cp, new_loc = new_loc)
        if my_move.doubles:
            self.cp.dcount += 1
        if self.cp.inJail or self.cp.dcount == 3:
            outcome = self.in_jail()
            if outcome:
                my_move.doubles = None
                #my_move = Movement(self.cp, new_loc = self.cp.loc + )
                my_move.new = 10 + outcome[0]
                my_move.nspace = self.board[my_move.new]      
            elif outcome == False:
                pass
            else:
                my_move.doubles = None
                return my_move
            ending = ''
            if my_move.new in (8, 11):
                ending = 'n'
            advprint(f"{self.cp.name} rolled a{ending} {my_move.new - 10}")
        my_move.move()
        cprop = my_move.nspace
        if not isinstance(cprop, str):
            if not cprop.owner:
                a = Command(self, 'choice', "Would you like to buy it?\n")
                a1 = a.action()
                if a1:
                    self.buy_property(self.cp, cprop)
                else:
                    advprint(f'{cprop} is up for auction!')
                    auc = Auction(cprop, [p for p in self.players if p not in self.plost], self)
                    if auc.auc():
                        self.buy_property(auc.cp, cprop, other_price=auc.cbid)
            else:
                cprop.pay_rent(cprop.owner, self.cp)
            #elif cprop.get_rent() <= self.cp.wallet:
            #    cprop.pay_rent(cprop.owner, self.cp)
            #else:
            #    a = self.raise_money(self.cp, cprop.owner, cprop.get_rent())
            #    if not a:
            #        self.lose(cprop.owner)
            #    else:
            #        cprop.pay_rent(cprop.owner, self.cp)
        else:
            self.special_space(cprop)
        return my_move

    def raise_money(self, p, other_p, debt):
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
        advprint(f"{p} owes {other_p} ${debt}")
        def check_options(p):
            """ Display the player's assets.
            
            Arguments:
                p (Player): the player raising money.
                
            Side effects:
                prints p's available assets and their sell/mortgage price
            """
            advprint('Here are your assets:')
            advprint()
            advprint(f"Your current balance: ${p.wallet}")
            for s in p.deeds:
                for prop in s:
                    if prop.bnum:
                        advprint(f"{prop} : {'hotel' if prop.bnum == 5 else f'{prop.bnum} houses'}, sell price: ${prop.bprice // 2}")
                    else:
                        advprint(f"{prop} : {'Mortgaged' if prop.mstatus else f'Unmortgaged, mortgage price: ${prop.mprice}'}")
        while p.wallet < debt:
            if p.check_lost(debt):
                advprint("You lose!")
                return
            check_options(p)
            c = Command(self, 'poor', "What would you like to do?\n")
            ctype, pname = c.action()
            if ctype not in ('mortgage', 'sell'):
                advprint("Please enter either 'mortgage' or 'sell', followed by the property you choose")
                continue
            cprop = self.find_prop(pname)
            if cprop == None:
                continue
            if ctype == 'mortgage':
                cprop.mortgage()
            else:
                n = 0
                for i in p.deeds[cprop.set]:
                    if i.bnum > cprop.bnum:
                        if i.bnum == 5:
                            advprint(f'Houses must be sold evenly across a set. {i} has a hotel, while {cprop} has {cprop.bnum} houses')
                        else:
                            advprint(f'Houses must be sold evenly across a set. {i} has {i.bnum} houses, while {cprop} has {cprop.bnum}')
                        n += 1
                if not n:
                    try:
                        p += cprop.sell_house()
                    except:
                        continue
        return debt
                
    def do_chance(self):
        """ Carries out the effect for each chance card.
            
            Side effects:
                Prints the text of the card drawn
                Depending on the card drawn, can move the player, charge extra
                    rent, give or charge money, send them to Jail, or give them 
                    a GOJF card
        """
        ind, text = self.chance.draw_card()
        advprint(text)
        try:
            if ind == 0:
                self.cp += 200
            elif ind == 1:
                self.move(new_loc=24)
            elif ind == 2:
                self.move(new_loc=11)      
            elif ind == 3:
                if self.cp.loc >= 28 or self.cp.loc < 12:
                    self.board[12].extra = True
                    self.move(new_loc=12)
                else:
                    self.board[28].extra = True
                    self.move(new_loc=28)
            elif ind == 4 or ind == 5:
                if self.cp.loc >= 35 or self.cp.loc < 5:
                    self.board[5].extra = True
                    self.move(new_loc=5)
                elif self.cp.loc < 15:
                    self.board[15].extra = True
                    self.move(new_loc=15)
                elif self.cp.loc < 25:
                    self.board[25].extra = True
                    self.move(new_loc=25)
                else:
                    self.board[35].extra = True
                    self.move(new_loc=35)
            elif ind == 6:
                self.cp += 50
            elif ind == 7:
                self.cp.chance += 1
            elif ind == 8:
                self.move(new_loc = self.cp.loc-3)
            elif ind == 9:
                self.cp.loc = 10
                self.cp.inJail = True
                advprint(f"{self.cp.name} is going directly to Jail!")
            elif ind == 10:
                repairs = 0
                for pset in self.cp.deeds:
                    if len(self.cp.deeds[pset]) != 0:
                        for prop in self.cp.deeds[pset]:
                            if prop.bnum == 5:
                                repairs += 100
                            else:
                                repairs += 25 * prop.bnum
                advprint(f"{self.cp.name} paid ${repairs} in building repairs")
                self.cp -= repairs
                #advprint(f"{self.cp.name}'s wallet balance: ${self.cp.wallet}")
            elif ind == 11:
                self.extra = True
                self.move(new_loc=5)
            elif ind == 12:
                self.cp -= 15
            elif ind == 13:
                self.move(new_loc=39)
            elif ind == 14:
                for p in self.players:
                    self.cp.creditor = p
                    self.cp -= 50
                    p += 50
            elif ind == 15:
                self.cp += 150
        except LoserError:
            return
    def do_cc(self):
        """ Carries out the effect for each community chest card.

            Side effects:
                Prints the text of the card drawn
                Depending on the card drawn, can move the player, charge extra
                    rent, give or charge money, send them to Jail, or give them 
                    a GOJF card
        """
        ind, text = self.cc.draw_card()
        advprint(text)
        try:
            if ind == 0:
                self.move(new_loc=0)
            elif ind == 1:
                self.cp += 200
            elif ind in (2, 11, 12):
                self.cp -= 50
            elif ind == 3:
                self.cp += 50
            elif ind == 4:
                self.cp += 1
            elif ind == 5:
                self.cp.loc = 10
                self.cp.inJail = True
                advprint(f"{self.cp.name} is going directly to Jail!")
            elif ind == 6:
                for p in self.cp:
                    p.creditor = self.cp
                    p -= 50
                    self.cp += 50
                    p.creditor = 'the Bank'
            elif ind in (7, 10, 16):
                self.cp += 100
            elif ind == 8:
                self.cp += 20
            elif ind == 9:
                for p in self.players:
                    p.creditor = self.cp
                    p -= 10
                    self.cp += 10
                    p.creditor = 'the Bank'
            elif ind == 13:
                self.cp += 25
            elif ind == 14:
                repairs = 0
                for pset in self.cp.deeds:
                    if len(self.cp.deeds[pset]) != 0:
                        for prop in self.cp.deeds[pset]:
                            if prop.bnum == 5:
                                repairs += 115
                            else:
                                repairs += 40 * prop.bnum
                advprint(f"{self.cp.name} paid ${repairs} in building repairs")
                self.cp -= repairs
                #advprint(f"{self.cp.name}'s wallet balance: ${self.cp.wallet}")
            elif ind == 15:
                self.cp += 10
        except LoserError:
            return

    def special_space(self, space):
        """ Handles special effects from landing on certain spaces.
            Args:
                space (str): the name of the space the player landed on.
                player (player): the player who landed on the space.
            Side effects:
                If space is 'Income Tax' or 'Luxury Tax', changes the player's
                    balance appropriately
                If space is Free Parking, GO, or OR (space is Jail AND player is not in jail), 
                    return None
                If space is Go To Jail, moves the player to Jail and sets
                    player.inJail to True
                If space is Chance or Community Chest, calls the appropriate function
                    and checks if the deck is empty, refreshing if it is
                Prints a message saying what happened.
        """
        try:
            if space == 'Go':
                return
            elif space == 'Income Tax':
                advprint(f"{self.cp.name} just paid $200 in Income Tax")
                self.cp -= 200
                return
            elif space == 'Luxury Tax':
                advprint(f"{self.cp.name} just paid $100 for the Luxury Tax")
                self.cp -= 100
                return
            elif space == 'Free Parking':
                return
            elif space == 'Go To Jail':
                self.cp.loc = 10
                self.cp.inJail = True
                advprint(f"{self.cp.name} is going directly to Jail!")
                return
            elif space == 'Jail' and self.cp.inJail == False:
                return
            elif space == 'Community Chest':
                self.do_cc()
                if len(self.cc) == 0:
                    if self.check_card()[1]:
                        self.cc.refresh(taken=True)
                    else:
                        self.cc.refresh()
            elif space == 'Chance':
                self.do_chance()
                if len(self.chance) == 0:
                    if self.check_card[0]:
                        self.chance.refresh(taken=True)
                    else:
                        self.chance.refresh()
        except LoserError:
            return
    
    def lose(self, loser, creditor):
        """ Removes the current player from the game.
        
        Arguments:
            creditor (Player, None): the player that the current player owes. if
                None, the current player owes the bank
                
        Side effects:
            if creditor is None, puts all of loser's properties up for auction
            otherwise, gives their properties to creditor, while handling their
                mortgaged status
            gives their GOJF cards to the appropriate party
        """
        if not creditor:
            for aset in loser.deeds:
                for p in aset:
                    p.mstatus = None
                    advprint(f'{p} is up for auction!')
                    auc = Auction(p, self.players - loser, self)
                    if auc.auc():
                        self.buy_property(auc.cp, p, other_price = auc.cbid)
                        for i in auc.cp.deeds[p.set]:
                            i.pcount = len(auc.cp.deeds[p.set])
                    else:
                        p.owner = None
            loser.chance, loser.cc = 0
        else:
            try:
                for aset in loser.deeds:
                    for p in loser.deeds[aset]:
                        p.owner = creditor
                        c = Command(self, 'rich', f"{creditor.name}, would you like to unmortgage {p}, or pay 10% interest? Enter either 'unmortgage' or 'interest': ")
                        while True:
                            try:
                                c1 = c.action()
                                break
                            except:
                                advprint("Please enter either 'unmortgage' or 'interest'")
                                c = Command(self, 'rich', f"{creditor.name}, would you like to unmortgage {p}, or pay 10% interest? Enter either 'unmortgage' or 'interest': ")
                        if c.text == 'unmortgage':
                            mstat = p.unmortgage()
                            if not mstat:
                                choice = ''
                                while choice not in ('y', 'n'):
                                    choice = Command(self, 'choice', 'Would you like to raise money for this? y or n ').text
                                choice = choice.action()
                                if choice:
                                    self.raise_money(creditor, 'the Bank', p.mprice)
                                    p.unmortgage()
                                elif creditor.wallet < p.mprice // 10:
                                    choice = ''
                                    while choice not in ('y', 'n'):
                                        choice = Command(self, 'choice', "You don't have enough money to pay the interest. Would you like to raise money for this? y or n ").text
                                    if choice.action():
                                        advprint(f'You pay the ${p.mprice // 10} interest')
                                        creditor -= p.mprice // 10
                                    else:
                                        p.owner = None
                                        continue
                                else:
                                    advprint(f'You pay ${p.mprice // 10} in interest instead')
                                    creditor -= p.mprice // 10
                                    creditor += p
                            else:
                                creditor += p
                        elif creditor.wallet < p.mprice // 10:
                            choice = ''
                            while choice not in ('y', 'n'):
                                choice = Command(self, 'choice', "You don't have enough money to pay the interest. Would you like to raise money for this? y or n ").text
                            if choice.action():
                                advprint(f'You pay the ${p.mprice // 10} interest')
                                creditor -= p.mprice // 10
                            else:
                                p.owner = None
                                continue
                        else:
                            creditor -= p.mprice // 10
                        creditor += p
                    loser.deeds[aset].clear()
                    creditor * aset
            except LoserError:
                self.lose(creditor, None)
                return
            creditor.chance += loser.chance
            creditor.cc += loser.cc
            loser.chance, loser.cc = 0
        self.plost.append(loser)
                        
    def check_card(self):
        chance_count = 0
        cc_count = 0
        for p in self.players:
            if p.chance:
                chance_count += 1
            if p.cc:
                cc_count += 1
        return chance_count, cc_count

    def improve_property(self, builder, bprop, bcount:str):
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
            return None
        try:
            bcount1 = int(bcount)
        except:
            advprint("Please enter an integer for the number of buildings")
            return None
        if bprop.bnum == 5:
            advprint(f"{bprop.name} already has a hotel!")
            return None
        if builder.wallet < bprop.bprice * bcount1:
            advprint("You don't have enough money!")
            return False
        if builder.count_set(setname=bprop.set) != bprop.stot:
            advprint("You don't own the full set!")
            return None
        else:
            for i in builder.deeds[bprop.set]:
                if i.mstatus == True:
                    advprint("One of the properties in this set is mortgaged.")
                    return None
                if bprop.bnum + bcount1 > i.bnum + 1 and bprop != i:
                    advprint(f"You must build evenly across a set. {bprop.name} has {bprop.bnum} houses, while {i.name} only has {i.bnum}. You cannot build {bcount1} houses on {bprop.name}")
                    return None
        choice = Command(self, 'choice', f"This will cost ${bprop.bprice * bcount1}. Are you sure? Enter y or n\n")
        if not choice.action():
            advprint('Purchase cancelled')
            return
        x = bprop.build_house(num=bcount1)
        builder -= x
        return 'yay'