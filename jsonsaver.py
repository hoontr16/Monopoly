import json
from monopoly_player import Player, protected_words
from monopoly_property import Property, Railroad, Utility, board_spaces
from monopoly_boardstate import BoardState
from monopoly_cards_exp import chance, community_chest as cc
from copy import copy
import re

class PlayerEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Player):
            return {'name': obj.name, 'turn order': obj.turn, 'location': obj.loc,
                    'wallet': obj.wallet, 'deeds': {name: [repr(i) for i in obj.deeds[name]]
                        for name in obj.deeds}, 'state': repr(obj.game),
                    'chance': obj.chance, 'cc': obj.cc, 'in Jail': obj.inJail,
                    'jail turns': obj.jailTurn
                    }
        return json.JSONEncoder.default(self, obj)
    
class PropertyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Property):
            return {'name': obj.name, 'bnum': obj.bnum, 'owner': repr(obj.owner),
                    'pcount': obj.pcount}
        return json.JSONEncoder.default(self, obj)
    
class BoardStateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BoardState):
            return {'state': {'players': obj.players, 'turn': obj.turn, 'board': obj.board,
                    'turn total': obj.turntotal, 'chance': repr(obj.chance),
                    'cc': repr(obj.cc), 'lost players': obj.plost, 'time saved': obj.time}}
        return json.JSONEncoder.default(self, obj)

def save(state, path='backup.json'):
    newstate = copy(state)
    jsonplayers = [json.dumps(p, indent=2, cls=PlayerEncoder) for p in newstate.players]
    #for p in newstate.players:
    #    jsonplayers.append(json.dumps(p, indent=2, cls=PlayerEncoder))
    jlost = [json.dumps(p, indent=2, cls=PlayerEncoder) for p in state.plost]
    jsonboard = {}
    for i in newstate.board:
        space = newstate.board[i]
        if isinstance(space, Property):
            jsonboard[i] = json.dumps(space, indent=2, cls=PropertyEncoder)
        else:
            jsonboard[i] = space
    newstate.players = jsonplayers
    newstate.board = jsonboard
    newstate.plost = jlost
    #my_save = json.dumps(state, cls=BoardStateEncoder, indent=2)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(newstate, f, indent=2, cls=BoardStateEncoder)
        
class LoadError(Exception):
    pass

