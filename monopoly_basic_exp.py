from random import randint
from time import sleep
import json

def roll_dice():
    """Simulates a single roll of two dice.
    
    Returns:
        int: integer between 2-12
    """
    x, y = randint(1, 6), randint(1, 6)
    if x == y:
        return [x + y, 'doubles']
    else:
        return [x + y, None]
    
def advprint(*args, **kwargs):
    with open('config.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    with open('log.txt', 'a', encoding='utf-8') as f:
        print(*args, **kwargs, file=f)
    if settings['printmode']:
        print(*args, **kwargs)
        sleep(0.3)