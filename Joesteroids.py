

# Simple pygame program
# Import and initialize the pygame library
import pygame
import pickle
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    K_SPACE,
    K_RETURN,
    K_r,
    K_e,
    K_q,
    K_w,
    K_a,
    K_s,
    K_d,
    K_p,
    K_x,
    KEYDOWN,
    KEYUP,
    QUIT,
)

import traceback
import math
import random
#**********************BEGIN************************#
pygame.init()
font=pygame.font.Font('freesansbold.ttf',32)
pausefont=pygame.font.Font('freesansbold.ttf',128)
clock=pygame.time.Clock()

# Set up the drawing window
displayInfo = pygame.display.Info()
pygame.display.set_caption("OH NO! SPACE ROCKS!")
screenHeight=displayInfo.current_h-120
screenWidth=displayInfo.current_w-120
screenCentre=(screenWidth/2,screenHeight/2)
screen = pygame.display.set_mode([screenWidth, screenHeight])
screenBuffer = pygame.Surface((screenWidth, screenHeight)) #Store screen for use as BG for pause screen


# Run until the user asks to quit
running = True

#Some colours

BLACK=(0,0,0)
WHITE=(255,255,255)
RED=(255,0,0)
GREEN=(0,255,0)
BLUE=(0,0,255)
AMBER=(255,127,0)

#Asteroid Variables - maybe better placed in class instead
asteroidImg=pygame.image.load('Baren.png').convert_alpha()


#Ship Variables
shipAcc=0.05
shipMaxSpeed=4
shipRotAcc=1.5
shipInfo = pygame.image.load('ship2.png')
powerUpImages=[pygame.image.load("Terran.png").convert_alpha()]
shipWidth=40
shipHeight= shipWidth*(shipInfo.get_height()/shipInfo.get_width())
shipImgOriginal = pygame.transform.scale(pygame.image.load('ship2.png').convert_alpha(), (shipWidth, shipHeight))
shipImg = shipImgOriginal
starList=[]
laserSpeed=15.0 #15 is a good speed
laserLength = 40.0 #40 is good
laserMaxTemp = 150
startLives=3
score = 0
highScore=0
listAsteroids=[]
listLasers=[]
powerUp=None
paused=False
flipper=False

################################################ CLASSES ############################################

class Spritesheet: #Sprite Animations - this is a tricky one
    def __init__(self, filename, cols, rows):
        self.filename=filename
        sheet_load=pygame.image.load(filename).convert()
        self.sprite_sheet = pygame.transform.scale(sheet_load, (sheet_load.get_width()*2, sheet_load.get_height()*2))
        self.cols = cols  #no. of columns in spritesheet
        self.rows = rows  #no. of rows
        self.totalCellCount = cols*rows
        self.rect=self.sprite_sheet.get_rect()
        self.w=self.sprite_sheet.get_width()
        self.h=self.sprite_sheet.get_height()
        self.sprite_w=self.w/cols
        self.sprite_h=self.h/rows
        self.select=[]
        self.frame_counter=0

        for row in range(rows):
            for col in range(cols):
                x=col*self.sprite_w
                y=row*self.sprite_h
                self.select.append((x,y))

    def get_sprite(self, index):#,x,y,w,h):
        x,y=self.select[index]
        w=self.sprite_w
        h=self.sprite_h
        sprite=pygame.Surface((w,h))
        sprite.set_colorkey(BLACK)
        sprite.blit(self.sprite_sheet,(0,0), (x,y,w,h))
        return sprite
    def get_frame(self, x, y):
        """Blits a sprite, the next frame in the animation on each call.
        """
        f=math.floor(self.frame_counter/2) #halve the frame rate
        x-=self.sprite_w/2
        y-=self.sprite_h/2
        screen.blit(self.get_sprite(f), (x,y)) #x and y is top left. Needs to be central.
        self.frame_counter+=1
        if math.floor(self.frame_counter/2) >= len(self.select):
            self.frame_counter=0
            return True
      

