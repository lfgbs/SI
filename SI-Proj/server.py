# Usage: `python testing_tool.py test_number`, where the argument test_number is
# either 0 (first test set) or 1 (second test set).
# This can also be run as `python3 testing_tool.py test_number`.

from __future__ import print_function
import random
import sys
import traceback
import time
import json
import os
import select

from collections import deque
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import argparse

from utils import *
from actions import *
from error_msgs import *
from utils import _PRINT

from viewer import Viewer

# Use raw_input in Python2.
try:
  input = raw_input
except NameError:
  pass


MAX_RETARD = 20000


DEBUG_FILE = "server_debug.txt"

def debug(*args):
    _PRINT(*args, file=sys.stderr, flush=True)
    with open(DEBUG_FILE, 'a') as f:
        stdout, sys.stdout = sys.stdout, f # Save a reference to the original standard output
        _PRINT(*args)
        sys.stdout = stdout
print = debug # dont erase this line, otherwise you cannot use the print function for debug 

def Output(*line):
    _PRINT(*line)
    sys.stdout.flush()
    if line=="END":
        sys.exit(0)
    elif line=="ERROR":
        sys.exit(1)


ACTION_LABEL = ["Upgrade building", "Recruit soldiers", "Move soldiers"]


CELL_PIXELS = 48
        

def printBitmap(b):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            _PRINT((b>>(y*WIDTH+x))&1 ,end=' ', file=sys.stderr)
        _PRINT(file=sys.stderr)
    _PRINT(file=sys.stderr)



ACTION_MAP = [UpgradeBase, RecruitSoldiers, MoveSoldiers]



