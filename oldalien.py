#!/usr/bin/env python

"""This is a much simpler version of the aliens.py
example. It makes a good place for beginners to get
used to the way pygame works. Gameplay is pretty similar,
but there are a lot less object types to worry about,
and it makes no attempt at using the optional pygame
modules.
It does provide a good method for using the updaterects
to only update the changed parts of the screen, instead of
the entire screen surface. This has large speed benefits
and should be used whenever the fullscreen isn't being changed."""


# import
import random, os.path, sys
import pygame
from pygame.locals import *

# Throws an exception if extended image formats can't be loaded
if not pygame.image.get_extended():
    raise SystemExit("Requires the extended image loading from SDL_image")


# constants
FRAMES_PER_SEC = 40
PLAYER_SPEED   = 12
MAX_SHOTS      = 2
SHOT_SPEED     = 5
ALIEN_SPEED    = 6
ALIEN_ODDS     = 45
EXPLODE_TIME   = 6
SCREENRECT     = Rect(0, 0, 640, 480) # Sets screen size


# some globals for friendly access
dirtyrects = [] # list of update_rects
next_tick = 0   # used for timing
class Img: pass # container for images
main_dir = os.path.split(os.path.abspath(__file__))[0]  # Program's directory


# First, we define some utility functions

def load_image(file, transparent):
    "loads an image, prepares it for play"
    file = os.path.join(main_dir, 'data', file) # Gets file location path
    try:
        surface = pygame.image.load(file) # Loads image into a surface
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s' %
                         (file, pygame.get_error()))
    if transparent: # Sets areas of image which are transparent to be the same colour as the surface background
        corner = surface.get_at((0, 0))
        surface.set_colorkey(corner, RLEACCEL)
    return surface.convert()



# The logic for all the different sprite types

class Actor:
    "An enhanced sort of sprite class"
    def __init__(self, image): # Initilises an actor
        self.image = image
        self.rect = image.get_rect()

    def update(self): # Updates the current state of an actor
        "update the sprite state for this frame"
        pass

    def draw(self, screen): # Draws sprite to screen surface
        "draws the sprite into the screen"
        r = screen.blit(self.image, self.rect)
        dirtyrects.append(r)

    def erase(self, screen, background): # Erases sprite by replacing with the original background image
        "gets the sprite off of the screen"
        r = screen.blit(background, self.rect, self.rect)
        dirtyrects.append(r)


class Player(Actor):
    "Cheer for our hero"
    def __init__(self): # Initialises the actor 'player'
        Actor.__init__(self, Img.player) # Runs initialisation
        self.alive = 1
        self.reloading = 0
        self.rect.centerx = SCREENRECT.centerx
        self.rect.bottom = SCREENRECT.bottom - 10

    def move(self, direction): # Moves the player rectangle in direction
        # rect.move(x,y) conducts movement and rect.clamp(_) keeps the rect inside screenrect
        self.rect = self.rect.move(direction*PLAYER_SPEED, 0).clamp(SCREENRECT)


class Alien(Actor):
    "Destroy him or suffer"
    def __init__(self): # Initialises the actor 'Alien'
        Actor.__init__(self, Img.alien) # Runs initialisation
        self.facing = random.choice((-1,1)) * ALIEN_SPEED
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        global SCREENRECT
        self.rect[0] = self.rect[0] + self.facing # Moves alien across screen
        if not SCREENRECT.contains(self.rect): # Checks if alien is still on screen
            self.facing = -self.facing;
            #self.rect.top = self.rect.bottom + 3
            self.rect = self.rect.clamp(SCREENRECT)

#-------------------------------------------------------------------------------

class Bossleft(Actor):
    "Main left body of boss enemy"
    def __init__(self):
        Actor.__init__(self, Img.bossleft)
        self.facing = random.choice((-1,1)) * ALIEN_SPEED
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        global SCREENRECT
        self.rect[0] = self.rect[0] + self.facing # Moves boss across screen
        if not SCREENRECT.contains(self.rect): # Checks if boss is still on screen
            self.facing = -self.facing;
            #self.rect.top = self.rect.bottom + 3
            self.rect = self.rect.clamp(SCREENRECT)

#-------------------------------------------------------------------------------

class Explosion(Actor):
    "Beware the fury"
    def __init__(self, actor): # Initialises explosion actor
        Actor.__init__(self, Img.explosion)
        self.life = EXPLODE_TIME
        self.rect.center = actor.rect.center

    def update(self):
        self.life = self.life - 1 # Decreases time left for explosion animation


class Shot(Actor):
    "The big payload"
    def __init__(self, player): # Initialises shot actor
        Actor.__init__(self, Img.shot)
        self.rect.centerx = player.rect.centerx
        self.rect.top = player.rect.top - 10

    def update(self):
        self.rect.top = self.rect.top - SHOT_SPEED # Moves bullet up screen by shot speed