class Sprite(pygame.sprite.Sprite):
    #Inherit this into classes for all floating/spinning/singular direction things.
    #e.g. background sprites, projectiles, asteroids, etc
    def __init__(self):
        super().__init__()
        pass
        self.startImage=pygame.image.load('Baren.png')
        self.image=self.startImage
        self.rect=self.image.get_rect()
        self.mask=pygame.mask.from_surface(self.image, threshold=127)
        self.x=0
        self.y=0
        self.drawX=0
        self.drawY=0
        self.angle=0
        self.rotationSpeed=0
        self.currentSpeed=0
        self.wrappable=False
        self.vector=None
        
    def rotate(self):
        self.angle=constrainAngle(self.angle, self.rotationSpeed)
        self.image=pygame.transform.rotate(self.startImage, self.angle)
        self.rect = self.image.get_rect(center = self.rect.center)
        self.rect.x=self.drawX
        self.rect.y=self.drawY
        self.mask=pygame.mask.from_surface(self.image, threshold=127)

    def wrap(self): #wrap around screen
        width=self.image.get_width()
        height=self.image.get_height()
        
        if self.wrappable==True:
            if (self.drawX + width) < 0: #gone left
                self.x = screenWidth+ (self.image.get_width()/2)
            if self.drawX > screenWidth: #gone right
                self.x = -(width/2)
            if (self.drawY + height) < 0: #gone up
                self.y = screenHeight+(self.image.get_height()/2)
            if self.drawY > screenHeight: #gone down
                self.y = -(height/2)
        self.drawX=self.x-(self.image.get_width()/2)
        self.drawY=self.y-(self.image.get_height()/2)

    def exitCheck(self):
        if not (0-self.width <= self.x <= screenWidth+self.width) or not (0-self.height <= self.y <= screenHeight+self.height):
            return True
        else:
            return False
        
    def getVector(self, angle, speed): # * . * . * . * T R I G O N O M E T R Y * . * . * . *
        #feed in angle and speed to give a delta x/y out.
        theta=math.radians(angle)
        dX= math.sin(theta) * speed
        dY= math.cos(theta) * speed
        result = [dX, dY]
        return result

    def randomStart(self):
        """
        Requires:  self.width, self.height, self.x, self.y
        """
        side=random.randint(0,3)
        
        if side==0:#top
            self.x=random.randint(0,screenWidth)
            self.y = 0 - (self.height/2)
        elif side==1:#right
            self.x=screenWidth+(self.width/2)
            self.y=random.randint(0,screenHeight)
        elif side==2:#bottom
            self.x=random.randint(0,screenHeight)
            self.y=screenHeight+(self.height/2)
        elif side==3:#left
            self.x=0-(self.height/2)
            self.y=random.randint(0,screenHeight)
        dx,dy = screenCentre[0]-self.x,screenCentre[1]-self.y
        rads = math.atan2(dx,dy)
        angle = math.degrees(rads) + random.randint(-15,15)
        speed=round(random.uniform(0.5,2),3)
        self.vector = self.getVector(angle, speed)
        
    