class Environment:
    def __init__(self, difficulty, viewer):
        self.difficulty = difficulty
        self.base_cost = BASE_COST[difficulty]
        self.base_prod = BASE_PRODUCTION[difficulty]
        self.viewer = viewer
        self.building_level = 0
        self.retard = 0
        self.actions_taken = 0

        self.turn = 0


        self.resources = 500
        self.board = [[[None, 0] for w in range(WIDTH)] for h in range(HEIGHT)]

        self.board[HEIGHT//2][0] = [ALLIED_MAIN_BUILDING, self.building_level]

        for i in range(HEIGHT):
            self.board[i][4] = [ALLIED_SOLDIER_RANGED, 5]
            self.board[i][5] = [ALLIED_SOLDIER_MELEE, 10]

    def end(self):
        return self.board[HEIGHT//2][0][0] != ALLIED_MAIN_BUILDING or self.turn>=MAX_T or self.retard>=MAX_RETARD

    def validatePurchases(self, actions):
        leftactions = []
        for action in actions:
            if isinstance(action, UpgradeBase):
                cost = int(self.base_cost*(1.4**self.building_level))
                if self.resources < cost:
                    return None, INVALID_ACTION(f"Cannot upgrade building, current cost is {cost} and you only have {self.resources} available")
                self.resources -= cost
                self.building_level += 1
                self.board[HEIGHT//2][0] = [ALLIED_MAIN_BUILDING, self.building_level]

            elif isinstance(action, RecruitSoldiers):
                cost = action.getPrice()
                lx,ly = action.location
                if self.resources < cost:
                    return None, INVALID_ACTION(f"Cannot recuit soldiers, current cost is {cost} and you only have {self.resources} available")
                cell = self.board[ly][lx] 
                if cell[0] and cell[0]!=action.type:
                    return None, INVALID_ACTION(f"Cannot recruit soldiers of different type in the same location, move your soldiers first")
                self.resources -= cost
                if cell[0]:
                    self.board[ly][lx][1] += action.amount
                else:
                    self.board[ly][lx] = [action.type, action.amount]
            else:
                leftactions.append(action)
            
        return leftactions, None

    @property
    def upgrade_cost(self):
        return int(self.base_cost*(1.4**self.building_level))


    @property
    def production(self):
        return int(self.base_prod*(1.2**self.building_level))

            
    def applyActions(self, actions):
        actions = sorted(actions)
        for action in actions:
            if isinstance(action, UpgradeBase):
                cost = int(self.base_cost*(1.4**self.building_level))
                if self.resources < cost:
                    return INVALID_ACTION(f"Cannot upgrade building, current cost is {cost} and you only have {self.resources} available")
                self.resources -= cost
                self.building_level += 1
                self.board[HEIGHT//2][0] = [ALLIED_MAIN_BUILDING, self.building_level]
           
        
        self.enemyPlay()

        self.resources += int(self.base_prod*(1.2**self.building_level))
    
    def get_state_dict(self): 
        return {
            'turn': self.turn,
            'retard': self.retard, 
            'resources': self.resources,
            'production': self.production,
            'upgrade_cost': self.upgrade_cost,
            'actions_taken': self.actions_taken
        }
    

    def validateAndApplyMovements(self, actions):
        disabledRanged = [[0]*WIDTH for h in range(HEIGHT)] 
        
        visited = []

        influence = {} 

        alied_soldiers = [[None]*WIDTH for h in range(HEIGHT)]
        
        for action in actions:
            if not isinstance(action, MoveSoldiers):
                return INVALID_ACTION(action.actionID)         

            frx, fry = action.fr

            cell = self.board[fry][frx]
            if cell[0] not in alied_s:
                return INVALID_ACTION(f"Cannot move troops in {action.fr}")

            if cell[1] < action.amount:
                return INVALID_ACTION(f"Cannot move {action.amount} soldiers when you only have {cell[1]} in coord {action.fr}")

            if action.fr not in influence:
                influence[action.fr] = []

            if action.to not in influence:
                influence[action.to] = []
            
            influence[action.fr].append( (cell[0], -action.amount) )
            influence[action.to].append( (cell[0], action.amount) )
            

            if cell[0] == ALLIED_SOLDIER_RANGED:
                disabledRanged[fry][frx] += action.amount

            visited.append((frx, fry))

        for row in range(HEIGHT):
            for col in range(WIDTH):                   
                
                cell = self.board[row][col]
                if (col,row) not in influence: 
                    if cell[0] in alied_s:
                        alied_soldiers[row][col] = self.board[row][col][:]
                    continue #not affected by movement

                moveaway = [entry for entry in influence[(col,row)] if entry[1]<0]
                moveamount = -sum(entry[1] for entry in moveaway)
                currentamount = cell[1] if cell[0] in alied_s else 0
                #debug("moveamount",moveamount)
                if moveamount > currentamount: 
                    # not enought troops
                    return INVALID_ACTION(f"Cannot move {moveamount} soldiers when you only have {currentamount} in coord {(col, row)}")

                remaining = currentamount - moveamount 

                movein = [entry for entry in influence[(col,row)] if  entry[1]>0]
                #debug("movein: ", movein)
                if not movein:
                    alied_soldiers[row][col] = [cell[0], remaining] if remaining else None
                    continue
                else:
                    melees = sum([entry[1] for entry in movein if entry[0]==ALLIED_SOLDIER_MELEE]) 
                    rangeds = sum([entry[1] for entry in movein if entry[0]==ALLIED_SOLDIER_RANGED]) 

                    if remaining and ((melees and cell[0]==ALLIED_SOLDIER_RANGED) or (rangeds and cell[0]==ALLIED_SOLDIER_MELEE)):
                        return INVALID_ACTION(f"Cannot mix ranged soldiers with melee soldiers in same cell {(col, row)}, move then first or swap them in the same turn")

                    # TODO add possibility to suicide/clean melee soldiers and position ranged squad in the same turn
                    if melees and rangeds:
                        return INVALID_ACTION(f"Cannot merge ranged soldiers with melee soldiers in the same cell {(col, row)}")

                    if remaining:
                        alied_soldiers[row][col] = [cell[0], remaining + melees + rangeds]  
                    else:
                        alied_soldiers[row][col] = [ALLIED_SOLDIER_MELEE if melees else ALLIED_SOLDIER_RANGED, melees + rangeds] if melees + rangeds else None

        #first apply damage from range units
        areadamage = [(3,0),(2,1),(1,2),(0,3),(-1,2),(-2,1),(-3,0),(-2,-1),(-1,-2),(0,-3),(1,-2),(2,-1)]
        for row in range(HEIGHT):
            for col in range(WIDTH):
                cell = self.board[row][col]
                if cell[0] == ALLIED_SOLDIER_RANGED and cell[1]>disabledRanged[row][col]:
                    damage = min(500, cell[1]-disabledRanged[row][col]) #max 500 damage
                    if not damage: continue
                    if damage < 0:
                        return INVALID_ACTION(f"Negative damage on ranged units error!!")
                    for area in areadamage:
                        mx, my = area
                        nx = col + mx
                        ny = row + my 
                        if not (0<=nx<WIDTH and 0<=ny<HEIGHT): continue
                        targetcell = self.board[ny][nx]
                        if targetcell[0] in [ENEMY_SOLDIER_MELEE,ENEMY_SOLDIER_RANGED]:
                            targetcell[1] = max(0, targetcell[1]-damage)
                            if targetcell[1]==0: # kill all troops
                                self.board[ny][nx] = [None, 0]


        for row in range(HEIGHT):
            for col in range(WIDTH):
                cell = self.board[row][col]
                if alied_soldiers[row][col]:
                    if cell[0] in enemy_s:
                        self.board[row][col] = duelResult(alied_soldiers[row][col], cell)
                    else:
                        self.board[row][col] = alied_soldiers[row][col][:]
                
                elif cell[0] in alied_s:
                    self.board[row][col] = [None, 0]


        debug("State after your actions:")
        debug("\n".join([', '.join([gridstr(cell) for cell in aliedrow]) for aliedrow in self.board]))


        return None


    def enemyEngage(self, troops):
        for row in range(HEIGHT):
            for col in range(WIDTH):
                cell = self.board[row][col]
                if troops[row][col] and cell[0] in [ALLIED_MAIN_BUILDING, ALLIED_SOLDIER_MELEE, ALLIED_SOLDIER_RANGED]:
                    self.board[row][col] = duelResult(cell, [ENEMY_SOLDIER_MELEE, troops[row][col]])
                    troops[row][col] = 0
                

        
    def enemyMovement(self):
        for row in range(HEIGHT):
            cell = self.board[row][WIDTH-1]
            if cell[0] in alied_s:
                self.retard =  min(MAX_RETARD, self.retard+cell[1]/5.0)
                self.resources += cell[1]*SOLDIERS_COST[cell[0]]*2
                self.board[row][WIDTH-1] = [None, 0] 
        
        target = [0]*HEIGHT*WIDTH
        for row in range(HEIGHT):
            for col in range(WIDTH):
                cell = self.board[row][col]
                if cell[0] in [ALLIED_MAIN_BUILDING, ALLIED_SOLDIER_RANGED] or cell[0]==ALLIED_SOLDIER_MELEE and cell[1]>20:
                    target[row*WIDTH+col] = 1


        ntroops = [[0]*WIDTH for h in range(HEIGHT)]
        
        top_mask = (1<<WIDTH)-1
        bot_mask = top_mask<<((HEIGHT-1)*WIDTH)
        left_mask = 1
        right_mask = 1<<(WIDTH-1)
        for row in range(HEIGHT):
            left_mask |= left_mask<<WIDTH
            right_mask |= right_mask<<WIDTH
        

        moves = [1, -WIDTH, -1, WIDTH]
        masks = [right_mask, top_mask, left_mask, bot_mask]

        nodes=[-1]*WIDTH*HEIGHT

        for row in range(HEIGHT):
            for col in range(WIDTH):
                origincell = self.board[row][col] 
                if origincell[0] != ENEMY_SOLDIER_MELEE: continue
                visited = 1<<(row*WIDTH+col) 
                nodes[0] = row*WIDTH+col
                left = 0
                right = 1
                search = 1 
                while search:
                    node = nodes[left]
                    left += 1
                    b = 1<<node
                    for actionidx in range(4):
                        if (b & masks[actionidx]): continue
                        nextnode = node + moves[actionidx]
                        nb = 1 << nextnode
                        if (nb & visited): continue
                        
                        if target[nextnode]:
                            tx,ty = nextnode%WIDTH, nextnode//WIDTH
                            if abs(tx-col)>abs(ty-row): # prioritize y
                                ny = row
                                nx = col + (1 if tx>col else -1)
                            else:
                                nx = col
                                ny = row + (1 if ty>row else -1)
                            search = 0
                            break   
                        nodes[right] = nextnode
                        right+=1
                        visited |= nb

                
                ntroops[ny][nx] += origincell[1]
       
        
        # clear previous enemy troops
        for row in range(HEIGHT):
            for col in range(WIDTH):
                cell = self.board[row][col]
                if cell[0] in [ENEMY_SOLDIER_MELEE]:
                    self.board[row][col] = [None, 0]

        self.enemyEngage(ntroops)
        
        # reposition non-duel troops
        for row in range(HEIGHT):
            for col in range(WIDTH):
                if ntroops[row][col]:
                    if self.board[row][col][0]:
                        debug("ERROR!!")
                    self.board[row][col] = [ENEMY_SOLDIER_MELEE, ntroops[row][col]]

                

    def enemySpawn(self):
  
        spawnsoldiers = 2 + int( ( max(self.turn - self.retard, self.turn/3) **2)/65)
        if self.difficulty==0:
            cell = random.randint(0,HEIGHT-1)
        else:
            cell = self.turn%HEIGHT
        self.board[cell][WIDTH-1] = [ENEMY_SOLDIER_MELEE, spawnsoldiers]

        debug("State after enemy actions:")

        debug("\n".join([', '.join([gridstr(cell) for cell in aliedrow]) for aliedrow in self.board]))


    def setSoldier(self, soldiers):
        pass

    def outputState(self):

        Output(f"{self.building_level} {self.resources} {json.dumps(self.board, separators=(',', ':'))}")
        
    # cycle
    def readAndApplyTurnEvents(self):
        repeat = True
        while repeat:
            repeat = False
    
            try:
                actions, error = self.readActions() # 1
                if error: return error
                actions, error = self.validatePurchases(actions) # 2 
                if error: return error
                error = self.validateAndApplyMovements(actions) # 3
                if error: return error
                if self.viewer:
                    self.viewer.drawmap(self.board, self.get_state_dict()) # 5
                
            except TimeoutError:
                debug(f"ACTIONS were not read in time ({MAX_PROCESS_TIME}ms)!")
                repeat = True
             
            # enemy play
            self.enemyMovement() # 6
            self.enemySpawn() # 7
            self.resources += int(self.base_prod*(1.2**self.building_level)) # 8
            if self.viewer:
                self.viewer.drawmap(self.board, self.get_state_dict()) # 9
                
            self.turn += 1


    def readActions(self): # error handling, syntax handling (1)
        try:
            i, o, e = select.select( [sys.stdin], [], [], MAX_PROCESS_TIME/1000 )
            if not i:
                raise TimeoutError
            else:
                actions = sys.stdin.readline().strip()
            if actions=='':
                debug("No actions were taken!")
                return [], None

            if " " in actions:
                return None, COMMANDS_CANT_CONTAIN_SPACES(actions)
            actions = actions.split(";")
            if len(actions)>MAX_ACTIONS:
                return None, NUM_ACTIONS_EXCEEDED(len(actions), MAX_ACTIONS)

            parsed_actions = []
            
            for action in actions:
                actionId, *rest = action.split('|')           

                debug("Action received: ", ACTION_LABEL[int(actionId)], ' '.join(rest))
                nextaction = ACTION_MAP[int(actionId)](rest)
                if nextaction.error:
                    return None, nextaction.error
                parsed_actions.append(nextaction)
            self.actions_taken += len(parsed_actions)
            return parsed_actions, None 

        except TimeoutError:
            raise TimeoutError
        except:
            traceback.print_exc(file=sys.stderr)
            return None, INVALID_LINE_ERROR




def main():
    #Insert Argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-dif', '--difficulty', type=int, required=True,
                        help='Selects the difficulty of the simulation')
    parser.add_argument('-eval', '--evaluation', action='store_true', required=False,
                        help='Activates the evaluation mode, disabling the viewer for faster processing')
    args = vars(parser.parse_args())
    eval_mode = args['evaluation']
    level = args['difficulty']

    viewer = None if eval_mode else Viewer() 

    open(DEBUG_FILE, 'w').close()

    random.seed(int(time.time()*1000))

    debug("Difficulty is", level)
    
    env = Environment(level, viewer)    
    Output(f"{level} {env.base_cost} {env.base_prod}")
    ok = input()
    if env.viewer:
        env.viewer.drawmap(env.board, env.get_state_dict()) # 5
    while 1:
        env.outputState()
        error = env.readAndApplyTurnEvents()
        debug("SCORE: ", env.turn if env.retard<MAX_RETARD else int(MAX_T*1.5-env.turn/2), ", retard: ", env.retard)
        if env.end():
            debug("END!")
            Output("END")
            break
        elif error:
            debug("ERROR:",error)
            Output("ERROR")
            break

    time.sleep(200)

if __name__ == "__main__":
    main()