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

class Shield(pygame.sprite.Sprite):
    speed = 0
    animcycle = 12
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.frame = 0
        self.rect.center = (320,260)

    def update(self):
        self.rect.move_ip(0, 0)
        self.frame = self.frame + 1
        self.image = self.images[self.frame//self.animcycle%3]


class Shieldbutton(pygame.sprite.Sprite):
    speed = 0
    animcycle = 12
    images = []
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.health = 9 + random.choice((0,5))
        self.frame = 0
        self.rect.center = (320,280)

    def update(self):
        self.rect.move_ip(0, 0)
        self.frame = self.frame + 1
        self.image = self.images[self.frame//self.animcycle%3]


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


class Points(pygame.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.midbottom)
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
        self.font = pygame.font.Font(None, 30)
        self.font.set_italic(1)
        self.color = Color('yellow')
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 400)

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
        self.color = Color('yellow')
        msg = "Score: %d" % SCORE
        self.image = self.font.render(msg, 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = SCREENRECT.center

def main(winstyle = 0):
    # Initialize pygame
    pygame.display.init()
    pygame.font.init()

    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    # Load images, assign to sprite classes
    # (do this before the classes are used, after screen setup)
    img = load_image('player1.gif', 0)
    Player.images = [img, pygame.transform.flip(img, 1, 0)]
    img = load_image('explosion1.gif', 0)
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]
    Points.images = load_images('onepoint1.gif','onepoint2.gif','onepoint3.gif')
    Alien.images = load_images('newalien1.gif', 'newalien2.gif', 'newalien3.gif')
    Bossleft.images = [load_image('bossleftsmallv2.png', 1)]
    Bossright.images = [load_image('bossrightsmallv2.png', 1)]
    Shield.images = load_images('shield1.gif','shield2.gif','shield3.gif')
    Shieldbutton.images = load_images('shieldbutton1.gif','shieldbutton2.gif','shieldbutton3.gif')
    Bomb.images = [load_image('bomb.gif', 0)]
    Shot.images = [load_image('shot.gif', 0)]
    finalscreen = load_image('finalscreen.png', 0)

    # Decorate the game window
    icon = pygame.transform.scale(Alien.images[0], (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Pygame Aliens')
    pygame.mouse.set_visible(0)

    # Create the background, tile the bgd image
    bgdtile = load_image('background1.gif', 0)
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    # Initialize Game Groups
    aliens = pygame.sprite.Group()
    bosslefts = pygame.sprite.GroupSingle()
    bossrights = pygame.sprite.GroupSingle()
    shieldbuttons = pygame.sprite.Group()
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
    Shieldbutton.containers = shieldbuttons, all
    Shield.containers = shields, all
    Shot.containers = shots, all
    Bomb.containers = bombs, all
    Explosion.containers = all
    Points.containers = all
    Score.containers = all

    # Create Some Starting Values
    global score
    alienreload = ALIEN_RELOAD
    kills = 0
    clock = pygame.time.Clock()

    # Initialize our starting sprites
    global SCORE
    global BOMB_ODDS
    global timestarted
    timestarted = 0
    player = Player()
    Alien() #note, this 'lives' because it goes into a sprite group
    Bossleft()
    Bossright()
    Shield()
    shieldbutton = Shieldbutton()
    if pygame.font:
        all.add(Score())

    while player.alive():

        # Get input
        for event in pygame.event.get():
            if event.type == QUIT or \
                (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return
        keystate = pygame.key.get_pressed()

        # Clear/erase the last drawn sprites
        all.clear(screen, background)

        # Update all the sprites
        all.update()

        # Handle player input
        direction = keystate[K_RIGHT] - keystate[K_LEFT]
        player.move(direction)
        firing = keystate[K_SPACE]
        if not player.reloading and firing and len(shots) < MAX_SHOTS:
            Shot(player.gunpos())
        player.reloading = firing

        # Create new alien
        if alienreload:
            alienreload = alienreload - 1
        elif len(aliens) < 10: #not int(random.random() * ALIEN_ODDS):
            Alien()
            alienreload = ALIEN_RELOAD

#        if (SCORE/10).is_integer() and len(bosslefts) < 1:
#            Bossleft()
#            Bossright()
#            shield = Shield()

        # Drop bombs
        for a in aliens:
            if a and not int(random.random() * BOMB_ODDS):
                Bomb(a)

        # Collision detection for aliens and shots
        for alien in pygame.sprite.groupcollide(shots, aliens, 1, 1).keys():
            Points(alien)
            SCORE = SCORE + 1

        # Collision detection for bombs and player
        for bomb in pygame.sprite.spritecollide(player, bombs, 1):
            Explosion(player)
            Explosion(bomb)
            player.kill()

################################################################################

        # Collision detection for bombs
        pygame.sprite.groupcollide(shields, shots, 0, 1)
        pygame.sprite.groupcollide(bosslefts, bombs, 0, 1)
        pygame.sprite.groupcollide(bossrights, bombs, 0, 1)

        # Collsion for shield and shots
        if len(shieldbuttons) > 0:
            if shieldbutton.health > 0:
                for shot in pygame.sprite.groupcollide(shots, shieldbuttons, 1, 0).keys():
                    shieldbutton.health = shieldbutton.health - 1
                    Points(shot)

        # Collision for shield and shots on final hit
            else:
                for shieldbutton in pygame.sprite.groupcollide(shieldbuttons, shots, 0, 0).keys():
                    for shot in pygame.sprite.groupcollide(shots, shieldbuttons, 1, 1).keys():
                        for shield in shields:
                            shield.kill()
                        Points(shot)
#                        rightspeed =
                        Bossleft.speed = -3
                        Bossright.speed = 6

        # Collision detection for boss and shots
        if len(shieldbuttons) == 0:
            for bossleft in pygame.sprite.groupcollide(bosslefts, shots, 1, 1):
                Explosion(bossleft)
                SCORE = SCORE + 5
            for bossright in pygame.sprite.groupcollide(bossrights, shots, 1, 1):
                Explosion(bossright)
                SCORE = SCORE + 10

################################################################################

        #draw the scene
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        #cap the framerate
        clock.tick(40)

        #increase bomb droprate, reduce timestep to speed up or increase to slow down
        if BOMB_ODDS == 500 and timestarted == 0:
            timestep = 0
            timestarted = 1
        if BOMB_ODDS > 400 and timestep >= 10:
            BOMB_ODDS = BOMB_ODDS - 1
            timestep = 0
        else:
            if timestep > 10:
                timestep = 0
            timestep = timestep + 1

    pygame.time.wait(500)

    # Final screen and score displaying
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