class Asteroid(Sprite):
    """An Asteroid object. Generates a random start location, size and rotational speed on init.
    """
    def __init__(self, x=-1, y=-1, width=-1):
        super().__init__()
        
        #This is default for parent (Random) asteroids. The if statement populates for child asteroids
        self.x=random.randint(0,screenWidth)
        self.y=random.randint(0,screenHeight)
        self.angle=random.randint(0,360)
        scale = random.uniform(1,5)
        self.width=round(50*scale)
        self.speed=round(random.uniform(0.2,2),3)
        self.vector = self.getVector(self.angle, self.speed)
        
        #self.randomStart()
        
        if not x==-1: #If attributes set (i.e. child asteroids)    
            self.x=x
            self.y=y
            self.width=width
            self.height=self.width*(asteroidImg.get_height()/asteroidImg.get_width())
            #self.xMove=round(random.uniform(-0.5, 0.5), 3)
            #self.yMove=round(random.uniform(-0.5, 0.5), 3)
        else: 
            self.height=self.width*(asteroidImg.get_height()/asteroidImg.get_width())
            self.randomStart()
            
        self.startImage=pygame.transform.scale(asteroidImg, (self.width, self.height))              
        self.rotationSpeed=random.uniform(-2.00,2.00)      
        self.image=pygame.transform.rotate(self.startImage, self.angle)
        self.rect=self.image.get_rect()
        self.xMove=self.vector[0]
        self.yMove=self.vector[1]
        self.drawX=self.x-(self.image.get_width()/2)
        self.drawY=self.y-(self.image.get_height()/2)
        self.wrappable=True
    
    def draw(self):       
        self.x+=self.xMove
        self.y+=self.yMove
        self.rotate()
        self.drawX=self.x-(self.image.get_width()/2)
        self.drawY=self.y-(self.image.get_height()/2)
        self.wrap()
        self.crashCheck()
        screen.blit(self.image, (self.drawX,self.drawY))
                

    def crashCheck(self): #Check if player has collided.
        cm = pygame.sprite.collide_mask(self, player1)
        if cm != None:
            player1.destroyed()
            print("death")
            listAsteroids.clear()
            #self.destroy()
            
    def destroy(self): #called when hit by laser   
        if self.width > 55: #if asteroid is big enough, generate two half sized asteroids
            listAsteroids.append(Asteroid(self.x, self.y, self.width/2))
            listAsteroids.append(Asteroid(self.x, self.y, self.width/2))
        listAsteroids.remove(self)
        if len(listAsteroids)==0:
            print("Win.") #Do level complete type stuff here
            saveScores()
            player1.reset()
    
class Laser(Sprite):#(pygame.sprite.Sprite):
    """
    LASER BEAM.
    """
    def __init__(self, x, y, angle):
        super().__init__()
        self.x=x #start location passed from ship
        self.y=y
        self.angle=angle
        self.wrappable=False
        # Get movement vector (dX, dY) at creation as this does not change.       
        self.dX, self.dY=self.getVector(self.angle, laserSpeed)
        self.endX=self.x-self.getVector(self.angle, laserLength)[0]
        self.endY=self.y-self.getVector(self.angle, laserLength)[1]
        ####SPRITE TEST
        self.image = pygame.Surface([laserLength*2, laserLength*2])#dimensions much bigger than necessary        
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.width=self.rect.width
        self.height=self.rect.height
        self.mask = pygame.mask.from_surface(self.image)
        self.vec=getVector(self.angle, laserLength)
        self.drawX=x-(self.rect.width/2)
        self.drawY=y-(self.rect.height/2)        
        pygame.draw.line(self.image, (175,0,0), ((self.width/2)-(self.vec[0]/2),(self.height/2)-(self.vec[1]/2)), ((self.width/2)+(self.vec[0]/2),(self.height/2)+(self.vec[1]/2)), 3) #Draw line on Image. We never really Blit the image.
        
        ####SPRITE TEST END
    def draw(self):

        self.x-=self.dX
        self.y-=self.dY
        self.endX-=self.dX
        self.endY-=self.dY
        ####SPRITE TEST
        self.wrap()
        self.rect.x = self.drawX
        self.rect.y = self.drawY
        screen.blit(self.image, (self.drawX,self.drawY))
        self.mask = pygame.mask.from_surface(self.image)
        ####SPRITE TEST END
        
        if self.impactCheck() or self.exitCheck():
            listLasers.remove(self)
            
    def impactCheck(self): #Check if laser hit any asteroids
        for a in list(listAsteroids): #iterate through copy of listAsteroids
            cm = pygame.sprite.collide_mask(self, a)
            if cm != None:
                a.destroy()
                player1.score+=1
                lucky()
                return True

                            


    