def main():
    "Run me for adrenaline"
    global dirtyrects

    # Initialize SDL components
    pygame.init() # Initialises all pygame modules
    screen = pygame.display.set_mode(SCREENRECT.size, 0) # Creates a display window
    clock = pygame.time.Clock() # Creates a Clock object to keep track of time

    # Load the Resources (including arguement if they are transparent)
    Img.background = load_image('background.gif', 0)
    Img.shot = load_image('shot.gif', 1)
    Img.bomb = load_image('bomb.gif', 1)
    Img.danger = load_image('danger.gif', 1)
    Img.alien = load_image('alien1.gif', 1)
    Img.player = load_image('oldplayer.gif', 1)
    Img.explosion = load_image('explosion1.gif', 1)
#-------------------------------------------------------------------------------
    Img.bossleft = load_image('bossleftsmall.png', 1)
    #Img.bossright = load_image('bossrightsmall.png', 1)
    #Img.bossshield = load_image('bossshieldsmall.png', 0)
#-------------------------------------------------------------------------------

    # Create the background
    background = pygame.Surface(SCREENRECT.size) # Creates a Surface for the background
    for x in range(0, SCREENRECT.width, Img.background.get_width()):
        background.blit(Img.background, (x, 0)) # Draws a rect for the background
    screen.blit(background, (0,0)) # Draws background rect onto main screen
    pygame.display.flip() # Updates contents of screen surface

    # Initialize Game Actors
    player = Player()
    aliens = [Alien()]
#-------------------------------------------------------------------------------
    bosslefts = [Bossleft()]
#-------------------------------------------------------------------------------
    shots = []
    explosions = []

    # Main loop
    while player.alive or explosions:
        clock.tick(FRAMES_PER_SEC) # Updates clock, computes how many milliseconds have passes since previous call

        # Gather Events
        pygame.event.pump() # Internally process pygame event handlers
        keystate = pygame.key.get_pressed() # Get state of all keyboard buttons
        if keystate[K_ESCAPE] or pygame.event.peek(QUIT): # Checks if either escape has been pressed or game has a quit event in queue
            break

        # Clear screen and update actors
        for actor in [player] + aliens + shots + explosions + bosslefts:
            actor.erase(screen, background) # Erase old sprites on screen
            actor.update() # Draw new sprites on screen

        # Clean Dead Explosions and Bullets (from lists)
        for e in explosions:
            if e.life <= 0:
                explosions.remove(e)
        for s in shots:
            if s.rect.top <= 0:
                shots.remove(s)

        # Move the player
        direction = keystate[K_RIGHT] - keystate[K_LEFT] # Checks which direction to move
        player.move(direction)

        # Create new shots
        if not player.reloading and keystate[K_SPACE] and len(shots) < MAX_SHOTS: # Checks if max shots already exist
            shots.append(Shot(player))
        player.reloading = keystate[K_SPACE] # Sets to reload if a shot has been fired

        # Create new alien
        #if not int(random.random() * ALIEN_ODDS):
        if len(aliens) < 10:
            aliens.append(Alien())

#-------------------------------------------------------------------------------
        if len(bosslefts) < 1:
            bosslefts.append(Bossleft())
#-------------------------------------------------------------------------------

        # Detect collisions
        alienrects = []
        for a in aliens:
            alienrects.append(a.rect)

#-------------------------------------------------------------------------------
        bossleftrect = []
        for b in bosslefts:
            bossleftrect.append(b.rect)
#-------------------------------------------------------------------------------

        # Checks for collision between alien shots and player
        hit = player.rect.collidelist(alienrects) # Tests if two rects overlap
        if hit != -1:
            alien = aliens[hit]
            explosions.append(Explosion(alien))
            explosions.append(Explosion(player))
            aliens.remove(alien)
            player.alive = 0
        # Checks for collisions between player shots and aliens
        for shot in shots:
            hit = shot.rect.collidelist(alienrects)
            if hit != -1:
                alien = aliens[hit]
                explosions.append(Explosion(alien))
                shots.remove(shot)
                aliens.remove(alien)
                break
#-------------------------------------------------------------------------------
        for shot in shots:
            hit = shot.rect.collidelist(bossleftrect)
            if hit != -1:
                bossleft = bosslefts[hit]
                explosions.append(Explosion(bossleft))
                shots.remove(shot)
                bosslefts.remove(bossleft)
                break
#-------------------------------------------------------------------------------

        # Draw everybody
        for actor in [player] + aliens + shots + explosions + bosslefts:
            actor.draw(screen)

        pygame.display.update(dirtyrects)
        dirtyrects = []

    pygame.time.wait(50)


#if python says run, let's run!
if __name__ == '__main__':
    main()