class SaveState:
    def __init__(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            self.state = json.load(f)['state']
            self.p = [json.loads(i) for i in self.state['players']]
            self.l = [json.loads(i) for i in self.state['lost players']]
            self.b = {}
            for i in self.state['board']:
                try:
                    self.b[i] = json.loads(self.state['board'][i])
                except json.decoder.JSONDecodeError:
                    self.b[i] = self.state['board'][i]
            del self.state['players']
            del self.state['board']
            del self.state['lost players']
        #self.p = self.state['players']
        #self.b = self.state['board']

    def verify_property(self, prop):
        print(f"verifying {prop['name']}")
        c = 0
        for space in board_spaces:
            if isinstance(space, Property) and space.name == prop['name']:
                try:
                    prop['pcount'] = int(prop['pcount'])
                except ValueError:
                    raise LoadError("Bad pcount")
                if prop['pcount'] < 0 or prop['pcount'] > space.stot:
                    raise LoadError("Bad pcount")
                if (isinstance(space, Railroad) or isinstance(space, Utility)) and prop['bnum'] != '0':
                    raise LoadError("Bad bnum")
                c += 1
                break
        if not c:
            raise LoadError("Bad name")
        try:
            prop['bnum'] = int(prop['bnum'])
        except ValueError:
            raise LoadError("Bad bnum")
        if prop['bnum'] not in range(6):
            raise LoadError("Bad bnum")
        c = 0
        if prop['owner'] != 'None':
            if prop['pcount'] <= 0:
                raise LoadError('Bad pcount')
            for p in self.p:
                if prop['owner'].split()[1] == p.name:
                    c += 1
                    break
        elif prop['pcount'] != 0:
            raise LoadError("Bad pcount")
        if not c:
            raise LoadError("Bad owner")
        
    def verify_space(self, space):
        if isinstance(space, str):
            if space not in {'Go', 'Community Chest', 'Income Tax', 'Chance', 'Jail', 'Free Parking', 'Luxury Tax', 'Go To Jail'}:
                raise LoadError('bad special space')
        elif isinstance(space, dict):
            try:
                self.verify_property(space)
            except LoadError as e:
                raise e
        else:
            raise LoadError('bad space')
    
    def verify_players(self):
        turns = []
        for p in self.p:
            print(f"Verifying {p['name']}")
            if p['name'] in protected_words and protected_words.index(p['name']) > 14:
                raise LoadError("Bad name")
            try:
                p['turn order'] = int(p['turn order'])
            except ValueError:
                raise LoadError("Bad turn order")
            turns.append(p['turn order'])
            try:
                p['location'] = int(p['location'])
            except ValueError:
                raise LoadError("Bad location")
            if p['location'] not in range(40):
                raise LoadError("Bad location")
            if p["wallet"] < 0:
                raise LoadError("Bad wallet")
            if p['state'].split('saved at ')[1].strip('>') != self.state['time saved']:
                raise LoadError("Bad state")
            try:
                p['chance'] = int(p['chance'])
            except ValueError:
                raise LoadError("Bad chance")
            if p['chance'] not in (0, 1):
                raise LoadError("Bad chance")
            try:
                p['cc'] = int(p['cc'])
            except ValueError:
                raise LoadError("Bad cc")
            if p['cc'] not in (0, 1):
                raise LoadError("Bad cc")
            if p['in Jail'] not in ('true', 'false'):
                raise LoadError("Bad Jail bool")
            try:
                p['jail turns'] = int(p['jail turns'])
            except ValueError:
                raise LoadError("Bad jail turns")
            if (p['in Jail'] == 'true' and p['jail turns'] not in range(3)) or (
                p['in Jail'] == 'false' and p['jail turns'] != 0):
                raise LoadError("Bad jail turns")
            props = [repr(i) for i in board_spaces]
            for s in p['deeds']:
                for prop in p['deeds'][s]:
                    if prop not in props:
                        raise LoadError('Bad deeds')
        turns.sort()
        if turns != list(range(len(self.p))):
            raise LoadError('Bad turn orders')
        
    def verify_deck(self, deck, mytype):
        rdeck = "(\{[^\{\}]+\})"
        s = re.search(rdeck, deck)[1]
        mydeck = dict(s)
        mykeys = set(mydeck.keys())
        myvals = set(mydeck.values())
        if mytype == 'chance':
            basekeys = set(chance.keys())
            basevals = set(chance.values())
        elif mytype == 'cc':
            basekeys = set(cc.keys())
            basevals = set(cc.values())
        else:
            raise LoadError('bad deck type')
        if not mykeys <= basekeys or not myvals <= basevals:
            raise LoadError('bad deck')
    
    def verify_state(self):
        if self.state['turn'] not in range(len(self.p)):
            raise LoadError('bad turn number')
        if not isinstance(self.state['turn total'], int) or self.state['turn total'] < 0:
            raise LoadError('bad turn total')
        try:
            self.verify_deck(self.state['chance'], 'chance')
            self.verify_deck(self.deck['cc'], 'cc')
        except LoadError as e:
            raise e
    
    def verify(self):
        try:
            self.verify_players()
            self.verify_state()
            for i in self.b:
                self.verify_space(self.b[i])
        except LoadError as e:
            raise e
     
    def load(self):
        try:
            self.verify()
        except LoadError as e:
            raise e
        loadplayers = []
        for p in self.p:
            myp = Player(p['name'], p['turn order'], p['state'], p['location'], p['chance'], p['cc'], p['wallet'])
            myp.inJail = True if p['in Jail'] == 'true' else False
            myp.jailTurn = p['jail turns']
            for s in myp.deeds:
                myp.deeds[s].clear()
            loadplayers.append(myp)
        for s in self.b:
            space = self.b[s]
            if isinstance(space, dict):
                for i in board_spaces.values:
                    if i.name == space['name']:
                        myspace = i
                        myspace.bnum = space['bnum']
                        myspace.pcount = space['pcount']
                        if space['owner'] == None:
                            own = None
                        else:
                            for p in loadplayers:
                                if repr(p) == space['owner']:
                                    own = p
                                    p.deeds[myspace.set].append(myspace)
                                    break
                        myspace.owner = own
        loadstate = BoardState(pdef=loadplayers)
        loadstate.turn = self.state['turn order']
        loadstate.board = board_spaces
        loadstate.turntotal = self.state['turn total']
        mychance = dict(self.state['chance'].split('with cards ')[1].strip('>'))
        mycc = dict(self.state['cc'].split('with cards ')[1].strip('>'))
        loadstate.chance = mychance
        loadstate.cc = mycc
        for l in self.l:
            for p in loadstate.players:
                if l['name'] == p.name:
                    loadstate.plost.append(p)
                    break
        for p in loadstate.players:
            p.state = loadstate
        return loadstate
            
if __name__ == '__main__':
    pass
    #print(load(4))