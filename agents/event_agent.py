import random

def crowd_status():
    crowd = random.randint(0,10)
    if crowd > 6:
        return "Crowd Surge Expected"
    return "Crowd Normal"