class Ship(Sprite):
    """
    Ship(x, y, image)
    Player controllable object. Receives keyboard inputs (hopefully)
    """
    def __init__(self, x, y):
        super().__init__()
        self.x=x
        self.y=y
        self.startImage=shipImg
        self.image=self.startImage
        self.targetSpeed=0
        self.currentSpeed=0
        self.lives=startLives
        self.laserTemp=0
        self.lasers=1
        self.overTemp=False
        self.locked=False
        self.score=0
        self.wrappable=True
        self.dead=False
        self.death_sprite = Spritesheet("ExplosionSpriteSheet.png", 4, 4)
        
        
    def draw(self):
        if self.dead:
            if not self.death_sprite.get_frame(self.x, self.y):
                return
            else:
                self.reset()
                return
                
        self.rotate()
        self.accel()
        dX, dY = getVector(self.angle,self.currentSpeed)
        self.x-=dX
        self.y-=dY
        self.wrap()        
        screen.blit(self.image, (self.drawX,self.drawY))
        self.mask=pygame.mask.from_surface(self.image, threshold=127)

    def accel(self):
        self.currentSpeed += (((self.targetSpeed-self.currentSpeed)/2)*shipAcc)
        if (abs(self.targetSpeed-self.currentSpeed)) < 0.05:
                self.currentSpeed=self.targetSpeed

    def reset(self):
        print("now reset")
        self.dead=False
        self.angle=0
        self.x,self.y = screenCentre
        self.targetSpeed=0
        self.currentSpeed=0
        self.laserTemp=0
        newScene()
        

        
    def destroyed(self):      
        self.dead=True    
        self.lives-=1
        if self.lives<0:
            self.lives=0
        
    def get_keys(self):
        keys = pygame.key.get_pressed()
        if not self.locked:
            if keys[K_w] and not keys[K_s]:
                self.targetSpeed = shipMaxSpeed
            if keys[K_s] and not keys[K_w]:
                self.targetSpeed = -shipMaxSpeed
            if not (keys[K_s] ^ keys[K_w]):
                self.targetSpeed = 0.0

            if keys[K_a] and not keys[K_d]:
                self.rotationSpeed=shipRotAcc
            if keys[K_d] and not keys[K_a]:
                self.rotationSpeed=-shipRotAcc
            if not (keys[K_a] ^ keys[K_d]):
                self.rotationSpeed = 0.0
        
    def fire(self):
        if not self.overTemp:
            if self.lasers==1:
                listLasers.append(Laser(self.x, self.y, self.angle))
            self.laserTemp+=10
            if self.laserTemp>=laserMaxTemp:
                self.laserTemp=laserMaxTemp
                self.overTemp = True

     

class PowerUp(Sprite):
    """
    Power Up spawns somewhere off screen and heads towards the centre of the screen(ish). Randomly selected, but easy to implement external selection later.
    """

    def __init__(self):
        super().__init__()
        p=random.randint(0, (len(powerUpImages)-1))
        #Randomly selects a powerup image
        self.width=35
        self.speed=1
        self.rotationSpeed=1
        self.height=self.width*(powerUpImages[p].get_height()/powerUpImages[p].get_width())
        self.randomStart()
        self.startImage=pygame.transform.scale(powerUpImages[p], (self.width, self.height))
        self.image=self.startImage
        
    def draw(self):
        self.x+=self.vector[0]
        self.y+=self.vector[1]
        self.rotate()
        self.wrap()
        screen.blit(self.image, (self.drawX,self.drawY))
        self.mask=pygame.mask.from_surface(self.image, threshold=127)
        self.picked_up()
        if self.x > (screenWidth+self.width) or self.x<-self.width or self.y > (screenHeight+self.height) or self.y<-self.height:
            powerUp=None

    def picked_up(self):
        global powerUp
        cm = pygame.sprite.collide_mask(self, player1)
        if cm != None:
            player1.lives += 1
            powerUp=None


