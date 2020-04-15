#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import pygame
import random
import time
import math

windowSize = (width, height) = (960, 720)
boardPosX = 400
boardPosY = 115
gameSize = 10
unitSize = 20
boardRect = pygame.Rect((boardPosX, boardPosY), (gameSize * unitSize,
                        gameSize * unitSize))
boardColor = pygame.Color(80, 80, 80)
playerColor = pygame.Color(255, 255, 0)
snackColor = pygame.Color(255, 0, 0)
gameOver = False
score = 0
left = 0
right = 1
up = 2
down = 3
random.seed(time.time())
bodyStartLength = 3


class cube(object):

    def __init__(
        self,
        head,
        dirx,
        diry,
        pos,
        ):
        self.head = head
        self.dirx = dirx
        self.diry = diry
        self.pos = (self.x, self.y) = pos
        self.rect = pygame.Rect(pos, (unitSize, unitSize))

    def getdirX(self):
        return self.dirx

    def getdirY(self):
        return self.diry

    def getPosBehind(self, length):
        """if length < 2:
            return (self.x - self.dirx * 2, self.y - self.diry * 2)
        else:
            return (self.x - self.dirx, self.y - self.diry)
        print("getPos behind self Pos : " + str(self.pos))
        print("get Pos behind Pos: (" + str(self.x) + "," + str(self.y) + ")")
        print("getPosBehindDirX: " +str(self.dirx) + " DirY: " + str(self.diry))
        print("getPosBehindtoReturn: (" + str(self.x - self.dirx) + "," +  str(self.y - self.diry) + ")")"""
        return (self.x - self.dirx, self.y - self.diry)

    def getPos(self):
        return self.pos

    def getDir(self):
        if self.dirx == -1 and self.diry == 0:
            return left
        elif self.dirx == 1 and self.diry == 0:
            return right
        elif self.dirx == 0 and self.diry == -1:
            return up
        elif self.dirx == 0 and self.diry == 1:
            return down

    def move(
        self,
        dirx,
        diry,
        turns,
        back,
        ):
        if self.head:
            self.dirx = dirx
            self.diry = diry
        elif self.head == False:
            for t in turns:
                if self.getPos() == t['pos']:
                    self.dirx = t['dirx']
                    self.diry = t['diry']
                    if back:
                        del turns[turns.index(t)]

        self.x += self.dirx
        self.y += self.diry
        self.pos = (self.x, self.y)

    def draw(self, screen):
        pygame.draw.rect(screen, playerColor, pygame.Rect((boardPosX
                         + self.x * unitSize, boardPosY + self.y
                         * unitSize), (unitSize, unitSize)))


