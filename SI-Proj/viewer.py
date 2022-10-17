from utils import *
import sys
import time

CELL_PIXELS = 48
CELL_INCREASE = 65
FPS =25
TIME_BETWEEN_DRAWS = 1/FPS

try:
    import pygame
    from game_objects import *
except:
    print(f"Error importing pygame modules: {sys.exc_info()[1]}", file=sys.stderr, flush=True)

class Viewer:
    def __init__(self):
        self.history = []
        
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode([WIDTH*CELL_PIXELS + 10, HEIGHT*CELL_PIXELS + 5 + CELL_INCREASE])
        self.board_history = []


    def drawmap(self, board, state_dict, saveToHistory=True, saveFrameToFile=None):
        start = time.time()
        pygame.event.get()
 
        self.screen.fill(0)
        bg = pygame.image.load(os.path.join('sprites', 'map_1.png'))

        #INSIDE OF THE GAME LOOP
        self.screen.blit(bg, (5, CELL_INCREASE))
        
        temp_board = [[[None, 0] for w in range(WIDTH)] for h in range(HEIGHT)]

        text = 'Turn ' + str(state_dict['turn']+1)
        myfont = pygame.font.SysFont('arial', 15, bold=True)
        textsurface = myfont.render(text, False, (255, 255, 255))
        text_width, text_height = myfont.size(text)
        self.screen.blit(textsurface,( 5 + (WIDTH//2)*CELL_PIXELS - text_width/2 , CELL_PIXELS - 2*text_height - 10 ))

        text = 'Current Resources: ' + str(state_dict['resources'])
        myfont = pygame.font.SysFont('arial', 15, bold=False)
        textsurface = myfont.render(text, False, (255, 255, 255))
        text_width, text_height = myfont.size(text)
        self.screen.blit(textsurface,( 5, CELL_PIXELS - 2*text_height - 10 ))

        text = 'Current Production: ' + str(state_dict['production'])
        myfont = pygame.font.SysFont('arial', 15, bold=False)
        textsurface = myfont.render(text, False, (255, 255, 255))
        text_width, text_height = myfont.size(text)
        self.screen.blit(textsurface,( 5, CELL_PIXELS - 2*text_height + 10 ))

        text = 'Base Upgrade Cost: ' + str(state_dict['upgrade_cost'])
        myfont = pygame.font.SysFont('arial', 15, bold=False)
        textsurface = myfont.render(text, False, (255, 255, 255))
        text_width, text_height = myfont.size(text)
        self.screen.blit(textsurface,( 5, CELL_PIXELS - 2*text_height + 30 ))

        vertical_line = pygame.Surface((1, HEIGHT*CELL_PIXELS), pygame.SRCALPHA)
        vertical_line.fill((255, 255, 255, 50))
        horizontal_line = pygame.Surface((WIDTH*CELL_PIXELS, 1), pygame.SRCALPHA)
        horizontal_line.fill((255, 255, 255, 50)) # You can change the 100 depending on what transparency it is.

        for row in range(HEIGHT+1):
            startpixel =  CELL_INCREASE + row * CELL_PIXELS
            self.screen.blit(horizontal_line, (5, startpixel))
        for col in range(WIDTH+1):
            startpixel =  5 + col * CELL_PIXELS
            self.screen.blit(vertical_line, (startpixel, CELL_INCREASE))


        ranged_soldier = RangedSoldier()
        stealth_melee = MeleeSoldier(stealth=True)
        melee_soldier = MeleeSoldier()
        enemy_melee = MeleeSoldier(side=1)
        enemy_ranged = RangedSoldier(side=1)
        for row in range(HEIGHT):
            for col in range(WIDTH):
                cell = board[row][col]
                temp_board[row][col] = cell[:]
                soldier = None
                building = False
                
                if cell[0]:
                    text = str(cell[1]) if cell else "-"
                    myfont = pygame.font.SysFont('consolas', 15, bold=False)
                    textsurface = myfont.render(text, False, (255, 255, 255))
                    text_width, text_height = myfont.size(text)
                    if cell[0] == ALLIED_SOLDIER_MELEE:
                        if cell[1] <= 20:
                            soldier = stealth_melee # spawn invisible soldier
                        else:
                            soldier = melee_soldier # spawn melee soldier
                    elif cell[0] == ALLIED_SOLDIER_RANGED:
                        soldier = ranged_soldier  # spawn soldier
                    elif cell[0] == ENEMY_SOLDIER_MELEE:
                        soldier = enemy_melee
                    elif cell[0] == ENEMY_SOLDIER_RANGED:
                        soldier = enemy_ranged
                    elif cell[0] == ALLIED_MAIN_BUILDING:
                        building = True
                        soldier = Building()
                        
                    if soldier:
                        soldier.rect.x = 5 + col*CELL_PIXELS   # go to x
                        soldier.rect.y = CELL_INCREASE + row*CELL_PIXELS  # go to y
                        soldier_list = pygame.sprite.Group()
                        soldier_list.add(soldier)
                        soldier_list.draw(self.screen)

                    if building:
                        myfont = pygame.font.SysFont('freesans', 18, bold=True)
                        textsurface = myfont.render(text, False, (0, 0, 0))
                        text_width, text_height = myfont.size(text)
                        #temp_surface = pygame.Surface(textsurface.get_size())
                        #temp_surface.fill((255,255,255))
                        #temp_surface.blit(textsurface, (0, 0))
                        self.screen.blit(textsurface,( 5 + (col+1)*CELL_PIXELS - text_width , CELL_INCREASE + (row+1)*CELL_PIXELS - 2*text_height - 5 ))
                    else:
                        self.screen.blit(textsurface,( 5 + (col+1)*CELL_PIXELS - text_width , CELL_INCREASE + (row+1)*CELL_PIXELS - text_height ))
                        
        pygame.display.flip()

        if saveToHistory:
            pass
            #self.board_history[self.turn] = temp_board
            self.board_history.append((temp_board,state_dict))
        wait_time = TIME_BETWEEN_DRAWS - time.time() + start
        if wait_time>0:
            time.sleep(wait_time)



    def createAndSaveMovie(self):
        pass

