from random import randint
from time import sleep

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
    print(*args, **kwargs)
    sleep(0.3)