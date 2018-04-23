# A game by Francis Riazi Kermani - 2018
# Space invaders-esque game to analyse
# optimality of human behaviour

# Import python modules
import random, os.path
from datetime import datetime

# Import basic pygame modules
import pygame
from pygame.locals import *

# Check if we can load more than standard BMP
if not pygame.image.get_extended():
    raise SystemExit("Sorry, extended image module required")


# Game constants
GAME_TIME      = 7.5     #time in mins
MAX_SHOTS      = 2       #most player bullets onscreen
ALIEN_ODDS     = 22      #chances a new alien appears
BOMB_ODDS      = 500     #chances a new bomb will drop
ALIEN_RELOAD   = 4       #frames between new aliens
SCREENRECT     = Rect(0, 0, 640, 480)
SCORE          = 0

# Define program directory
main_dir = os.path.split(os.path.abspath(__file__))[0]

# Define image loading functions
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

# Classes for sprites and point logic
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


class Boss_reward:
    def __init__(self,theta,sigma_r,sigma_mu,lamb):
        self.theta=theta
        self.sigma_r=sigma_r
        self.sigma_mu=sigma_mu
        self.lamb=lamb
        self.mu=random.uniform(0.0,2*self.theta)

    def get_reward(self):
        return self.clip(int(random.gauss(self.mu,self.sigma_r)))

    def clip(self,x):
        if x > 2*self.theta:
            return 2*self.theta
        if x < 0:
            return 0
        return x

    def update(self):
        self.mu=self.lamb*self.mu+(1.-self.lamb)*self.theta+random.gauss(0.,self.sigma_mu)


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


