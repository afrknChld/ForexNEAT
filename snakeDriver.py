from snakeRunner import snakeRunner, snakeNN
import neat
import time
import random
import pickle
import threading
import sys

def run_snakes(fileNames):
    snakes = []
    for file in fileNames:
        print(file)
        if file == "winner.pkl":
            genome = pickle.load(open(file,'rb'))
            config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            'config')
            snake = snakeNN(genome, config, "Albert")
            print(snake.name)
            snakes.append(snake)
        else:
            snake = pickle.load(open(file,'rb'))
            snakes.append(snake)

    runner = snakeRunner()
    runner.addSnakesToRun(snakes)
    runner.run(False)

def main():
    if len(sys.argv) > 1:
        run_snakes(sys.argv[1:])
    else:
        run_snakes(["winner.pkl"])

if __name__ == "__main__":
	main()
