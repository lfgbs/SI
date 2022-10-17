
from utils import *
from error_msgs import *
from actions import *


UPGRADE_BUILDING = 0
RECRUIT_SOLDIERS = 1 
MOVE_SOLDIERS = 2

class Action:
    def __init__(self, actionID):
        self.actionID = actionID
        self.error = None

class UpgradeBase(Action):
    def __init__(self, arguments):
        super().__init__(UPGRADE_BUILDING)

class RecruitSoldiers(Action):
    def __init__(self, arguments):
        super().__init__(RECRUIT_SOLDIERS)
        possible_types = alied_s
        if len(arguments)!=4:
            self.error = INVALID_ACTION("Recruit soldiers requires 2 arguments, type and amount")
            return
        try:
            type, amount, lx, ly = map(int, arguments)
        except:
            self.error = NOT_INTEGER_ERROR("Type, amount and locations must be integer!")
            return

        if type not in possible_types:
            self.error = INVALID_ACTION(f"Type {type} must be one of the following: {possible_types}")
            return

        if amount <= 0:
            self.error = INVALID_ACTION(f"Amount of soldiers must be positive, requested: {amount}")
            return
        
        if not (0<=lx<WIDTH and 0<=ly<HEIGHT):
            self.error = INVALID_COORDINATES(f" location({lx, ly})")
            return
        
        if abs(lx-0)>1 or abs(VCENTER-ly)>1 or abs(lx-0)+abs(VCENTER-ly)!=1:
            self.error = INVALID_ACTION(f"Recruting position({(lx,ly)}) is not at 1 cell difference to the base({(0,VCENTER)})")
        
        self.type = type
        self.amount = amount
        self.location = (lx,ly)
        
    def getPrice(self):
        return SOLDIERS_COST[self.type]*self.amount

class MoveSoldiers(Action):
    def __init__(self, arguments):
        super().__init__(MOVE_SOLDIERS)
        possible_types = alied_s
        if len(arguments)!=5:
            self.error = INVALID_ACTION("Move soldiers requires 5 arguments, fromX, fromY, toX, toY, and amount")
            return
       
        try:
            fromX, fromY, toX, toY, amount = map(int, arguments)
        except:
            self.error = NOT_INTEGER_ERROR("amount must be integer!")
            return

        if not (0<=fromX<WIDTH and 0<=fromY<HEIGHT) or not (0<=toX<WIDTH and 0<=toY<HEIGHT):
            self.error = INVALID_COORDINATES(f" from({fromX, fromY}); to({toX, toY}) ")
            return

        mx, my = fromX-toX, fromY-toY        
        if (mx,my) not in [(1,0),(0,1),(-1,0),(0,-1)]:
            self.error = INVALID_MOVE_COORD((fromX,fromY),(toX,toY))
            return 

        
        if amount <= 0:
            self.error = INVALID_ACTION(f"Amount of soldiers must be positive, requested: {amount}")
            return

        self.fr = (fromX, fromY)
        self.to = (toX, toY)
        self.amount = amount
            