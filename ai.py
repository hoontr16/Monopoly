from monopoly_player import Player
from math import floor
from random import randrange
from monopoly_basic_exp import advprint

class ComputerPlayer(Player):
    def __init__(self, *args, **kwargs):
        self.mort_priority = ('Utilities', 'Brown', 'Dark Blue', 'Light Blue', 'Pink', 'Green', 'Railroads', 'Yellow', 'Orange', 'Red')
        self.house_sell_priority = ('Brown', 'Light Blue', 'Yellow', 'Dark Blue', 'Green', 'Pink', 'Orange', 'Red')
        super().__init__(*args, **kwargs)
    def jail_turn(self):
        if self.chance:
            return 'chance'
        elif self.cc:
            return 'cc'
        elif (self.state.turntotal / len(self.state.players) < 5\
            or sum(self.count_set().values()) < 5) and self.state.turntotal / len(self.state.players) < 15:
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
            hlist.append(s) if self.deeds[s][0].bnum else None
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
        def msort(p1, p2):
            if p1.set == p2.set:
                if p2.rent[0] > p1.rent[0]:
                    return p2
                return p1
            
            if p1.pcount == p1.stot and p2.pcount == p2.stot:
                mcount1 = 0
                for i in self.deeds[p1.set]:
                    if i.mstatus:
                        mcount1 += 1
                mcount2 = 0
                for i in self.deeds[p2.set]:
                    if i.mstatus:
                        mcount2 += 1
                return min(mcount1 / p1.stot, mcount2 / p2.stot)
                    
            return min(p1.stot - p1.pcount, p2.stot - p2.pcount)
        
        mlist = []
        for s in self.mort_priority[::-1]:
            for p in self.deeds[s]:
                mlist.append(p) if p.mstatus == True else None
        mlist.sort(key=msort)
        for p in mlist:
            if self.wallet > p.mprice * 2.5:
                p.umortgage()
                
    def get_mortgaged_prop(self, prop):
        if not prop.mstatus:
            raise ValueError("This property is not mortgaged")
        prop.owner = self
        if self.count_set(setname=prop.set) + 1 == prop.pcount:
            target = prop.mprice * 2
        else:
            target = prop.mprice * 2.5
        if self.wallet >= target:
            