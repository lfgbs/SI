import pygame
import os

ALPHA = (0, 255, 0)

class MeleeSoldier(pygame.sprite.Sprite):
    """
    Spawn a melee soldier
    """

    def __init__(self, side=0, stealth=False):
        pygame.sprite.Sprite.__init__(self)
        self.images = []

        if side == 0:
            if stealth:
                img = pygame.image.load(os.path.join('sprites', 'melee_stealth.png')).convert()
            else:
                img = pygame.image.load(os.path.join('sprites', 'melee_alpha.png')).convert()
        else:
            img = pygame.image.load(os.path.join('sprites', 'melee_enemy.png')).convert()
        img.convert_alpha()     # optimise alpha
        img.set_colorkey(ALPHA) # set alpha
        self.images.append(img)
        self.image = self.images[0]
        self.rect = self.image.get_rect()

class RangedSoldier(pygame.sprite.Sprite):
    """
    Spawn a ranged soldier
    """

    def __init__(self, side=0):
        pygame.sprite.Sprite.__init__(self)
        self.images = []

        if side == 0:
            img = pygame.image.load(os.path.join('sprites', 'ranged_alpha.png')).convert()
        else:
            img = pygame.image.load(os.path.join('sprites', 'ranged_enemy.png')).convert()
        img.convert_alpha()     # optimise alpha
        img.set_colorkey(ALPHA) # set alpha
        self.images.append(img)
        self.image = self.images[0]
        self.rect = self.image.get_rect()


class Building(pygame.sprite.Sprite):
    def __init__(self, side=0):
        pygame.sprite.Sprite.__init__(self)
        self.images = []

        if side == 0:
            img = pygame.image.load(os.path.join('sprites', 'base_alpha.png')).convert()
        #else:
            #img = pygame.image.load(os.path.join('sprites', 'ranged_enemy.png')).convert()
        img.convert_alpha()     # optimise alpha
        img.set_colorkey(ALPHA) # set alpha
        self.images.append(img)
        self.image = self.images[0]
        self.rect = self.image.get_rect()