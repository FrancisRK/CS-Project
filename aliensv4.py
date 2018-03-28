#!/usr/bin/env python

import random, os.path

#import basic pygame modules
import pygame
from pygame.locals import *

#see if we can load more than standard BMP
if not pygame.image.get_extended():
    raise SystemExit("Sorry, extended image module required")


#game constants
MAX_SHOTS      = 2       #most player bullets onscreen
ALIEN_ODDS     = 22      #chances a new alien appears
BOMB_ODDS      = 500     #chances a new bomb will drop
ALIEN_RELOAD   = 4       #frames between new aliens
SCREENRECT     = Rect(0, 0, 640, 480)
SCORE          = 0

# Define program directory

main_dir = os.path.split(os.path.abspath(__file__))[0]

# Define utility functions

def load_image(file, transparent):
    "loads an image, prepares it for play"
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))
    if transparent: # Sets areas of image which are transparent to be the same colour as the surface background
        corner = surface.get_at((50, 0))
        surface.set_colorkey(corner, RLEACCEL)
    return surface.convert()

def load_images(*files):
    imgs = []
    for file in files:
        imgs.append(load_image(file, 0))
    return imgs


class dummysound:
    def play(self): pass

def load_sound(file):
    if not pygame.mixer: return dummysound()
    file = os.path.join(main_dir, 'data', file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print ('Warning, unable to load, %s' % file)
    return dummysound()



# each type of game object gets an init and an
# update function. the update function is called
# once per frame, and it is when each object should
# change it's current position and state. the Player
# object actually gets a "move" function instead of
# update, since it is passed extra information about
# the keyboard


class Player(pygame.sprite.Sprite):
    speed = 10
    bounce = 24
    gun_offset = -11
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = -1

    def move(self, direction):
        if direction: self.facing = direction
        self.rect.move_ip(direction*self.speed, 0)
        self.rect = self.rect.clamp(SCREENRECT)
        if direction < 0:
            self.image = self.images[0]
        elif direction > 0:
            self.image = self.images[1]
        self.rect.top = self.origtop - (self.rect.left//self.bounce%2)

    def gunpos(self):
        pos = self.facing*self.gun_offset + self.rect.centerx
        return pos, self.rect.top


class Alien(pygame.sprite.Sprite):
    speed = 5
    animcycle = 12
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.facing = random.choice((-1,1)) * Alien.speed
        self.frame = 0
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        self.rect.move_ip(self.facing, 0)
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing;
            #self.rect.top = self.rect.bottom + 1
            self.rect = self.rect.clamp(SCREENRECT)
        self.frame = self.frame + 1
        self.image = self.images[self.frame//self.animcycle%3]

################################################################################

class Bossleft(pygame.sprite.Sprite):
    speed = 0
    animcycle = 12
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.frame = 0
        self.rect.center = (270,200)
        self.speed = 0

    def update(self):
        self.rect.move_ip(Bossleft.speed,0)
        if not SCREENRECT.colliderect(self.rect):
            self.kill()
#            Bossleft.speed = -Bossleft.speed
#            self.rect.top = self.rect.bottom + 1
#            self.rect = self.rect.clamp(SCREENRECT)
#        self.frame = self.frame + 1
#        self.image = self.images[self.frame//self.animcycle%3]

class Bossright(pygame.sprite.Sprite):
    speed = 0
    animcycle = 12
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.frame = 0
        self.rect.center = (370,200)
        self.speed = 0

    def update(self):
        self.rect.move_ip(Bossright.speed,0)
        if not SCREENRECT.colliderect(self.rect):
            self.kill()
#            Bossright.speed = -Bossright.speed
#            self.rect.top = self.rect.bottom + 1
#            self.rect = self.rect.clamp(SCREENRECT)
#        self.frame = self.frame + 1
#        self.image = self.images[self.frame//self.animcycle%3]

class Shield(pygame.sprite.Sprite):
    speed = 0
    animcycle = 12
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.health = 10 + random.choice((0,5))
#        self.facing = 0
        self.frame = 0
#        if self.facing == 0:
        self.rect.center = (320,260)

    def update(self):
        self.rect.move_ip(0, 0)
        self.frame = self.frame + 1
        self.image = self.images[self.frame//self.animcycle%3]



################################################################################

class Explosion(pygame.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife

    def update(self):
        self.life = self.life - 1
        self.image = self.images[self.life//self.animcycle%2]
        if self.life <= 0: self.kill()


class Shot(pygame.sprite.Sprite):
    speed = -11
    images = []
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top <= 0:
            self.kill()


class Bomb(pygame.sprite.Sprite):
    speed = 9
    images = []
    def __init__(self, alien):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=
                    alien.rect.move(0,5).midbottom)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom >= 470:
            Explosion(self)
            self.kill()


class Score(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = Color('white')
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self):
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = "Score: %d" % SCORE
            self.image = self.font.render(msg, 0, self.color)


class Finalscore(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 50)
        self.font.set_italic(1)
        self.color = Color('white')
        msg = "Score: %d" % SCORE
        self.image = self.font.render(msg, 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = SCREENRECT.center

def main(winstyle = 0):
    # Initialize pygame
    #pygame.init()
    pygame.display.init()
    pygame.font.init()

    if pygame.mixer and not pygame.mixer.get_init():
        print ('Warning, no sound')
        pygame.mixer = None

    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    #Load images, assign to sprite classes
    #(do this before the classes are used, after screen setup)
    img = load_image('player1.gif', 0)
    Player.images = [img, pygame.transform.flip(img, 1, 0)]
    img = load_image('explosion1.gif', 0)
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]
    Alien.images = load_images('alien1.gif', 'alien2.gif', 'alien3.gif')
    Bossleft.images = [load_image('bossleftsmallv2.png', 1)]
    Bossright.images = [load_image('bossrightsmallv2.png', 1)]
    Shield.images = load_images('shield1.gif','shield2.gif','shield3.gif')
    Bomb.images = [load_image('bomb.gif', 0)]
    Shot.images = [load_image('shot.gif', 0)]

    #decorate the game window
    icon = pygame.transform.scale(Alien.images[0], (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Pygame Aliens')
    pygame.mouse.set_visible(0)

    #create the background, tile the bgd image
    bgdtile = load_image('background.gif', 0)
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    #load the sound effects
    boom_sound = load_sound('boom.wav')
    shoot_sound = load_sound('car_door.wav')
    if pygame.mixer:
        music = os.path.join(main_dir, 'data', 'house_lo.wav')
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)

    # Initialize Game Groups
    aliens = pygame.sprite.Group()
    bosslefts = pygame.sprite.GroupSingle()
    bossrights = pygame.sprite.GroupSingle()
    shields = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    all = pygame.sprite.RenderUpdates()
    lastalien = pygame.sprite.GroupSingle()

    # Assign default groups to each sprite class
    Player.containers = all
    Alien.containers = aliens, all, lastalien
    Bossleft.containers = bosslefts, all
    Bossright.containers = bossrights, all
    Shield.containers = shields, all
    Shot.containers = shots, all
    Bomb.containers = bombs, all
    Explosion.containers = all
    Score.containers = all

    # Create Some Starting Values
    global score
    alienreload = ALIEN_RELOAD
    kills = 0
    clock = pygame.time.Clock()

    # Initialize our starting sprites
    global SCORE
    player = Player()
    Alien() #note, this 'lives' because it goes into a sprite group
    Bossleft()
    Bossright()
    shield = Shield()
    if pygame.font:
        all.add(Score())

    while player.alive():

        #get input
        for event in pygame.event.get():
            if event.type == QUIT or \
                (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return
        keystate = pygame.key.get_pressed()

        # clear/erase the last drawn sprites
        all.clear(screen, background)

        #update all the sprites
        all.update()

        #handle player input
        direction = keystate[K_RIGHT] - keystate[K_LEFT]
        player.move(direction)
        firing = keystate[K_SPACE]
        if not player.reloading and firing and len(shots) < MAX_SHOTS:
            Shot(player.gunpos())
            shoot_sound.play()
        player.reloading = firing

        # Create new alien
        if alienreload:
            alienreload = alienreload - 1
        elif len(aliens) < 10: #not int(random.random() * ALIEN_ODDS):
            Alien()
            alienreload = ALIEN_RELOAD

#        if SCORE == 10 and len(bosslefts) < 1:
#            Bossleft()

        # Drop bombs
        for a in aliens:
            if a and not int(random.random() * BOMB_ODDS):
                Bomb(a)

        # Detect collisions
        for alien in pygame.sprite.spritecollide(player, aliens, 1):
            boom_sound.play()
            Explosion(alien)
            Explosion(player)
            SCORE = SCORE + 1
            player.kill()

        for alien in pygame.sprite.groupcollide(shots, aliens, 1, 1).keys():
            boom_sound.play()
            Explosion(alien)
            SCORE = SCORE + 1

        for bomb in pygame.sprite.spritecollide(player, bombs, 1):
            boom_sound.play()
            Explosion(player)
            Explosion(bomb)
            player.kill()

################################################################################

        pygame.sprite.groupcollide(shields, bombs, 0, 1)
        pygame.sprite.groupcollide(bosslefts, bombs, 0, 1)
        pygame.sprite.groupcollide(bossrights, bombs, 0, 1)

        if shield.health > 0:
            if pygame.sprite.groupcollide(shields, shots, 0, 1):
                shield.health = shield.health - 1

        else:
            if pygame.sprite.groupcollide(shields, shots, 1, 1):
                Bossleft.speed = -5
                Bossright.speed = 7


        if len(shields) == 0:
            if pygame.sprite.groupcollide(bosslefts, shots, 1, 1):
                SCORE = SCORE + 5
            if pygame.sprite.groupcollide(bossrights, shots, 1, 1):
                SCORE = SCORE + 10

################################################################################

        #draw the scene
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        #cap the framerate
        clock.tick(40)

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)

    # Final screen and score displaying

    finalscreen = load_image('finalscreen.png', 0)
    screen.blit(finalscreen, (0,0))
    pygame.display.flip()
    all.empty()
    all.add(Finalscore())
    dirty = all.draw(screen)
    pygame.display.update(dirty)

    pygame.time.wait(2000)
    pygame.quit()



#call the "main" function if running this script
if __name__ == '__main__': main()
