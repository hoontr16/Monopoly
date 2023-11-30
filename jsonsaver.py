import json
from monopoly_player import Player, protected_words
from monopoly_property import Property, Railroad, Utility, board_spaces
from monopoly_boardstate import BoardState
from monopoly_cards_exp import chance, community_chest as cc
from copy import copy
import re
from monopoly_basic_exp import advprint

class PlayerEncoder(json.JSONEncoder):
    """ An encoder for Player objects.
    """
    def default(self, obj):
        """ Encode a Player object.
        
        Arguments:
            obj (Player): the player to encode
            
        Returns:
            dict: the Player object's attributes, as a dictionary
            if obj is not a Player, return the default method of the parent class
        """
        if isinstance(obj, Player):
            return {'name': obj.name, 'turn order': obj.turn, 'location': obj.loc,
                    'wallet': obj.wallet, 'deeds': {name: [repr(i) for i in obj.deeds[name]]
                        for name in obj.deeds}, 'state': repr(obj.game),
                    'chance': obj.chance, 'cc': obj.cc, 'in Jail': obj.inJail,
                    'jail turns': obj.jailTurn
                    }
        return json.JSONEncoder.default(self, obj)
    
class PropertyEncoder(json.JSONEncoder):
    """ An encoder for Property objects.
    """
    def default(self, obj):
        """ Encode a Property object.
        
        Arguments:
            obj (Property): the property to encode

        Returns:
            dict: the Property object's volatile attributes, as a dictionary
            if obj is not a Property, return the default method of the parent class            
        """
        if isinstance(obj, Property):
            return {'name': obj.name, 'bnum': obj.bnum, 'owner': repr(obj.owner),
                    'pcount': obj.pcount}
        return json.JSONEncoder.default(self, obj)
    
class BoardStateEncoder(json.JSONEncoder):
    """ An encoder for BoardState objects.
    """
    def default(self, obj):
        """ Encode a BoardState object.
        """
        if isinstance(obj, BoardState):
            return {'state': {'players': obj.players, 'turn': obj.turn, 'board': obj.board,
                    'turn total': obj.turntotal, 'chance': repr(obj.chance),
                    'cc': repr(obj.cc), 'lost players': obj.plost, 'time saved': obj.time}}
        return json.JSONEncoder.default(self, obj)

def save(state, path='backup'):
    """ Save a BoardState to a json file.
    
    Arguments:
        state (BoardState): the object to save
        path (str): the path to the file to save to. file designator not included. defaults to 'backup', saving to backup.json
    
    Side effects:
        writes to a file, creating it if necessary
    """
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
    with open(f"{path}.json", 'w', encoding='utf-8') as f:
        json.dump(newstate, f, indent=2, cls=BoardStateEncoder)
        
class LoadError(Exception):
    pass

