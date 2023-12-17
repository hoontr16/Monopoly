from monopoly_basic_exp import roll_dice, advprint
from monopoly_exceptions import LoserError, ImprovementError

class Property:
    """ An object for properties.
    
    Attributes:
        name (str): its name
        set (str): the set it belongs to
        stot (int): how many properties are in its set, including itself
        price (int): the cost to buy it
        mprice (int): how much a player gains when mortgaging it, also used to 
            calculate the cost to unmortgage
        mstatus (bool): whether its mortgaged
        rent (list): the rent prices as a list of ints, with increasing values for each
            level of improvement (houses & hotels)
        bprice (int): the cost to improve it
        bnum (int): how many buildings it has, 5 being a hotel
        owner (Player or None): the current owner of the Property.
        extra (bool): whether to charge extra rent next time the get_rent method
            is called
        pcount (int): how many properties in its set the property's current owner
            owns.
        iprice (int): how much a player pays in interest when recieving this
            property mortgaged.
    """
    def __init__(self, name:str, my_set:str, set_total:int, price:int, mortgage_price:int, \
                 rent_prices:list, building_price:int, building_num:int=0, \
                 mortgage_status:bool=False):
        """ Initialize a Property object.
        
        Arguments:
            name (str): its name.
            my_set (str): the set it belongs to
            set_total (str): how many properties are in its set
            price (int): the price to buy this property
            mortgage_price (int): the money a player gains when mortgaging
            rent_prices (list): the rent prices as a list of ints, with increasing
                values for each level of improvement (houses & hotels)
            building_price (int): the cost to improve it
            building_num (int): how many buildings it currently has, 5 being a 
                hotel. determines which rent value gets retrieved. defaults to 0
            mortgage_status (bool): whether it's currently mortgaged. defaults 
                to False
            
            Side effects:
                sets attributes using the arguments, as well as:
                    self.owner to None
                    self.extra to False
                    self.pcount to 0
        """
        self.name = name
        self.set = my_set
        self.stot = set_total
        self.price = price
        self.mprice = mortgage_price
        self.mstatus = mortgage_status        
        self.rent = rent_prices
        self.bprice = building_price
        self.bnum = building_num
        self.owner = None
        self.extra = False
        self.pcount = 0
        self.iprice = self.mprice // 10
    
    def get_rent(self):
        """ Determines how much to charge for rent.
        
        Side effects:
            if self.extra is True, along with charging extra, sets self.extra 
                back to False
        
        Returns:
            int: if charging extra rent, returns the appropriate level of rent 
                    times 2
                elif the owner has the full set, and self has no improvements, 
                    returns double the unimproved rent
                else, returns the rent value from self.rent, using its 
                    improvement level as the index
        """
        if self.extra:
            self.extra = False
            return self.rent[self.bnum] * 2
        elif self.pcount == self.stot and self.bnum == 0:
            return 2 * self.rent[0]
        else:
            return self.rent[self.bnum]
    
    def pay_rent(self, lord, guest):
        """ Charges rent between two players.
        
        Arguments:
            lord (player): the owner of the property
            guest (player): the player paying the rent
            
        Side effects:
            if the property is mortgaged, prints a message and returns None
            otherwise, calls self.get_rent, and transfers the value returned
                from the guest's wallet to the owner's
            prints helpful messages afterwards
        """
        if self.mstatus:
            advprint('No rent this time! This property is mortgaged')
            return
        rent = self.get_rent()
        guest.creditor = lord
        try:
            guest -= rent
            guest.creditor = 'the Bank'
        except LoserError:
            return
        lord += rent
        advprint(f'{guest.name} just paid {lord.name} ${rent} to stay at {self.name}')
        #advprint(f"{guest.name}'s wallet balance: ${guest.wallet}")
        #advprint(f"{lord.name}'s wallet balance: ${lord.wallet}")

    def build_house(self, num = 1):
        """ Builds a house (or two).
        
        Arguments:
            num (int): how many improvements to make. defaults to 1, should either
                be 1 or 2
                
        Side effects:
            adds num to self's bnum attribute
            
        Returns:
            if the property already has a hotel, does not build the house,
                instead returning None
            otherwise, returns the total cost of the improvement, as num * the
                cost per improvement
        """
        if self.bnum == 5:
            return None
        self.bnum += num
        return self.bprice * num
    
    def sell_house(self, num = 1):
        """ Sells a house (or two).
        
        Arguments:
            num (int): how many improvements to sell. defaults to 1, should either
                be 1 or 2
                
        Side effects:
            subtracts num from self's bnum attribute
            
        Returns:
            if the property has no improvements to sell, does not sell a house,
                instead returning None
            otherwise, returns the money raised, as half of the bprice times num,
                rounded down and converted to int
        """
        if self.bnum == 0:
            return
        self.bnum -= num
        return int((self.bprice * num * 0.5) // 1)
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'<property {self.name!r}>' 
    
    def mortgage(self):
        """ Mortgages the Property.
        
        Side effects:
            prints messages if the property can't be mortgaged
            otherwise, adds the mortgage value to the owner's wallet, and sets
                self's mstatus attribute to True
        
        Returns:
            if the property is already mortgaged, or if any property in its set
                has improvements, returns None
            otherwise, returns True
        """
        if self.mstatus:
            advprint("This property is already mortgaged")
            return
        for p in self.owner.deeds[self.set]:
            if p.bnum != 0:
                advprint("All properties in a set must have no houses in order to mortgage any property in that set")
                return
        self.owner += self.mprice
        self.mstatus = True
        return True
    
    def unmortgage(self):
        """ Unmortgages the Property.
        
        Side effects:
            prints messages if the property can't be unmortgaged
            otherwise, subtracts the mortgage value (plus 10% interest, rounded
                down) from the owner's wallet, sets the self.mstatus attribute
                to False, and prints a message
        
        Returns:
            if it can't be mortgaged, returns None
            otherwise, returns True
        """
        if not self.mstatus:
            advprint('This property is not mortgaged')
            return
        if self.owner.wallet < (self.mprice * 1.1) // 1:
            advprint("You don't have enough money to unmortgage this")
            return
        self.owner -= int((self.mprice * 1.1) // 1)
        self.mstatus = False
        advprint(f"{self.owner} unmortgaged {self} for ${int(self.mprice * 1.1)}")
        return True
    
    def __bool__(self):
        if len(self.rent) == 0 and not self.name:
            return False
        return True
    
class Railroad(Property):
    """ A subclass of Property, for railroads.
    """
    def get_rent(self):
        """ Calculate the rent.
        
        Side effects:
            if self.extra is True, along with charging extra, sets self.extra 
                back to False
        
        Returns:
            int: if charging extra rent, returns the appropriate level of rent 
                    times 2
                else, returns the rent value from self.rent, using the number of
                    railroads owned by self's owner minus 1 as the index
        """
        if self.extra:
            self.extra = False
            return self.rent[self.pcount - 1] * 2        
        else:
            return self.rent[self.pcount - 1]
        
    def build_house(self, num=1):
        raise ImprovementError('no building houses on railroads!')
    
    def sell_house(self, num=1):
        raise ImprovementError('no selling houses on railroads')

class Utility(Property):
    """ A subclass of Property, for utilities.
    """
    def get_rent(self):
        """ Calculate the rent.
        
        Side effects:
            if self.extra is True, along with charging extra, sets self.extra 
                back to False
            prints the dice roll for the rent
        
        Returns:
            if charging extra rent, returns 10 times the dice roll.
            otherwise, returns the dice roll times either 4 or 10, depending on 
                how many utilities the owner owns
        """
        dice_roll = roll_dice()[0]
        ending = ''
        if dice_roll in (8, 11):
            ending = 'n'
        advprint(f'You rolled a{ending} {dice_roll}!')
        if self.extra:
            self.extra = False
            return self.rent[1] * dice_roll
        return self.rent[self.pcount - 1] * dice_roll    
        
    def build_house(self, num=1):
        raise ImprovementError('no building houses on utilities!')
    
    def sell_house(self, num=1):
        raise ImprovementError('no selling houses on utilities')
    
board_spaces = {0: 'Go', 1: Property('Mediterranean Avenue', 'Brown', 2, 60, 30, [2, 10, 30, 90, 160, 250], 50),
                2: 'Community Chest', 3: Property('Baltic Avenue', 'Brown', 2, 60, 30, [4, 20, 60, 180, 320, 450], 50),
                4: 'Income Tax', 5: Railroad('Reading Railroad', 'Railroads', 3, 200, 100, [25, 50, 100, 200], 0),
                6: Property('Oriental Avenue', 'Light Blue', 3, 100, 50, [6, 30, 90, 270, 400, 550], 50),
                7: 'Chance', 8: Property('Vermont Avenue', 'Light Blue', 3, 100, 50, [6, 30, 90, 270, 400, 550], 50),
                9: Property('Connecticut Avenue', 'Light Blue', 3, 120, 60, [8, 40, 100, 300, 450, 600], 50),
                10: 'Jail', 11: Property('St. Charles Place', 'Pink', 3, 140, 70, [10, 50, 150, 450, 625, 750], 100),
                12: Utility('Electric Company', 'Utilities', 3, 150, 75, [4, 10], 0),
                13: Property('States Avenue', 'Pink', 3, 140, 70, [10, 50, 150, 450, 625, 750], 100),
                14: Property('Virginia Avenue', 'Pink', 3, 160, 80, [12, 60, 180, 500, 700, 900], 100),
                15: Railroad('Pennsylvania Railroad', 'Railroads', 3, 200, 100, [25, 50, 100, 200], 0),
                16: Property('St. James Place', 'Orange', 3, 180, 90, [14, 70, 200, 550, 750, 950], 100),
                17: 'Community Chest', 18: Property('Tennessee Avenue', 'Orange', 3, 180, 90, [14, 70, 200, 550, 750, 950], 100),
                19: Property('New York Avenue', 'Orange', 3, 200, 100, [16, 80, 220, 600, 800, 1000], 100),
                20: 'Free Parking', 21: Property('Kentucky Avenue', 'Red', 3, 220, 110, [18, 90, 250, 700, 875, 1050], 150),
                22: 'Chance', 23: Property('Indiana Avenue', 'Red', 3, 220, 110, [18, 90, 250, 700, 875, 1050], 150),
                24: Property('Illinois Avenue', 'Red', 3, 240, 120, [20, 100, 300, 750, 925, 1100], 150),
                25: Railroad('B&O Railroad', 'Railroads', 3, 200, 100, [25, 50, 100, 200], 0),
                26: Property('Atlantic Avenue', 'Yellow', 3, 260, 130, [22, 110, 330, 800, 975, 1150], 150),
                27: Property('Ventnor Avenue', 'Yellow', 3, 260, 130, [22, 110, 330, 800, 975, 1150], 150),
                28: Utility('Water Works', 'Utilities', 3, 150, 75, [4, 10], 0),
                29: Property('Marvin Gardens', 'Yellow', 3, 280, 140, [24, 120, 360, 850, 1025, 1200], 150),
                30: 'Go To Jail', 31: Property('Pacific Avenue', 'Green', 3, 300, 150, [26, 130, 390, 900, 1100, 1275], 200),
                32: Property('North Carolina Avenue', 'Green', 3, 300, 150, [26, 130, 390, 900, 1100, 1275], 200),
                33: 'Community Chest', 34: Property('Pennsylvania Avenue', 'Green', 3, 320, 160, [28, 150, 450, 1000, 1200, 1400], 200),
                35: Railroad('Short Line', 'Railroads', 3, 200, 100, [25, 50, 100, 200], 0),
                36: 'Chance', 37: Property('Park Place', 'Dark Blue', 3, 350, 175, [35, 175, 500, 1100, 1300, 1500], 200),
                38: 'Luxury Tax', 39: Property('Boardwalk', 'Dark Blue', 3, 400, 200, [50, 200, 600, 1400, 1700, 2000], 200)}