class Finalscore(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 50)
        self.font.set_italic(1)
        self.color = Color('yellow')
        msg = "Final Score: %d" % SCORE
        self.image = self.font.render(msg, 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = SCREENRECT.center


class Player(pygame.sprite.Sprite):
    speed = 10
    bounce = 24
    gun_offset = 0
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


class Points(pygame.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor, imagelist):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.images = imagelist
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.midbottom)
        self.life = self.defaultlife

    def update(self):
        self.life = self.life - 1
        self.image = self.images[self.life//self.animcycle%2]
        if self.life <= 0: self.kill()


class Record:
    def __init__(self,filename):
        self.file=open(filename,'w')

    def write(self,entry1,entry2,entry3,entry4):
        self.file.write(str(pygame.time.get_ticks())+" "+str(entry1)+" "+str(entry2)+" "+str(entry3)+" "+str(entry4)+"\n")

    def short_write(self,entry1):
        self.file.write(entry1+"\n")


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
        self.health = 1
        self.frame = 0
        self.rect.center = (320,280)

    def update(self):
        self.rect.move_ip(0, 0)
        self.frame = self.frame + 1
        self.image = self.images[self.frame//self.animcycle%3]


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


class Timer(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 30)
        self.font.set_italic(1)
        self.color = Color('yellow')
        self.currenttime = 300
        startingtime = 300
        msg = "Time left: %d" % startingtime
        self.image = self.font.render(msg, 0, self.color)
        self.rect = self.image.get_rect().move(500, 400)

    def update(self):
        if timeleft != self.currenttime:
            self.currenttime = timeleft
            msg = "Time left: %d" % timeleft
            self.image = self.font.render(msg, 0, self.color)


def main(winstyle = 0):

    # Initialize the data output
    name = input("Enter participant name: ")
    age = input("Enter age: ")
    gender = input("Enter gender (M/F/O): ")
    handedness = input("Enter handedness (L/R/A): ")
    vision = input("Confirm that you have normal or 'corrected to normal' vision (Y/N): ")
    file_name = name+"-"+datetime.now().strftime("%Y_%m_%d-%H_%M_%S")+".dat"
    record = Record(os.path.normpath(os.path.join(os.getcwd(), "log_data/",file_name)))
    record.short_write("Name: "+name)
    record.short_write("Age: "+age)
    record.short_write("Gender: "+gender)
    record.short_write("Handedness: "+handedness)
    record.short_write("Vision: "+vision+"\n"+"-----")
    log = open("log_key",'a')
    log.write(name+" "+file_name+"\n")
    log.close()

    # Initialize pygame
    pygame.display.init()
    pygame.font.init()

    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    # Load images, assign to sprite classes
    # (do this before the classes are used, after screen setup)
    img = load_image('newplayer.gif', 0)
    Player.images = [img, pygame.transform.flip(img, 1, 0)]
    img = load_image('explosion1.gif', 0)
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]
    points0 = [load_image('zeropoint1.gif',1), load_image('zeropoint2.gif',1), load_image('zeropoint3.gif',1)]
    points1 = [load_image('1point1.gif',1), load_image('1point2.gif',1), load_image('1point3.gif',1)]
    points2 = [load_image('2point1.gif',1), load_image('2point2.gif',1), load_image('2point3.gif',1)]
    points3 = [load_image('3point1.gif',1), load_image('3point2.gif',1), load_image('3point3.gif',1)]
    points4 = [load_image('4point1.gif',1), load_image('4point2.gif',1), load_image('4point3.gif',1)]
    points5 = [load_image('5point1.gif',1), load_image('5point2.gif',1), load_image('5point3.gif',1)]
    points6 = [load_image('6point1.gif',1), load_image('6point2.gif',1), load_image('6point3.gif',1)]
    points7 = [load_image('7point1.gif',1), load_image('7point2.gif',1), load_image('7point3.gif',1)]
    points8 = [load_image('8point1.gif',1), load_image('8point2.gif',1), load_image('8point3.gif',1)]
    points9 = [load_image('9point1.gif',1), load_image('9point2.gif',1), load_image('9point3.gif',1)]
    points10 = [load_image('10point1.gif',1), load_image('10point2.gif',1), load_image('10point3.gif',1)]
    points11 = [load_image('11point1.gif',1), load_image('11point2.gif',1), load_image('11point3.gif',1)]
    points12 = [load_image('12point1.gif',1), load_image('12point2.gif',1), load_image('12point3.gif',1)]
    points13 = [load_image('13point1.gif',1), load_image('13point2.gif',1), load_image('13point3.gif',1)]
    points14 = [load_image('14point1.gif',1), load_image('14point2.gif',1), load_image('14point3.gif',1)]
    points15 = [load_image('15point1.gif',1), load_image('15point2.gif',1), load_image('15point3.gif',1)]
    points16 = [load_image('16point1.gif',1), load_image('16point2.gif',1), load_image('16point3.gif',1)]
    points17 = [load_image('17point1.gif',1), load_image('17point2.gif',1), load_image('17point3.gif',1)]
    points18 = [load_image('18point1.gif',1), load_image('18point2.gif',1), load_image('18point3.gif',1)]
    points19 = [load_image('19point1.gif',1), load_image('19point2.gif',1), load_image('19point3.gif',1)]
    points20 = [load_image('20point1.gif',1), load_image('20point2.gif',1), load_image('20point3.gif',1)]
    points21 = [load_image('21point1.gif',1), load_image('21point2.gif',1), load_image('21point3.gif',1)]
    points22 = [load_image('22point1.gif',1), load_image('22point2.gif',1), load_image('22point3.gif',1)]
    points23 = [load_image('23point1.gif',1), load_image('23point2.gif',1), load_image('23point3.gif',1)]
    points24 = [load_image('24point1.gif',1), load_image('24point2.gif',1), load_image('24point3.gif',1)]
    points25 = [load_image('25point1.gif',1), load_image('25point2.gif',1), load_image('25point3.gif',1)]
    points26 = [load_image('26point1.gif',1), load_image('26point2.gif',1), load_image('26point3.gif',1)]
    points27 = [load_image('27point1.gif',1), load_image('27point2.gif',1), load_image('27point3.gif',1)]
    points28 = [load_image('28point1.gif',1), load_image('28point2.gif',1), load_image('28point3.gif',1)]
    points29 = [load_image('29point1.gif',1), load_image('29point2.gif',1), load_image('29point3.gif',1)]
    points30 = [load_image('30point1.gif',1), load_image('30point2.gif',1), load_image('30point3.gif',1)]
    points31 = [load_image('31point1.gif',1), load_image('31point2.gif',1), load_image('31point3.gif',1)]
    points32 = [load_image('32point1.gif',1), load_image('32point2.gif',1), load_image('32point3.gif',1)]
    points33 = [load_image('33point1.gif',1), load_image('33point2.gif',1), load_image('33point3.gif',1)]
    points34 = [load_image('34point1.gif',1), load_image('34point2.gif',1), load_image('34point3.gif',1)]
    points35 = [load_image('35point1.gif',1), load_image('35point2.gif',1), load_image('35point3.gif',1)]
    points36 = [load_image('36point1.gif',1), load_image('36point2.gif',1), load_image('36point3.gif',1)]
    points37 = [load_image('37point1.gif',1), load_image('37point2.gif',1), load_image('37point3.gif',1)]
    points38 = [load_image('38point1.gif',1), load_image('38point2.gif',1), load_image('38point3.gif',1)]
    points39 = [load_image('39point1.gif',1), load_image('39point2.gif',1), load_image('39point3.gif',1)]
    points40 = [load_image('40point1.gif',1), load_image('40point2.gif',1), load_image('40point3.gif',1)]
    points41 = [load_image('41point1.gif',1), load_image('41point2.gif',1), load_image('41point3.gif',1)]
    points42 = [load_image('42point1.gif',1), load_image('42point2.gif',1), load_image('42point3.gif',1)]
    points43 = [load_image('43point1.gif',1), load_image('43point2.gif',1), load_image('43point3.gif',1)]
    points44 = [load_image('44point1.gif',1), load_image('44point2.gif',1), load_image('44point3.gif',1)]
    points45 = [load_image('45point1.gif',1), load_image('45point2.gif',1), load_image('45point3.gif',1)]
    points46 = [load_image('46point1.gif',1), load_image('46point2.gif',1), load_image('46point3.gif',1)]
    points47 = [load_image('47point1.gif',1), load_image('47point2.gif',1), load_image('47point3.gif',1)]
    points48 = [load_image('48point1.gif',1), load_image('48point2.gif',1), load_image('48point3.gif',1)]
    points49 = [load_image('49point1.gif',1), load_image('49point2.gif',1), load_image('49point3.gif',1)]
    points50 = [load_image('50point1.gif',1), load_image('50point2.gif',1), load_image('50point3.gif',1)]
    pointspenalty = [load_image('-10point1.gif',1), load_image('-10point2.gif',1), load_image('-10point3.gif',1)]
    pointimages = [points0, points1, points2, points3, points4, points5, points6, points7, points8, points9, points10,
                   points11, points12, points13, points14, points15, points16, points17, points18, points19, points20,
                   points21, points22, points23, points24, points25, points26, points27, points28, points29, points30,
                   points31, points32, points33, points34, points35, points36, points37, points38, points39, points40,
                   points41, points42, points43, points44, points45, points46, points47, points48, points49, points50,
                   pointspenalty]
    Alien.images = load_images('newalien1.gif', 'newalien2.gif', 'newalien3.gif')
    Bossleft.images = [load_image('bossleftsmallv2.png', 1)]
    Bossright.images = [load_image('bossrightsmallv2.png', 1)]
    Shield.images = load_images('shield1.gif','shield2.gif','shield3.gif')
    Shieldbutton.images = load_images('shieldbutton1.gif','shieldbutton2.gif','shieldbutton3.gif')
    Bomb.images = [load_image('newbomb.gif', 0)]
    Shot.images = [load_image('newshot.gif', 0)]
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
    global SCORE
    global BOMB_ODDS
    global BOMB_THRESHOLD
    global timestarted
    global timeleft
    BOMB_THRESHOLD = BOMB_ODDS/2
    timestarted = 0
    timeleft = GAME_TIME
    alienreload = ALIEN_RELOAD
    kills = 0
    clock = pygame.time.Clock()

    # Create distribution parameters for boss_reward
    theta = 25
    sigma_r = 4.0
    sigma_mu = 2.8
    lamb = 0.9836
    mu_left = Boss_reward(theta,sigma_r,sigma_mu,lamb)
    mu_right = Boss_reward(theta,sigma_r,sigma_mu,lamb)

    # Initialize our starting sprites
    player = Player()
    Alien() #note, this 'lives' because it goes into a sprite group
#    Bossleft()
#    Bossright()
#    Shield()
#    shieldbutton = Shieldbutton()
#    record.write("boss_spawned","--",0,"")
    if pygame.font:
        all.add(Score())
        all.add(Timer())

    # Main gameplay loop
    while player.alive():

        # Get player input
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


        ## Spawn sprites
        # Spawn alien
        if alienreload:
            alienreload = alienreload - 1
        elif len(aliens) < 10:
            Alien()
            alienreload = ALIEN_RELOAD

        # Spawn new boss
        if len(bosslefts) < 1 and len(bossrights) < 1 and pygame.time.get_ticks() % 10000 < 500:
            mu_right.update()
            mu_left.update()
            Bossleft.speed = 0
            Bossright.speed = 0
            Bossleft()
            Bossright()
            Shield()
            shieldbutton = Shieldbutton()
            record.write("Current Score: "+str(SCORE)+", ", "Points Change: 0, ", "Event: Boss spawned", "")

        # Spawn bombs
        for a in aliens:
            if a and not int(random.random() * BOMB_ODDS):
                Bomb(a)


        ## Collision logic
        # Collision detection for aliens and shots
        for alien in pygame.sprite.groupcollide(shots, aliens, 1, 1).keys():
            Points(alien, pointimages[1])
            SCORE = SCORE + 1
            record.write("Current Score: "+str(SCORE)+", ", "Points Change: +1, ", "Event: Alien destroyed", "")

        # Collision detection for bombs and player
        for bomb in pygame.sprite.spritecollide(player, bombs, 1):
            Explosion(player)
            Points(bomb, pointimages[51])
            SCORE = SCORE - 10
            record.write("Current Score: "+str(SCORE)+", ", "Points Change: -10, ", "Event: Player hit", "")

        # Collision detection for bombs/shots and invulnerable sprites
        pygame.sprite.groupcollide(shields, shots, 0, 1)
        pygame.sprite.groupcollide(bosslefts, bombs, 0, 1)
        pygame.sprite.groupcollide(bossrights, bombs, 0, 1)

        # Collsion for shield and shots
        if len(shieldbuttons) > 0:
#            if shieldbutton.health > 0:
#                for shot in pygame.sprite.groupcollide(shots, shieldbuttons, 1, 0).keys():
#                    shieldbutton.health = shieldbutton.health - 1
#                    Points(shot, pointimages[0])

        # Collision for shield and shots on final hit
#            else:
                for shieldbutton in pygame.sprite.groupcollide(shieldbuttons, shots, 0, 0).keys():
                    for shot in pygame.sprite.groupcollide(shots, shieldbuttons, 1, 1).keys():
                        for shield in shields:
                            shield.kill()
                            record.write("Current Score: "+str(SCORE)+", ", "Points Change: 0, ", "Event: Boss shield destroyed", "")
                        Points(shot, pointimages[0])
                        rightspeed = 4
                        leftspeed = -4
                        Bossleft.speed = leftspeed
                        Bossright.speed = rightspeed
                        record.write("Current Score: "+str(SCORE)+", ", "Points Change: 0, ", "Event: Boss moving", "")

        # Collision detection for boss and shots
        if len(shieldbuttons) == 0:
            for bossleft in pygame.sprite.groupcollide(bosslefts, shots, 1, 1):
                for bossright in bossrights:
                    bossright.kill()
                reward = mu_left.get_reward()
                #Points(bossleft, pointimages[abs(leftspeed)])
                Points(bossleft, pointimages[reward])
                SCORE = SCORE + reward
                #record.write("bossleft_destroyed",reward,mu_left.mu,SCORE)
                record.write("Current Score: "+str(SCORE)+", ", "Points Change: +"+str(reward)+", ", "Event: Bossleft destroyed, ",
                    "Mu_left: "+str(mu_left.mu)+", Mu_right: "+str(mu_right.mu))
            for bossright in pygame.sprite.groupcollide(bossrights, shots, 1, 1):
                for bossleft in bosslefts:
                    bossleft.kill()
                reward = mu_right.get_reward()
                #Points(bossright, pointimages[rightspeed])
                Points(bossright, pointimages[reward])
                SCORE = SCORE + reward
                #record.write("bossleft_destroyed",reward,mu_right.mu,SCORE)
                record.write("Current Score: "+str(SCORE)+", ", "Points Change: +"+str(reward)+", ", "Event: Bossleft destroyed, ",
                    "Mu_left: "+str(mu_left.mu)+", Mu_right: "+str(mu_right.mu))


        # Draw the scene
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        # Cap the framerate
        clock.tick(40)

        # Increase bomb droprate, reduce timestep -> more /increase -> fewer
        if BOMB_ODDS == 500 and timestarted == 0:
            timestep = 0
            timestarted = 1
        if BOMB_ODDS > 250 and timestep >= 10:
            BOMB_ODDS = BOMB_ODDS - 1
            timestep = 0
        else:
            if timestep > 10:
                timestep = 0
            timestep = timestep + 1

        # Track time remaining
        timeleft = int(((GAME_TIME*60000) - pygame.time.get_ticks())/1000)
        if timeleft <= 0:
            player.kill()

    pygame.time.wait(500)

    # Final screen and score displaying
    screen.blit(finalscreen, (0,0))
    pygame.display.flip()
    all.empty()
    all.add(Finalscore())
    dirty = all.draw(screen)
    pygame.display.update(dirty)
    record.short_write("\n"+"-----\n"+"Final Score: "+str(SCORE))

    pygame.time.wait(3000)
    pygame.quit()


# Call the "main" function if running this script
if __name__ == '__main__': main()
