from snake import snakeGame
import time
import random

def testDriver():

    snakeGameConfig = {
          "useKeys":True,
          "gameSize":10
    }

    game = snakeGame(snakeGameConfig);

    while not game.gameOver:
        input = game.simulPlay({});
        #print(input)
        #game.move(round(3 * random.random()))

    print("Score " + str(game.score))
    game.reset()

def main():
    testDriver()

if __name__ == "__main__":
    main()