class MainRun:
    """
    MAIN PROCESS CLASS.
    The "Game" will run as a function here. A lot of global functions should migrate here.
    Different screens and menus will be done here.
    Would like to bring "screen" variable into here but not sure if possible at this time? 
    Maybe necessary to have main menu windowed but game full screen.
    """
    def __init__(self):
        #clock=pygame.time.Clock()

        # Set up the drawing window
        #self.displayInfo = pygame.display.Info()#
        #self.screenHeight=displayInfo.current_h-120#
        #self.screenWidth=displayInfo.current_w-120#
        #self.screenCentre=(screenWidth/2,screenHeight/2) #these might be unnecessary
        #screen = pygame.display.set_mode([screenWidth, screenHeight])
        #self.screenBuffer = self.screen
        self.running=True
        self.paused=False
        self.menu_selection=0
        self.menu_selected=False
        self.flipper=True
        #self.player1=Ship(screenCentre[0], screenCentre[1])
        newStars()
        
        
    def get_events(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                #Maybe prompt are you sure?
                self.running = False
                #pygame.quit()
                
            # Did the user hit a key? *****SINGULAR PRESS****
            if event.type == pygame.KEYDOWN:
                if event.key == K_SPACE and not player1.locked:
                    player1.fire()
                if event.key == K_q: #Q = Spawn Extra Asteroid
                    listAsteroids.append(Asteroid())
                if event.key == K_r: #R = Reset Game
                    gameReset()
                if event.key == K_e:
                    pass
                if event.key == K_p: #P = Pause
                    self.paused= not self.paused
                if event.key == K_x:
                    pass
                    #self.running=False
                if event.key == K_DOWN:
                    self.menu_selection+=1
                if event.key == K_UP:
                    self.menu_selection-=1
                if event.key == K_RETURN:
                    self.menu_selected=True
            #pygame.event.clear()
            
    def mainMenu(self):
        global font
        self.running=True
        self.menu_selection=0
        labelText=["Start", "Options", "Quit"]
        labels=[]
        
        for l in labelText:
            labels.append(font.render(l, 1, AMBER))

        while self.running:
            try:
                self.get_events()
                screen.fill(BLACK)
                drawStars()
                titleText="Space Rocks!"
                title=font.render(titleText, 1, AMBER)
                screen.blit(title,(screenCentre[0]-(title.get_width()/2), screenHeight/3))
                yPos=screenHeight/2
                self.menu_selection=self.menu_selection  % len(labels)
                for l in range(len(labels)):
                    if self.menu_selection == l:
                        drawX=screenCentre[0]-(labels[l].get_width()/2)
                        drawY=yPos
                        #Draw box around this, the selected text
                        pygame.draw.rect(screen, (GREEN), pygame.Rect(drawX-4, drawY-4, labels[l].get_width()+8, labels[l].get_height()+8), 3, 3)
                        
                    screen.blit(labels[l], (screenCentre[0]-(labels[l].get_width()/2), yPos))
                    yPos+=labels[l].get_height()*1.8 #Space out the options
                if self.menu_selected==True:
                    self.running=False

                screen.blit(title,(screenCentre[0]-(title.get_width()/2), screenHeight/3))
                pygame.display.flip()
                clock.tick(60)
            except Exception as e:
                print(traceback.format_exc())
                break
            
        #Loop ended by menu selection
        self.menu_selected=False
        
        if self.menu_selection==0:
            #play game
            self.Game()
        elif self.menu_selection==1:
            #options menu
            self.optionsMenu()
        elif self.menu_selection==2:
            #quit
            #pygame.quit()
            self.running=False

            
    def Game(self):
        self.running=True
        newScene()
        while self.running:
            try:
                player1.get_keys()
                self.get_events()
                if self.paused:
                    self.pauseScreen()
                    continue
                else:
                    self.flipper=True #reset flipper value so "paused" text always draw immediately next time.
                screen.fill(BLACK)
                drawStars()
                for a in list(listAsteroids):
                    a.draw()
                for l in list(listLasers):
                    l.draw()
                if powerUp != None:
                    powerUp.draw()
                drawLaserTemp()
                drawLives()
                player1.draw()

                #draw score
                scoreText="Score: " + str(player1.score)
                label1=font.render(scoreText, 1, WHITE)
                screen.blit(label1, (10,10))

                #draw high score
                highScoreText="High Score: " + str(highScore)
                label2=font.render(highScoreText, 1, WHITE)
                label2X=screenWidth-(label2.get_width()+10)
                label2Y=10
                screen.blit(label2, (label2X,label2Y))
                screenBuffer.blit(screen, (0,0)) #snatch a copy of the rendered frame, for use in pause screen
                pygame.display.flip()
                clock.tick(60)
            except Exception as e:
                print(traceback.format_exc())
                break
            
    def pauseScreen(self):        
        """
        Interrupts game loop. Put text overlay here.
        """
        screenText="PAUSED"
        label1=pausefont.render(screenText, 1, AMBER)
        lX=screenCentre[0]-label1.get_width()/2
        lY=screenHeight/3
        screen.fill(BLACK)
        screen.blit(screenBuffer, (0,0))
        if self.flipper:
            screen.blit(label1, (lX,lY))
        self.flipper=not self.flipper        
        pygame.display.flip()
        clock.tick(2)
        
    def optionsMenu(self): #What options do we even want?
        """
        Options Menu. Potential options: starting asteroids, full screen/windowed, etc...
        """
        self.running=True
        labelText=["Option 1", "Option 2", "Main Menu"]
        labels=[]
        for l in labelText:
            labels.append(font.render(l, 1, AMBER))
        self.menu_selection=0
        while self.running:
            try:
                self.get_events()
                screen.fill(BLACK)
                drawStars()
                yPos=screenHeight/2
                self.menu_selection=self.menu_selection  % len(labels)
                #print(len(labels))
                for l in range(len(labels)):
                    if self.menu_selection == l:
                        drawX=screenCentre[0]-(labels[l].get_width()/2)
                        drawY=yPos
                        #Draw box around this, the selected text
                        
                        pygame.draw.rect(screen, (GREEN), pygame.Rect(drawX-4, drawY-4, labels[l].get_width()+8, labels[l].get_height()+8), 3, 3)
                        
                    screen.blit(labels[l], (screenCentre[0]-(labels[l].get_width()/2), yPos))
                    yPos+=labels[l].get_height()*1.8 #Space out the options

                if self.menu_selected==True:
                    self.running=False
                pygame.display.flip()
                clock.tick(60)
            except Exception as e:
                print(traceback.format_exc())
                break
        self.menu_selected=False
        if self.menu_selection==0:
            self.mainMenu()
        elif self.menu_selection==1:
            self.mainMenu()
        elif self.menu_selection==2:
            self.mainMenu()
            
    
######################################END OF CLASSES########################################

############################################# Global Functions ##############################       
                        
def getVector(angle, speed): # * . * . * . * T R I G O N O M E T R Y * . * . * . *
    #feed in angle and speed to give a delta x/y out.
    theta=math.radians(angle)
    dX= math.sin(theta) * speed
    dY= math.cos(theta) * speed
    result = [dX, dY]
    return result

def drawLives():
    global shipInfo, screenCentre
    lives=player1.lives
    distanceFromTop=10
    lifeWidth = 50   
    lifeHeight=lifeWidth*(shipInfo.get_height()/shipInfo.get_width())
    lifeImg = pygame.transform.scale(shipInfo.convert_alpha(), (lifeWidth, lifeHeight))
    if lives>=3:
        screen.blit(lifeImg, (screenCentre[0]-(lifeWidth/2),distanceFromTop))
        screen.blit(lifeImg, (screenCentre[0]-(lifeWidth*2),distanceFromTop))
        screen.blit(lifeImg, (screenCentre[0]+(lifeWidth),distanceFromTop))
        
    elif lives==2:
        screen.blit(lifeImg, (screenCentre[0]-(lifeWidth*1.25),distanceFromTop))
        screen.blit(lifeImg, (screenCentre[0]+(lifeWidth*0.25),distanceFromTop))

    elif lives==1:
        screen.blit(lifeImg, (screenCentre[0]-(lifeWidth/2),distanceFromTop))
    
    
def newStars():
    """
    Generate a random list of stars for the background
    """
    global starList
    starList=[] #clear out the stars
    maxStars=int((screenHeight*screenWidth)/5000)
    maxStarsVar=int(maxStars*0.8)
    numStars = random.randint(maxStars-maxStarsVar,maxStars)
    for s in range(numStars):
        posX=random.randint(0,screenWidth)
        posY=random.randint(0,screenHeight)
        size=random.random()*3
        star=[posX,posY,size] #save list of star attributes
        starList.append(star) #save this star to list of all stars

def drawStars():
    """
    Loops through list of stars and draws them onto the screen
    """
    for star in starList:
            pygame.draw.circle(screen, WHITE, (star[0],star[1]), star[2])

def drawLaserTemp(): #Display target speed using throttle bar
    """
    Draws the temperature gauge for the laser gun. Also drops the temperature each frame.
    """
    global laserMaxtemp, laserOverTemp
    rectLength = 300
    rectTop = (40,80)
    rectWidth = 40
    rectColour=(175,175,175)#grey
    rectLineWidth=4
    barColour=(175,0,0)
    barMaxLength = rectLength-(2*rectLineWidth)
    barIncrement = barMaxLength/laserMaxTemp
    if player1.overTemp == True:
        rectColour=(RED)

    laserTempHeight= player1.laserTemp*barIncrement
    pygame.draw.rect(screen, barColour, ((rectTop[0]+rectLineWidth, rectTop[1]+(rectLength-(laserTempHeight+(rectLineWidth-1)))), (rectWidth-(2*rectLineWidth),laserTempHeight))) 
    #Draw border on top of temp bar to hide any overlap
    pygame.draw.rect(screen, rectColour, (rectTop, (rectWidth, rectLength)), width=rectLineWidth, border_radius=4)
    #decrease laserTemp
    if player1.laserTemp>0:#Bottom out at 0
        player1.laserTemp-=laserMaxTemp*0.002
    else:
        player1.laserTemp=0
    if player1.laserTemp <= laserMaxTemp/3:
        player1.overTemp=False
        
def gameOver():
    """
    Needs work. For processing the events when lives= 0
    """
    global shipCurrentSpeed, shipTargetSpeed, screenCentre, shipLocationRefX, shipLocationRefY, shipAngle, shipRotSpeed, score, highScore
    listAsteroids.clear()
    player1.currentSpeed=0
    player1.targetSpeed=0
    player1.angle=0.0
    player1.rotationSpeed = 0.0
    if player1.score > highScore:
        highScore = player1.score
        saveScores()
    player1.score=0
    

def scorePoints(points):
    global score
    score += points
      
def newScene(source="None Given"):
    global powerUp
    #called whenever game starts or ship moves off screen
    listAsteroids.clear()
    newStars()
    createAsteroids(2)
    
def lucky():
    global powerUp
    luck=random.randint(0,20)
    #if powerUp == None:
    if luck > 18:
        print("Lucky!")
        choice=random.randint(0,len(powerUpImages))
        powerUp=PowerUp()
        
def gameReset():
    player1.currentSpeed=0
    player1.targetSpeed=0
    player1.x,player1.y = screenCentre
    player1.angle=0.0
    player1.lives=startLives
    player1.rotationSpeed = 0.0
    player1.laserTemp=0.0
    player1.overTemp=False
    listAsteroids.clear()
    listLasers.clear()
    newScene("Game Reset")
    
def constrainAngle(angle, modifier): #modify ship angle and keep within 360deg. This can be moved to a class easily.
    angle = (angle+modifier)%360
    return angle

    
def loadScores():
    global highScore
    print("Loaded High Score: " + str(highScore))
    try:
        with open('space_scores.txt', 'rb') as file:
            highScore=pickle.load(file)
    except Exception as e:
        print(traceback.format_exc())

def saveScores():
    global highScore
    print("Saving High Score: " + str(highScore))
    try:
        with open('space_scores.txt', 'wb') as file:
            pickle.dump(highScore, file)
    except Exception as e:
        print(traceback.format_exc())
        
def createAsteroids(number):
    for i in range (0,number):
        listAsteroids.append(Asteroid())

############################## END OF GLOBAL FUNCTIONS #############################################
        
loadScores()
player1=Ship(screenCentre[0], screenCentre[1])
main=MainRun()
main.mainMenu()

# Done! Time to quit.

pygame.quit()

