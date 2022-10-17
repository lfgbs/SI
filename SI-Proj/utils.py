EMPTY_CELL = None
ALLIED_MAIN_BUILDING = 1
ALLIED_SOLDIER_MELEE = 2
ALLIED_SOLDIER_RANGED = 3
ENEMY_SOLDIER_MELEE = 4
ENEMY_SOLDIER_RANGED = 5
WALL = 6


# print
_PRINT = print

# prices
SOLDIERS_COST = {
    ALLIED_SOLDIER_MELEE: 50,
    ALLIED_SOLDIER_RANGED: 150
}

SOLDIER_MELEE_COST = SOLDIERS_COST[ALLIED_SOLDIER_MELEE]
SOLDIER_RANGED_COST = SOLDIERS_COST[ALLIED_SOLDIER_RANGED]


# constants
MAX_ACTIONS = 500
MAX_PROCESS_TIME = 200 # milliseconds
MAX_T = 2000 # maximun turns

# depends on the difficulty
BASE_COST = (500, 800)
BASE_PRODUCTION = (200, 200)

# soldier groups
alied_s = [ALLIED_SOLDIER_MELEE, ALLIED_SOLDIER_RANGED]
enemy_s = [ENEMY_SOLDIER_MELEE, ENEMY_SOLDIER_RANGED]

# map dimentions
HEIGHT = 11
VCENTER = HEIGHT//2 
WIDTH = 30


def gridstr(cell):
    cell = str(cell)
    for f,t in zip("1234", "BMRZ"):
        cell = cell.replace(f"[{f}",f"[{t}")

    return cell.ljust(9) 

# helper function
def duelResult(alied, enemy):
    if alied[0] == ALLIED_SOLDIER_MELEE and enemy[0] == ENEMY_SOLDIER_MELEE: # melee fight 
        if alied[1] > enemy[1]: 
            return [ALLIED_SOLDIER_MELEE, alied[1]-enemy[1]]
        elif alied[1] < enemy[1]:
            return [ENEMY_SOLDIER_MELEE, enemy[1]-alied[1]]
        else:
            return [None, 0]

    if alied[0] == ALLIED_SOLDIER_RANGED and enemy[0] == ENEMY_SOLDIER_MELEE: # ranged vs melee
        return [ENEMY_SOLDIER_MELEE, enemy[1]]
    
    if alied[0] == ALLIED_MAIN_BUILDING:
        return [ENEMY_SOLDIER_MELEE, enemy[1]]