class snake(object):

    body = []
    turns = []
    dir = 0
    dirx = -1
    diry = 0
    pos = (x, y) = (round((15 * gameSize/25) * random.random() + 5), round(15
                    * random.random() + 5))
    snackPos = (snackX, snackY) = (round((gameSize-2) * random.random() + 1),
                                   round((gameSize-2) * random.random() + 1))

    def __init__(self, color, unitSize,dir):
        self.color = color
        self.unitSize = unitSize
        self.setDir(dir)
        self.turnsCount = 0
        self.pos = (x, y) = (round((15 * gameSize/25) * random.random() + 2), round((15 * gameSize/25)
                    * random.random() + 2))
        self.snackX = round((gameSize-2) * random.random() + 1)
        self.snackY = round((gameSize-2) * random.random() + 1)
        self.body.append(cube(True, self.dirx, self.diry, self.pos))
        self.body.append(cube(False,self.dirx,self.diry,self.body[0].getPosBehind(0)))
        self.body.append(cube(False,self.dirx,self.diry,self.body[1].getPosBehind(0)))

    def reset(self):
        self.body.clear()
        self.turns.clear()
        self.turnsCount = 0

    def setDir(self, dir):
        if dir == left:
            self.dirx = -1
            self.diry = 0
            self.dir = left
        elif dir == right:
            self.dirx = 1
            self.diry = 0
            self.dir = right
        elif dir == up:
            self.dirx = 0
            self.diry = -1
            self.dir = up
        elif dir == down:
            self.dirx = 0
            self.diry = 1
            self.dir = down



    def move(self, dir):
        if dir == self.dir:
            return

        if dir == left:
            self.dirx = -1
            self.diry = 0
            self.dir = left
        elif dir == right:
            self.dirx = 1
            self.diry = 0
            self.dir = right
        elif dir == up:
            self.dirx = 0
            self.diry = -1
            self.dir = up
        elif dir == down:
            self.dirx = 0
            self.diry = 1
            self.dir = down

        newPos = self.body[0].getPos()

        if len(self.body) > 1 and (not self.turns or self.turns[len(self.turns) - 1]['pos'] != newPos):
            self.turnsCount+=1
            self.turns.append({'pos': self.body[0].getPos(),
                              'dirx': self.dirx, 'diry': self.diry})
    def isSnake(self,x):
        toReturn = 0;
        head = self.body[0];
        for cube in self.body[1:]:
            if x >3:
                snakeDiagonalX = cube.x - head.x
                snakeDiagonalY = cube.y - head.y
                isSnakeDiagonal = abs(snakeDiagonalX) == abs(snakeDiagonalY)
            if x == 0:
                #left
                if cube.y == head.y and cube.x < head.x:
                    #if the pos of any cube is to the direct left of the snake head
                    toReturn = 1
                    break
            elif x == 1:
                #up
                if cube.x == head.x and cube.y < head.y:
                    toReturn = 1
                    break
            elif x == 2:
                #right
                if cube.y == head.y and cube.x > head.x:
                    toReturn = 1
                    break
            elif x == 3:
                  #down
                if cube.x == head.x and cube.y > head.y:
                    toReturn = 1
                    break
            elif x == 4:
                #left-up
                if isSnakeDiagonal and not snakeDiagonalX == abs(snakeDiagonalX) and not snakeDiagonalY == abs(snakeDiagonalY):
                    toReturn = 1

            elif x == 5:
                #up-right
                if isSnakeDiagonal and snakeDiagonalX == abs(snakeDiagonalX) and not snakeDiagonalY == abs(snakeDiagonalY):
                    toReturn = 1
            elif x == 6:
                #right-down
                if isSnakeDiagonal and snakeDiagonalX == abs(snakeDiagonalX) and snakeDiagonalY == abs(snakeDiagonalY):
                    toReturn = 1
            elif x == 7:
                #down-left
                if isSnakeDiagonal and not snakeDiagonalX == abs(snakeDiagonalX) and snakeDiagonalY == abs(snakeDiagonalY):
                   toReturn = 1

        return toReturn

    def raycast(self):
        toReturn = []
        head = self.body[0];
        for x in range(8): #calculates raycasts for each direction
            appleDiagonalX = appleDiagonalY = 0
            isAppleDiagonal = False
            maxDSize = math.sqrt(2 * (gameSize * gameSize))
            if x >3:
                appleDiagonalX = self.snackX - head.x
                appleDiagonalY = self.snackY - head.y
                isAppleDiagonal = abs(appleDiagonalX) == abs(appleDiagonalY)
            if x == 0:
                #left
                leftNearestWall = head.x/gameSize
                isApple = 0
                if self.snackY == head.y and self.snackX < head.x:
                    #checks if apple is in raycast
                    isApple = 1
                leftArray = [leftNearestWall,isApple,self.isSnake(x)]
            elif x == 1:
                #up
                upNearestWall = head.y/gameSize
                isApple = 0
                if self.snackX == head.x and self.snackY < head.y:
                    isApple = 1
                rightArray = [upNearestWall,isApple,self.isSnake(x)]
            elif x == 2:
                #right
                rightNearestWall = (gameSize - head.x)/gameSize
                isApple = 0
                isSnake = 0
                if self.snackY == head.y and self.snackX > head.x:
                    isApple = 1
                upArray = [rightNearestWall,isApple,self.isSnake(x)]
            elif x == 3:
                #down
                downNearestWall = (gameSize - head.y)/gameSize
                isApple = 0
                isSnake = 0
                if self.snackX == head.x and self.snackY > head.y:
                    isApple = 1
                downArray = [downNearestWall,isApple,self.isSnake(x)]
            elif x == 4:
                #left-up
                leftUpNearestWall = math.sqrt((leftNearestWall * leftNearestWall) + (upNearestWall * upNearestWall))/maxDSize
                if upNearestWall == 0 or leftNearestWall == 0:
                    leftUpNearestWall = 0
                isApple = 0
                if isAppleDiagonal and not appleDiagonalX == abs(appleDiagonalX) and not appleDiagonalY == abs(appleDiagonalY):
                    isApple = 1;
                leftUpArray = [leftUpNearestWall,isApple,self.isSnake(x)]
            elif x == 5:
                #up-right
                upRightNearestWall = math.sqrt((upNearestWall * upNearestWall) + (rightNearestWall * rightNearestWall))/maxDSize
                if upNearestWall == 1 or rightNearestWall == 1:
                    upRightNearestWall = 0
                isApple = 0
                if isAppleDiagonal and appleDiagonalX == abs(appleDiagonalX) and not appleDiagonalY == abs(appleDiagonalY):
                    isApple = 1;
                upRightArray = [upRightNearestWall,isApple,self.isSnake(x)]
            elif x == 6:
                #right-down
                rightDownNearestWall = math.sqrt((rightNearestWall * rightNearestWall) + (downNearestWall * downNearestWall))/maxDSize
                if rightNearestWall ==0 or downNearestWall ==0:
                    rightDownNearestWall = 0
                isApple = 0
                if isAppleDiagonal and appleDiagonalX == abs(appleDiagonalX) and appleDiagonalY == abs(appleDiagonalY):
                    isApple = 1;
                rightDownArray = [rightDownNearestWall,isApple,self.isSnake(x)]

            elif x == 7:
                #down-left
                leftDownNearestWall = math.sqrt((leftNearestWall * leftNearestWall) + (downNearestWall * downNearestWall))/maxDSize
                if leftNearestWall == 0 or downNearestWall == 0:
                    leftDownNearestWall = 0
                isApple = 0
                if isAppleDiagonal and not appleDiagonalX == abs(appleDiagonalX) and appleDiagonalY == abs(appleDiagonalY):
                    isApple = 1;
                downLeftArray = [leftDownNearestWall,isApple,self.isSnake(x)]

        toReturn.extend(leftArray)
        toReturn.extend(leftUpArray)
        toReturn.extend(upArray)
        toReturn.extend(upRightArray)
        toReturn.extend(rightArray)
        toReturn.extend(rightDownArray)
        toReturn.extend(downArray)
        toReturn.extend(downLeftArray)
        #This section gets the one hot encoded tail direction and head direction
        headDir = self.body[0].getDir()
        tailDir = self.body[len(self.body)-1].getDir()
        headDirOneHot = [0,0,0,0]
        tailDirOneHot = [0,0,0,0]
        headDirOneHot[headDir] = 1
        tailDirOneHot[tailDir] = 1
        toReturn.extend(headDirOneHot)
        toReturn.extend(tailDirOneHot)
        return toReturn


    def lose(self):
        global gameOver
        gameOver = True
        global score
        score = len(self.body) - bodyStartLength

    def simulate(self):
        head = self.body[0]
        for x in self.body:
            x.move(self.dirx, self.diry, self.turns, x
                   == self.body[len(self.body) - 1])
            if x != head:
                if x.pos == head.pos:
                    self.lose()
            elif x.x < 0 or x.x > gameSize - 1:
                self.lose()
            elif x.y < 0 or x.y > gameSize - 1:
                self.lose()
            elif x.x == self.snackX and x.y == self.snackY:
                self.snackX = round((gameSize-2) * random.random() + 1)
                self.snackY = round((gameSize-2) * random.random() + 1)
                newdirX = self.body[len(self.body) - 1].getdirX()
                newdirY = self.body[len(self.body) - 1].getdirY()
                newPos = self.body[len(self.body)
                                   - 1].getPosBehind(len(self.body))
                self.body.append(cube(False, newdirX, newdirY, newPos))
                if len(self.body) == 2:
                    break

    def checkSplit(self):
        if len(self.body) > 1:
            if self.body[0].getPosBehind(0) != self.body[1].pos:
                return True;
        else:
            return False

    def draw(self, screen):
        self.screen = screen
        head = self.body[0]
        if self.checkSplit():
            print("FUCK IT SPLIT")
            print(self)
            print("Length of Turns " + str(len(self.turns)))
            print("Body[0] pos: " + str(self.body[0].pos))
            print("Body[1] pos: " + str(self.body[1].pos))
            print("Head Direction: " + str(self.dir))
            print("length of snake: " + str(len(self.body)))
            print("Body[1] dir: " + str(self.body[1].getDir()))
            correctPos = self.body[0].getPosBehind(0)
            self.body[1].x = correctPos[0]
            self.body[1].y = correctPos[1]
            print(correctPos)
            print("\n")

        for x in self.body:
            x.move(self.dirx, self.diry, self.turns, x
                   == self.body[len(self.body) - 1])
            x.draw(screen)
            if x != head:
                if x.pos == head.pos:
                    self.lose()
            elif x.x < 0 or x.x > gameSize - 1:
                self.lose()
            elif x.y < 0 or x.y > gameSize - 1:
                self.lose()
            elif x.x == self.snackX and x.y == self.snackY:
                self.snackX = round((gameSize-2) * random.random() + 1)
                self.snackY = round((gameSize-2) * random.random() + 1)
                newdirX = self.body[len(self.body) - 1].getdirX()
                newdirY = self.body[len(self.body) - 1].getdirY()
                newPos = self.body[len(self.body)
                                   - 1].getPosBehind(len(self.body))
                self.body.append(cube(False, newdirX, newdirY, newPos))
                if len(self.body) == 2:
                    break

            pygame.draw.rect(screen, snackColor, pygame.Rect((boardPosX
                             + self.snackX * unitSize, boardPosY
                             + self.snackY * unitSize), (unitSize,
                             unitSize)))



