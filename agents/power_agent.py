import random

def power_status():
    load = random.randint(50,100)
    if load > 90:
        return "Possible Power Failure"
    return "Power Stable"
