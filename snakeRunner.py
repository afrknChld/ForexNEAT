from marketAPI import trainingMarketAPI, liveMarketAPI, initMarketData
from multiprocessing import Process, Pool, Manager
import neat
import time
import random
import pickle
import threading
import gc
import psutil
import os
import numpy as np

def getMemoryUsage():
    process = psutil.Process(os.getpid())
    mem = process.memory_full_info().uss
    return mem

def testDriver():
    snakeGameConfig = {
          "useKeys":False
    }

    game = snakeGame(snakeGameConfig);

    while not game.gameOver:
        input = game.simulPlay();
        if game.gameOver:
            break
        print(input)
        game.move(round(3 * random.random()))
        print(game.gameOver)

    print("Score " + str(game.score))

class snakeNN(object):

    def __init__(self,genome, config, id):
        self.genome = genome
        self.neural_network = neat.nn.FeedForwardNetwork.create(genome, config)
        self.id = id
        self.results = None;
        self.lastAction = 2

    def runNN(self,input):
        output = self.neural_network.activate(input)
        print(output)
        output = [ (1/(1 + np.exp(-np.round(i,decimals = 10)))) for i in output ]
        if 
        return output.index(max(output));

    def test(self):
        #runs the NN in a test environment for the purpose of evaluating
        #fitness for training
        marketAPI = trainingMarketAPI();
        marketAPI.start()

        startTime = time.time()
        while marketAPI.end() == False:
            input = marketAPI.getInputData();
            output = self.runNN(input);

            if output == 0:
                if self.lastAction != 0:
                    self.lastAction = 0;
                    marketAPI.openPosition()
            elif output == 1:
                if self.lastAction != 1:
                    self.lastAction = 1;
                    marketAPI.closePosition();
            elif output == 2:
                self.lastAction = 2


        self.results = marketAPI.getResults();
        self.results["id"] = self.id;
        return self.results;

    def run(self):
        pass
        #Similar to test but runs NN in live functional environment
    def runWithUI(self):
        pass
        #will run with a polished gui showing data such as balance and equity
        #and a graph of the market

class snakeRunner(object):

    def __init__(self, genomes = [], config = None, gen = 0, idgen = 0):

        self.idgen = idgen+1;
        random.seed(time.time())
        self.snakes = [snakeNN(genome,config,self.genID()) for genome in genomes] #initializes all the snakes in generation
        self.results = []
        self.gen = gen
        self.threads = []

    def genID(self):
        self.idgen +=1;
        return self.idgen-1;

    def addSnakesToRun(self,snakes):
        self.snakes.extend(snakes)

    def configure(self,display, displayTop):
        self.display = display
        self.displayTop = displayTop

    def run(self,save):
        initMarketData();
        pool = Pool(processes = int(len(self.snakes)/4));
        for snake in self.snakes:
            self.threads.append(pool.apply_async(snake.test))
        pool.close();
        pool.join();
        for index, snake in enumerate(self.snakes):
            self.results.append((self.threads[index].get(),snake.genome));

    def getResults(self):
        return self.results;
