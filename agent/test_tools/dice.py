# agentic/test_tools.dice.py
import random
from typing import Dict

def dice() -> Dict[str, int]:
    """
    Simple dice roll tool.
    Returns a random number between 1 and 6.
    """
    value = random.randint(10, 16)
    return {"dice_roll": value}