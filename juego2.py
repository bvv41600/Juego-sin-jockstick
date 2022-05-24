from cgitb import reset
import collections
from email.mime import image
from pdb import Restart
import random

from errno import ENOTEMPTY
from msilib.schema import Class
from sre_constants import JUMP
from tabnanny import check
from turtle import position, update
from arcade import Sprite, calculate_hit_box_points_detailed
from numpy import tile
from pip import main
import pygame
from pygame.locals import *
from pygame import mixer
import pickle

pygame.mixer.pre_init(44100,  -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60


screen_width = 1000
screen_height = 1000

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platacormer')

#define game variebles
tile_size = 50
game_over = 0
main_menu =  True
level = 1


#load images
moon_img = pygame.image.load('img/moon.png')
bg_img = pygame.image.load('img/sky.png')
restart_img = pygame.image.load('img/restart_btn.png')
start_img = pygame.image.load('img/start_btn.png')
exit_img = pygame.image.load('img/exit_btn.png')

#load sounds
pygame.mixer.music.load('img/sound.flac')
pygame.mixer.music.play(-1, 0.0, 5000)
lava_fx = pygame.mixer.Sound('img/lava.mp3')
lava_fx.set_volume(0.2)
jump_fx = pygame.mixer.Sound('img/jump.wav')
jump_fx.set_volume(0.2)
game_over_fx = pygame.mixer.Sound('img/game_over.mp3')
game_over_fx.set_volume(0.3)

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False


        #get mause position
        pos = pygame.mouse.get_pos()

        #check mouseover and  clicked conditions
        if self.rect.collidepoint(pos):
           if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
               action = True
               self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        
        #draw button
        screen.blit(self.image, self.rect)

        return action

        

class player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 2

        if game_over == 0:
            #get keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = - 15
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]: 
                dx += 5 
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False: 
                self.counter = 0
                self.index = 0
                self.image = self.images_right[self.index]
            

            #handle animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0 
            if  self.direction == 1:
                self.image = self.images_right[self.index]
            if  self.direction == -1:
                self.image = self.images_left [self.index]

            #add gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10 

            dy += self.vel_y

            #check for collision
            self.in_air = True
            for tile in world.tile_list:
                #check for collision in x direction
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #check for collision in y direction
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below the ground i.e. jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    #check if above the ground i.e. falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False
            
            #check for  collision with  enemies
            if pygame.sprite.spritecollide(self, demon_group, False):
                game_over = -1
                game_over_fx.play()
            #check for  collision with  lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                game_over_fx.play()
                print(game_over)


            #update player  coordinates 
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            if self.rect.y:
             self.rect.y 

        #draw player onto screen
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

        return game_over

    def reset(self,x ,y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 8):
            img_right = pygame.image.load(f'img/R{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('img/ghost.gif')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True



class world():
    def __init__(self, data):
        self.tile_list = []

        #load images
        dirt_img = pygame.image.load('img/dirt.png')
        barrel_img = pygame.image.load('img/barrel.png')
        bat_gif = pygame.image.load('img/bat.gif')
        walls_img = pygame.image.load('img/walls.png')
        rock_img = pygame.image.load('img/rock.png')
        
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile =(img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(barrel_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile =(img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    img = pygame.transform.scale(bat_gif, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile =(img, img_rect)
                    self.tile_list.append(tile)
                if tile == 4:
                    img = pygame.transform.scale(walls_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile =(img, img_rect)
                    self.tile_list.append(tile)
                if tile == 5:
                    img = pygame.transform.scale(rock_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile =(img, img_rect)
                    self.tile_list.append(tile)
                if tile == 6:
                    demon = Enemy(col_count * tile_size, row_count * tile_size + -15)
                    demon_group.add(demon)
                if tile == 7:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)

                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            pygame.draw.rect(screen, (255, 255, 255), tile[1], 2)

class Enemy(pygame.sprite.Sprite):
    def __init__(self,x ,y):
        pygame.sprite.Sprite.__init__(self)
        demon_fx.play()
        self.image = pygame.image.load('img/demon.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direccion = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direccion
        self.move_counter += 1
        if abs(self.move_counter) > 100:
            self.move_direccion *= -1
            self.move_counter *= -1

class Lava(pygame.sprite.Sprite):
    def __init__(self,x ,y):
        pygame.sprite.Sprite.__init__(self)
        lava_fx.play()
        img = pygame.image.load('img/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
world_data = [
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,0,0,0,0,3,3,3,0,0,0,0,0,0,0,0,3,3,0,1],
[1,0,0,0,0,0,0,3,3,3,0,0,0,0,0,3,3,3,3,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,3,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,5,5,0,0,0,4,2,0,0,1],
[1,0,6,0,0,6,0,0,0,2,0,0,0,0,4,4,4,0,0,1],
[1,0,4,4,4,4,0,0,5,5,0,0,0,4,0,0,0,0,0,1],
[1,0,0,4,4,0,0,0,0,0,0,0,0,0,5,4,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,5,0,0,6,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,5,5,0,0,4,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,1],
[1,0,0,4,0,0,0,0,0,0,0,2,2,0,0,6,0,0,0,1],
[1,0,4,4,4,0,0,0,0,0,4,4,4,4,4,4,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,4,7,7,4,4,4,7,7,7,4,4,1],
[1,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]





player = player(150, screen_height - 150)

demon_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()

world = world(world_data)

#create buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 400,screen_height // 2, start_img )
exit_button = Button(screen_width // 2 + 150,screen_height // 2, exit_img )


run = True
while run:

    clock.tick(fps)

    screen.blit(bg_img, (0,0))
    screen.blit(moon_img, (150,150))

    if main_menu == True:
        if start_button.draw():
            main_menu = False
        if exit_button.draw():
            run = False
    else:
        world.draw()

        if game_over == 0:  
            demon_group.update()

        demon_group.draw(screen)
        lava_group.draw(screen)

        game_over = player.update(game_over)

        #if player has died
        if game_over ==  -1:
            if restart_button.draw():
                player.reset(150, screen_height - 150)
                game_over = 0


    print(world.tile_list)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()