#python3 pipe.py python3 server.py -dif 0 -- python3 client.py 
from operator import pos
from pickletools import read_unicodestringnl
import sys
from turtle import position

from actions import *
from utils import *
from utils import _PRINT

import json
import numpy as np

from functools import partial
from time import perf_counter
import random


DEBUG_FILE = "client_debug.txt"

def debug(*args):
    _PRINT(*args, file=sys.stderr, flush=True)
    with open(DEBUG_FILE, 'a') as f:
        stdout, sys.stdout = sys.stdout, f # Save a reference to the original standard output
        _PRINT(*args)
        sys.stdout = stdout

print = debug # dont erase this line, otherwise you cannot use the print function for debug 

def upgradeBase():
    return f"{UPGRADE_BUILDING}"

def recruitSoldiers(type, amount, location=(1,VCENTER)):
    return f"{RECRUIT_SOLDIERS}|{type}|{amount}|{location[0]}|{location[1]}".replace(" ","")

def moveSoldiers(pos, to, amount):
    return f"{MOVE_SOLDIERS}|{pos[0]}|{pos[1]}|{to[0]}|{to[1]}|{amount}".replace(" ","")

def playActions(actions):
    _PRINT(';'.join(map(str,actions)), flush=True)



# ENVIRONMENT
class Environment:
    def __init__(self, difficulty, base_cost, base_prod):
        self.difficulty = difficulty
        self.resources = 0
        self.building_level = 0
        self.base_cost = base_cost
        self.base_prod = base_prod
        self.board = [[None]*WIDTH for h in range(HEIGHT)]
        playActions([])

    @property
    def upgrade_cost(self):
        return int(self.base_cost*(1.4**self.building_level))


    @property
    def production(self):
        return int(self.base_prod*(1.2**self.building_level))


    def readEnvironment(self):
        state = input()
        
        if state in ["END", "ERROR"]:
            return state
        level, resources, board = state.split()
        level = int(level)
        resources = int(resources)
        debug(f"Building Level: {level}, Current resources: {resources}")
        self.building_level = level
        self.resources = resources
        self.board = json.loads(board)

        # uncomment next lines to use numpy array instead of array of array of array (3D array)
        # IT IS RECOMMENDED for simplicity
        # arrays to numpy converstion:  self.board[y][x][idx] => self.board[x,y,idx] 
        #
        self.board = np.swapaxes(np.array(json.loads(board)),0,1)
        #debug(self.board.shape)

    #calculates distance between two soldiers
    def distance(self, soldier1, soldier2):
        #return math.sqrt( (soldier1[0]-soldier2[0])**2 + (soldier1[1]-soldier2[1])**2 )
        return abs(soldier1[0]-soldier2[0])+abs(soldier1[1]-soldier2[1])

    #returns the position one tile to the right
    def right(self, soldier):
        return (soldier[0]+1, soldier[1])
    
    #returns the position one tile to the left
    def left(self, soldier):
        return (soldier[0]-1, soldier[1])

    #returns the position one tile to the left
    def left(self, soldier):
        return (soldier[0]-1, soldier[1])

    #returns the position one tile up
    def up(self, soldier):
        return (soldier[0], soldier[1]-1)

    #returns the position one tile down
    def down(self, soldier):
        return (soldier[0], soldier[1]+1)

    #calculates and returns best next position based on surrounding enemies and ranged soldiers 
    def dodge(self, soldier, neighbouring_enemies, frontline_m):
        if soldier[0]==frontline_m:
            return None

        #se estiver nas pontas faz dodge para dentro do campo
        if soldier[1]==0:
            return self.down(soldier)
        if soldier[1]==10:
            return self.up(soldier)

        if neighbouring_enemies:
            enemies_above=[enemy for enemy in neighbouring_enemies if enemy[1]<soldier[1]]
            enemies_below=[enemy for enemy in neighbouring_enemies if enemy[1]>soldier[1]]

            if enemies_above and not enemies_below:
                return self.down(soldier) 
            elif enemies_below and not enemies_above:
                return self.up(soldier)
            else:
                return self.up(soldier) #ainda não tem em conta qual dos inimigos tem menos tropas na posição
        else:
            return self.up(soldier)

    #deve retorner a posição para a qual o batalhão se deve movimentar
    def bait(self, soldier, melee, melee_formation, enemies):
        positions=[self.up(soldier), self.down(soldier)]
        valid_positions=[position for position in positions if position[1]>=0 and position[1]<=self.board.shape[1]-1]
        positions=[position for position in valid_positions if all(self.distance(position, enemy)>=2 for enemy in enemies) ] #filtra para opções de não perigo e válidas
        
        if positions:
            return random.choice(positions)

        return random.choice(valid_positions)

    def scatter(self, soldier, enemies, actions): #existe porque deveria ter-se em conta os inimigos nas proximidades mas de momento ainda nao o faz
        actions.append(moveSoldiers(soldier, self.right(soldier), min(self.board[soldier[0], soldier[1], 1]-21, 20 ))) #deixar apenas 21 ou enviar até 20

            

    #calculates and returns best next position based on surrounding enemies and ranged soldiers 
    def move_battalion(self, battalion, target_position, neighbouring_enemies=None):
        #todas as posiçoes que o batalhao pode ocupar
        positions=[self.right(battalion), self.left(battalion), self.up(battalion), self.down(battalion)]

        
        #dicionario com distancia de cada posição ao target
        positions.sort( key=partial(self.myKeyDistance, position=target_position) ) #sort for closest
    
        #returning first element
        return positions[0]

    def dispatch(self, battalion, ranged_formation, target_batallion_size, neighbouring_enemies=None):
        needed=[ranged for ranged in ranged_formation if ranged[0]==battalion[0] and self.distance(ranged, battalion)==1 and self.board[ranged[0], ranged[1], 1]<target_batallion_size]

        if battalion[1]==1 or battalion[1]==self.board.shape[1]-2:
            if needed:
                return needed[0]
        
            return self.left(battalion)

        if battalion[1]<self.board.shape[1]//2:
            if needed:
                return needed[0]
                
            if self.up(battalion) in ranged_formation:
                return self.up(battalion) 
            else:
                return None

        if battalion[1]>self.board.shape[1]//2:
            if needed:
                return needed[0]

            if self.up(battalion) in ranged_formation: 
                return self.down(battalion)
            else:
                return None


        ranged_formation_up=[ranged for ranged in ranged_formation if ranged[0]==battalion[0] and ranged[1]<battalion[1]]
        ranged_formation_down=[ranged for ranged in ranged_formation if ranged[0]==battalion[0] and ranged[1]>battalion[1]]

        avg_up=0
        avg_down=0

        if ranged_formation_up:
            for ranged in ranged_formation_up:
                avg_up+=self.board[ranged[0], ranged[1], 1]
            avg_up=avg_up/len(ranged_formation_up)

        if ranged_formation_down:
            for ranged in ranged_formation_down:
                avg_down+=self.board[ranged[0], ranged[1], 1]
            avg_down=avg_down/len(ranged_formation_down)

        if avg_up<avg_down:
            return self.up(battalion)
        
        return self.down(battalion)

    #serve para ordenar pela coluna
    def myKey(self, element):
        return element[0]
    
    #serve para ordenar pela distância a uma posição
    def myKeyDistance(self, element, position):
        return self.distance(element, position)  

    #serve para ordenar pela quantidade de tropas numa posição
    def myKeyAmount(self, position):
        return self.board[position[0], position[1], 1]      

    def get_formation(self, frontline_ranged_x):

        frontline_ranged=[]

        for j in range(self.board.shape[0]-5): 
            for i in range(1,self.board.shape[1]-1): #para cada posição no caluna x e nas 3 antecedentes entre 1 e height-1
                frontline_ranged.append((frontline_ranged_x-j, i)) # as posições já ficam sorted por coluna da mais alta para a mais baixa
        
        frontline_melee=[(frontline_ranged_x+1 ,2), (frontline_ranged_x+1,self.board.shape[1]-3)]

        return frontline_ranged, frontline_melee

    #se não for necessário fugir devolve None, caso contrário devolve a posição para a qual o batalhão se deve movimentar
    def flee(self, battalion, ranged ,enemies):
                
        if enemies :
            enemies.sort(key=partial(self.myKeyDistance, position=battalion))
            closest_enemy=enemies[0]

            #ainda só foge para a esquerda, qaundo estão encostados ao canto isto resulta numa situação impossível e crasha
            #foge se tiver um inimigo a 1 tile de distância. 
            if self.distance(battalion, closest_enemy)==1:
                atacking_ranged=[soldier for soldier in ranged if self.distance(soldier, closest_enemy)==3 and self.board[soldier[0], soldier[1], 1]>=self.board[closest_enemy[0], closest_enemy[1], 1] ]
                atacking_ranged_power=0
                for ranged in atacking_ranged:
                    atacking_ranged_power+=min(self.board[ranged[0], ranged[1], 1], 500) #só atacam 500
                if atacking_ranged_power>=self.board[closest_enemy[0], closest_enemy[1],1]:
                    return None
                else:
                    return self.left(battalion)

        return None

    def check_formation(self, ranged, formation_positions, target_battalion_size, enemies, actions):

        ranged_formation=formation_positions[0]
        
        #remover posições ocupadas por inimigos
        ranged_formation=[position for position in ranged_formation if self.board[position[0], position[1], 0]==None or self.board[position[0], position[1], 0]==3 ]
        
        threats=[enemy for enemy in enemies if any(self.distance(enemy, battalion)<=3 for battalion in ranged_formation)]

        if threats:
        
            for position in ranged_formation:

                flee=self.flee(position, ranged,enemies)

                if flee:
                    actions.append(moveSoldiers(position, flee , self.board[position[0], position[1], 1]))
                else:

                     #soldados fora da formação
                    ranged_out_of_formation=[soldier for soldier in ranged if (soldier[0]<position[0] or soldier not in ranged_formation) and self.board[soldier[0], soldier[1],1]>0]
            

                    troops_needed_in_position=0

                    if self.board[position[0], position[1], 0]==None or self.board[position[0], position[1], 0]==3:   
                        troops_needed_in_position=target_battalion_size-self.board[position[0], position[1], 1]
                    
                    while troops_needed_in_position>0 and ranged_out_of_formation!=[]:
                        
                        ranged_out_of_formation.sort( key=partial(self.myKeyDistance, position=position) ) #sort for closest
                        battalion_to_move=ranged_out_of_formation[0] #we want to move the battalion closest to our target position

                        #mexe a interseção entre a quantidade que precisa e a quantidade existente na posição mais próxima
                        number_of_moving_troops=min([self.board[battalion_to_move[0], battalion_to_move[1], 1], troops_needed_in_position] )
                    
                        actions.append(moveSoldiers(battalion_to_move, self.move_battalion(battalion_to_move, position), number_of_moving_troops))

                        troops_needed_in_position-=number_of_moving_troops
                        self.board[battalion_to_move[0], battalion_to_move[1], 1]-=number_of_moving_troops

                        ranged_out_of_formation=[soldier for soldier in ranged_out_of_formation if self.board[soldier[0], soldier[1], 1]>0]

                    if self.board[position[0], position[1], 1]>target_battalion_size:
                        new_pos=self.dispatch(position, ranged_formation,target_battalion_size) 
                        if new_pos:
                            actions.append(moveSoldiers(position, new_pos, self.board[position[0], position[1], 1]-target_battalion_size))

            for ranged in ranged_out_of_formation:
                actions.append(moveSoldiers(position, self.right(ranged), self.board[position[0], position[1], 1]))
                
                        
            return None
        
        else: #avançar no terreno se não houver ameaças
            if ranged_formation[0][0]<self.board.shape[0]-4:
                for soldier in ranged:
                    actions.append(moveSoldiers(soldier, self.right(soldier),  self.board[soldier[0], soldier[1], 1]))

                return 1
            else:
                return None
       

    def play(self): # agent move, call playActions only ONCE

        actions = []
        print("Current production per turn is:", self.production)
        print("Current building cost is:", self.upgrade_cost)

        #leitura do estado do mapa
        enemies=[]
        melee_stealth=[]
        melee=[]
        ranged=[]

        for line in range(self.board.shape[1]):
            for column in range(self.board.shape[0]):
                if self.board[column, line, 0]==4:
                    enemies.append((column, line))
                elif self.board[column, line, 0]==3:
                    ranged.append((column, line))
                elif self.board[column, line, 0]==2 and self.board[column, line, 1]<=20:
                    melee_stealth.append((column, line))
                elif self.board[column, line, 0]!=None and self.board[column, line, 0]!=1:
                    melee.append((column, line))

        ranged.sort(key=self.myKey, reverse=True)
        frontline_r=ranged[0][0]
        frontline_m=frontline_r+1
        formation_positions=self.get_formation(frontline_r)

         #o tamanho do batalhão é conforme o nº de inimigos
        if enemies:
            #média
            total_enemies=sum([self.board[enemy[0], enemy[1], 1] for enemy in enemies])
            avg_enemy_size=int(total_enemies/len(enemies))
            battalion_size=min(avg_enemy_size, 500)
        else:
            avg_enemy_size=0
            battalion_size=10

        if self.resources - 22*SOLDIER_MELEE_COST >= self.upgrade_cost and self.building_level<10: # upgrade building

            actions.append(upgradeBase())
            self.resources -= self.upgrade_cost

        """ if self.resources>=22*SOLDIER_MELEE_COST:
            actions.append(recruitSoldiers(2, 11, (0,6))) 
            actions.append(recruitSoldiers(2, 11, (0,4))) 
            self.resources -= 22*SOLDIER_MELEE_COST """

        if self.building_level<10:
            if self.resources>=22*SOLDIER_MELEE_COST:
                actions.append(recruitSoldiers(2, 11, (0,6))) 
                actions.append(recruitSoldiers(2, 11, (0,4))) 
                self.resources -= 22*SOLDIER_MELEE_COST 
        else:
            num_melee=self.resources//SOLDIER_MELEE_COST
            actions.append(recruitSoldiers(2, num_melee//2, (0,6)))
            actions.append(recruitSoldiers(2, num_melee//2, (0,4)))
            self.resources -= num_melee*SOLDIER_MELEE_COST



        
        #se depois de todas as outras compras ainda houver recursos para pelo menos 10 soldados ranged, gastar todo o dinheiro possível em soldados ranged
        """ if self.building_level<20:
            if self.resources>=10*SOLDIER_RANGED_COST:
                actions.append(recruitSoldiers(3, 10, (1,5))) 
        else:
            num_ranged=self.resources//SOLDIER_RANGED_COST
            actions.append(recruitSoldiers(3, num_ranged, (1,5))) """ 

        if self.resources>=10*SOLDIER_RANGED_COST:
                actions.append(recruitSoldiers(3, 10, (1,5)))

        
        #Ranged Actions
        move_up_flag=self.check_formation(ranged,formation_positions, battalion_size ,enemies, actions)

        #melee actions
        melee_formation=formation_positions[1]

        for soldier in melee:
           
            if move_up_flag:
                if soldier[0]<=frontline_m:
                    actions.append(moveSoldiers(soldier, self.right(soldier),  self.board[soldier[0], soldier[1], 1]))
                elif self.flee(soldier, ranged, enemies):
                    neighbouring_enemies=[enemy for enemy in enemies if self.distance(soldier, enemy)<=2]
                    actions.append(moveSoldiers(soldier, self.bait(soldier, melee, melee_formation, neighbouring_enemies) , self.board[soldier[0], soldier[1], 1]))
                continue
            
            else:
                
                if self.flee(soldier, ranged, enemies) and soldier[0]>=frontline_m:
                    neighbouring_enemies=[enemy for enemy in enemies if self.distance(soldier, enemy)<=2]
                    actions.append(moveSoldiers(soldier, self.bait(soldier, melee, melee_formation, neighbouring_enemies) , self.board[soldier[0], soldier[1], 1]))
                    continue

                if self.board[soldier[0], soldier[1], 1]>=50 and soldier[0]>=frontline_m:
                    actions.append(moveSoldiers(soldier, self.right(soldier) , self.board[soldier[0], soldier[1], 1]))
                    continue

                if soldier in melee_formation:
                    if self.board[soldier[0], soldier[1], 1]>21:
                        neighbouring_enemies=[enemy for enemy in enemies if self.distance(soldier, enemy)<=3]
                        self.scatter(soldier, neighbouring_enemies, actions)
                else:
                    if soldier[0]==0 and not (soldier[1]==0 or soldier[1]==self.board.shape[1]-1):
                        if soldier[1]<self.board.shape[1]//2:
                            if soldier[1]>0:
                                actions.append(moveSoldiers(soldier, self.up(soldier) , self.board[soldier[0], soldier[1], 1]))
                        else:
                            if soldier[1]<self.board.shape[1]-1:
                                actions.append(moveSoldiers(soldier, self.down(soldier) , self.board[soldier[0], soldier[1], 1]))
                                
                        continue

                    melee_formation.sort(key=partial(self.distance, soldier))
                    actions.append(moveSoldiers(soldier, self.move_battalion(soldier, melee_formation[0]) , self.board[soldier[0], soldier[1], 1]))
                             
            
        #melee stealth actions
        for soldier in melee_stealth:
            if not soldier[0] and soldier[1]<10 and soldier[1]>0:
                if soldier[1]<5:
                    actions.append(moveSoldiers(soldier, self.up(soldier),  self.board[soldier[0], soldier[1], 1]))
                else:
                    actions.append(moveSoldiers(soldier, self.down(soldier),  self.board[soldier[0], soldier[1], 1]))
            else:
                #evitar conflito com move_up
                if move_up_flag and soldier[0]<=frontline_m:
                    actions.append(moveSoldiers(soldier, self.right(soldier),  self.board[soldier[0], soldier[1], 1]))
                
                else:

                    direct_enemies=[enemy for enemy in enemies if enemy[1]==soldier[1] and self.distance(soldier, enemy)<=2] #inimigos na mesma linha e próximos
                    direct_enemies.sort(key=partial(self.myKeyDistance, soldier)) #sort para que o mais próximo fique no inicio da lista

                    if direct_enemies !=[] and soldier[0]>frontline_r:
                        neighbouring_enemies=[enemy for enemy in enemies if (self.distance(direct_enemies[0], enemy)<=2 and direct_enemies[0][0]<=enemy[0]) or (self.distance(soldier, enemy)<=2 and soldier[0]<=enemy[0])] #inimigos que não estão na mesma linha mas representam perigo se mudar de linha
                        
                        new_pos=self.dodge(soldier, neighbouring_enemies, frontline_m)
                        if new_pos:
                            actions.append(moveSoldiers(soldier, new_pos ,  self.board[soldier[0], soldier[1], 1]))

                    else:
                        actions.append(moveSoldiers(soldier, self.right(soldier),  self.board[soldier[0], soldier[1], 1]))
        
        

        playActions(actions)
        

def main():
    
    open(DEBUG_FILE, 'w').close()
    difficulty, base_cost, base_prod = map(int,input().split())
   
    env = Environment(difficulty, base_cost, base_prod)

    while 1: 
        signal = env.readEnvironment()
        if signal=="END":
            debug("GAME OVER")
            sys.exit(0)
        elif signal=="ERROR":
            debug("ERROR")
            sys.exit(1)

        start=perf_counter()
        env.play()
        end=perf_counter()

        #verifica se nós nalgum ciclo excedmos o tempo computacional de 200ms
        if end-start>=0.2:
            print("WARNING SURPASSED 200ms")
            exit(1)

if __name__ == "__main__":
    main()


