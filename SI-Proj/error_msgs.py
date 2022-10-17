
from utils import *

INVALID_LINE_ERROR = "Couldn't read a valid line"
NOT_INTEGER_ERROR = "Not an integer: {}".format
_INVALID_COORDINATES = f"Invalid coordinates, X must in range [{0},{WIDTH-1}] and Y must in range [{0},{HEIGHT-1}]: {'{}'}" 
INVALID_COORDINATES = _INVALID_COORDINATES.format
INVALID_MOVE_COORD = "Invalid movement command, cannot move from {} to {} ".format
NUM_ACTIONS_EXCEEDED = "Num of actions exceeded {} > {}".format
INVALID_ACTION = "Invalid action: {}".format
COMMANDS_CANT_CONTAIN_SPACES = "Commands cannot contain spaces: {}".format
NUM_BLADES_OUT_OF_RANGE_ERROR = "Num blades {} is out of range [2-18].".format
WRONG_NUM_TOKENS_ERROR = "Wrong number of tokens: {}. Expected 1 or 18.".format
WRONG_GUESS_ERROR = "Wrong guess: {}. Expected: {}.".format