class snakeGame(object):

    def __init__(self, config = {}):
        """Initializes snakeGame object

           Args:
                config (dict): list of configuration options for customization including
                    useKeys: whether or not the program should look to the keyboard or to the move function for input
                    windowSize: size of the window if a graphical interface is present
                    gameSize: dimensions of the game, the game is played on a gameSize * gameSize grid
                    not including any options will resort to default
        """
        self.dir = 0;
        self.useKeys = True;
        self.moved = False;
        self.score = 0;
        self.gameOver = False;
        if "gameSize" in config:
            global gameSize, boardRect
            gameSize = config.get("gameSize");
            boardRect = pygame.Rect((boardPosX, boardPosY), (gameSize * unitSize,
                        gameSize * unitSize))
        if "useKeys" in config:
            self.useKeys = config.get("useKeys");
        if "windowSize" in config:
            global windowSize
            windowSize = config.get("windowSize")

        self.setup = False



    def draw(self, screen, s,info = {}):
        screen.fill(0)
        pygame.draw.rect(screen, boardColor, boardRect)
        s.draw(screen)
        self.displayInfo(screen,info)
        pygame.display.flip()

    def move(self, direction):
        self.dir = direction;
        self.moved = True;

    def dirBackwards(self,dir):
        if dir == left:
            return right
        elif dir == right:
            return left
        elif dir == up:
            return down
        elif dir == down:
            return up


    def checkMove(self,s):
        if self.useKeys:
            keys = pygame.key.get_pressed()

            for key in keys:
                if keys[pygame.K_LEFT]:
                    self.dir = left
                    self.moved = True
                elif keys[pygame.K_RIGHT]:
                    self.dir = right
                    self.moved = True
                elif keys[pygame.K_UP]:
                    self.dir = up
                    self.moved = True
                elif keys[pygame.K_DOWN]:
                    self.dir = down
                    self.moved = True



        if self.moved:
            dirCheck = (len(s.body) > 1 and self.dir == self.dirBackwards(s.dir))
            if not dirCheck:
                s.move(self.dir)
            else:
                #s.lose()
                pass

            self.moved = False

    def play(self):
        """Starts the snake game and displays to a screen; most useful for simply playing snake controlled by a
           human
        """

        self.useKeys = true;
        clock = pygame.time.Clock()
        s = snake(playerColor, unitSize)
        dir = round(3 * random.random())
        s.move(self.dir)
        screen = pygame.display.set_mode((gameSize*unitSize,gameSize*unitSize))
        pygame.display.set_caption('Snake!')
        global boardRect, boardPosX, boardPosY, score
        boardRect = pygame.Rect((0, 0), (gameSize * unitSize,
                        gameSize * unitSize))
        tempPosX = boardPosX
        tempPosY = boardPosY
        boardPosX = 0
        boardPosY = 0

        while 1:
            if not gameOver:
                #pygame.time.delay(50)
                #clock.tick(10)
                self.draw(screen, s)
                self.score = score
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        boardPosX = tempPosX
                        boardPosY = tempPosY
                        boardRect = pygame.Rect((boardPosX, boardPosY), (gameSize * unitSize,
                            gameSize * unitSize))
                        self.useKeys = false
                        return

                self.checkMove(s);

            else:
                self.gameOver = True;
                pygame.font.init()
                screen.fill(0)
                pygame.draw.rect(screen, boardColor, boardRect)
                font = pygame.font.Font(pygame.font.get_default_font(),
                        15)
                self.score = score;
                text = font.render('Score: ' + str(score), True, (255,
                                   255, 255), (100, 100, 100))
                textRect = text.get_rect()
                screen.blit(text, textRect)
                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        boardPosX = tempPosX
                        boardPosY = tempPosY
                        boardRect = pygame.Rect((boardPosX, boardPosY), (gameSize * unitSize,
                            gameSize * unitSize))
                        self.useKeys = false
                        return
    def reset(self):
        pygame.quit()
        self.gameOver = False;
        self.score = 0;
        self.moved = False;
        self.setup = False;
        self.s.reset()
        global score, gameOver
        score = 0
        gameOver = False

    def displayInfo(self,screen,info):
        pygame.font.init()
        font = pygame.font.Font(pygame.font.get_default_font(),
                        15)
        scoreText = font.render('Score: ' + str(self.score), True, (255,
                           255, 255), (0, 0, 0))

        screen.blit(scoreText,(100,250))

        if "gen" in info:
            genText = font.render("Generation: " + str(info["gen"]), True, (255,
                           255, 255), (0, 0, 0))
            screen.blit(genText,(100,200))
        if "name" in info:
            nameText = font.render("Name: " + str(info["name"]), True, (255,
                           255, 255), (0, 0, 0))
            screen.blit(nameText,(100,250))
        if "steps" in info:
            stepsText = font.render("Steps: " + str(info["steps"]), True, (255,
                           255, 255), (0, 0, 0))
            screen.blit(stepsText,(100,300))
        if "highScore" in info:
            highScoreText = font.render('High Score in Generation: ' + str(info["highScore"]), True, (255,
                           255, 255), (0, 0, 0))
            screen.blit(highScoreText,(100,350))

    def snakeSetup(self,display):
        """ Sets up the snake game so that a step can be simulated

            Args:
                display (boolean): whether or not a graphical interface is needed

        """
        if display:
            self.screen = pygame.display.set_mode(windowSize)
            pygame.display.set_caption('Snake!')
        pygame.init()
        self.clock = pygame.time.Clock()
        self.dir =  left #round(3 * random.random())
        self.s = snake(playerColor, unitSize,self.dir)
        self.setup = True

    def simulPlay(self, info):
        """Simulates a step of the snake game while drawing to a screen; useful for simulating a
           computer controlled snake game with a graphical interface
        """

        if not self.setup:
            self.snakeSetup(True)

        screen = self.screen
        s = self.s
        clock = self.clock
        global score
        if not gameOver:
            pygame.time.delay(50)
            clock.tick(175)
            self.checkMove(s);
            self.draw(screen, s,info)
            self.score = score
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

        else:
            self.gameOver = True;
            self.score = score;

        return s.raycast()

    def getTurns(self):
        return self.s.turnsCount

    def displayScoreAfterGame(self, options):
        """Displays the score after a game has been played or simulated

           Args:
                options (dict): list of options for the display including:
                    time: the time that the window will be open
                not including any options will resort to default

        """
        if not self.setup:
            self.snakeSetup(true)

        screen = self.screen

        time = 10000000000;
        if "time" in options and time > 0:
            time = options.get("time")

        startTime = pygame.time.get_ticks()

        while(pygame.time.get_ticks()-startTime < time):
            pygame.font.init()
            screen.fill(0)
            pygame.draw.rect(screen, boardColor, boardRect)
            font = pygame.font.Font(pygame.font.get_default_font(),
                    15)
            global score
            self.score = score;
            text = font.render('Score: ' + str(score), True, (255,
                               255, 255), (0, 0, 0))
            textRect = text.get_rect()
            textRect.move(500, 100)
            screen.blit(text, textRect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

    def simulate(self):
        """Simulates a step of the snake game without drawing to a screen
        """
        if not self.setup:
            self.snakeSetup(False)

        s = self.s
        clock = self.clock
        global score

        if not gameOver:
            #pygame.time.delay(50)
            #clock.tick(10)
            self.checkMove(s);
            s.simulate();
            self.score = score

        else:
            self.gameOver = True;
            self.score = score;

        return s.raycast()



#def main():
#    game = snakeGame();
#    game.main();

#if __name__ == "__main__":
#    main()