class SaveState:
    """ An object for loading a saved game state.
    
    Attributes:
        state (dict): the non-Player, non-board attributes of the gamestate.
        p (list): the list of Player dictionaries
        l (list): the list of lost Players
        b (dict): the loaded board as a dictionary
    """
    def __init__(self, path):
        """ Initialize a SaveState from a JSON file.
        
        Arguments:
            path (str): the relative path to a JSON file
        
        Side effects:
            sets attributes
            loads from a file
        """
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
        """ Check whether an encoded property's values are valid.
        
        Arguments:
            prop (dict): the dictionary of the encoded Property
            
        Side effects:
            prints a message when beginning to check
        
        Raises:
            LoadError if an attribute is invalid
        """
        advprint(f"verifying {prop['name']}")
        c = 0
        for space in board_spaces.values():
            if isinstance(space, Property) and space.name == prop['name']:
                try:
                    prop['pcount'] = int(prop['pcount'])
                except ValueError:
                    raise LoadError("Bad pcount")
                if prop['pcount'] < 0 or prop['pcount'] > space.stot:
                    raise LoadError("Bad pcount")
                if (isinstance(space, Railroad) or isinstance(space, Utility)) and prop['bnum'] != 0:
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
                #print('boo')
                raise LoadError('Bad pcount')
            for p in self.p:
                if prop['owner'].split()[1] == p['name']:
                    #print('yay')
                    c += 1
                    break
        elif prop['pcount'] != 0:
            #print('boo')
            raise LoadError("Bad pcount")
        else:
            c += 1
        if not c:
            raise LoadError("Bad owner")
        
    def verify_space(self, space):
        """ Verify the values of a space.
        
        Arguments:
            space (str or dict): either the name of a special space, or the dictionary of a Property.
            
        Raises:
            LoadError if a special space is invalid, if raised by verify_property, or if space is another type
        """
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
        """ Verify the values for each Player object in self.p.
        
        Raises:
            LoadError if an attribute is invalid
        """
        turns = []
        for p in self.p:
            advprint(f"Verifying {p['name']}")
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
            if p['in Jail'] not in (True, False):
                #print(p['in Jail'])
                raise LoadError("Bad Jail bool")
            try:
                p['jail turns'] = int(p['jail turns'])
            except ValueError:
                raise LoadError("Bad jail turns")
            if (p['in Jail'] == 'true' and p['jail turns'] not in range(3)) or (
                p['in Jail'] == 'false' and p['jail turns'] != 0):
                raise LoadError("Bad jail turns")
            props = [repr(i) for i in board_spaces.values()]
            for s in p['deeds']:
                for prop in p['deeds'][s]:
                    if prop not in props:
                        #print(prop)
                        #print(props)
                        raise LoadError('Bad deeds')
        turns.sort()
        if turns != list(range(len(self.p))):
            raise LoadError('Bad turn orders')
        
    def extract_cards(self, str):
        """ Create a dictionary of cards from the formal string representation in the save state.
        
        Arguments:
            str (str): the string to pull from.
        
        Returns:
            dict: card indices and their names, in order
        """
        rdeck = r"(\{[^\{\}]+\})"
        s = re.search(rdeck, str)[1]
        rcards = r"(\d+):(\s(.+?)(,\s\D.+?)*),\s"
        r = re.finditer(rcards, s)
        mydeck = {}
        for i in r:
            try:
                mydeck[int(i[1])] = (i[3] + i[4]).strip("'").strip('"').replace("\\", "")
            except TypeError:
                mydeck[int(i[1])] = i[3].strip("'").strip('"').replace("\\", "")
        return mydeck
    
    def verify_deck(self, deck, mytype):
        """ Validate a saved deck.
        
        Arguments:
            deck (str): the saved deck.
            mytype (str): whether the deck is Chance or Community Chest.
            
        Raises:
            LoadError if the deck type is invalid, or there is an invalid card.
        """
        mydeck = self.extract_cards(deck)
        #print(mydeck)
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
            #print(myvals)
            #print(basevals)
            raise LoadError('bad deck')
    
    def verify_state(self):
        if self.state['turn'] not in range(len(self.p)):
            raise LoadError('bad turn number')
        if not isinstance(self.state['turn total'], int) or self.state['turn total'] < 0:
            raise LoadError('bad turn total')
        try:
            self.verify_deck(self.state['chance'], 'chance')
            self.verify_deck(self.state['cc'], 'cc')
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
            myp.inJail = p['in Jail']
            myp.jailTurn = p['jail turns']
            for s in myp.deeds:
                myp.deeds[s].clear()
            loadplayers.append(myp)
        for s in self.b:
            space = self.b[s]
            if isinstance(space, dict):
                for i in board_spaces.values():
                    if isinstance(i, Property):
                        a = i.name
                    else:
                        a = i
                    if a == space['name']:
                        myspace = i
                        myspace.bnum = space['bnum']
                        myspace.pcount = space['pcount']
                        if space['owner'] == 'None':
                            own = None
                        else:
                            for p in loadplayers:
                                if repr(p) == space['owner']:
                                    own = p
                                    p.deeds[myspace.set].append(myspace)
                                    break
                        myspace.owner = own
        loadstate = BoardState(pdef=loadplayers)
        loadstate.turn = self.state['turn']
        loadstate.board = board_spaces
        loadstate.turntotal = self.state['turn total']
        #mychance = dict(self.state['chance'].split('with cards ')[1].strip('>'))
        mychance = self.extract_cards(self.state['chance'])
        #mycc = dict(self.state['cc'].split('with cards ')[1].strip('>'))
        mycc = self.extract_cards(self.state['cc'])
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