from marketAPI import trainingMarketAPI, liveMarketAPI
import neat
import time
import random
import pickle
import threading

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

    def runNN(self,input):
        output = self.neural_network.activate(input)
        return output.index(max(output))

    def test(self):
        #runs the NN in a test environment for the purpose of evaluating
        #fitness for training
        marketAPI = trainingMarketAPI();
        marketAPI.start()

        while marketAPI.end() == False:
            input = marketAPI.getInputData();
            output = self.runNN(input);

            if output == 0:
                marketAPI.openPosition()
            elif output == 1:
                marketAPI.closePosition();

        self.results = marketAPI.getResults();

    def run(self):
        pass
        #Similar to test but runs NN in live functional environment
    def runWithUI(self):
        pass
        #will run with a polished gui showing data such as balance and equity
        #and a graph of the market

class snakeRunner(object):

    def __init__(self, genomes = [], config = None, gen = 0):

        self.idgen = len(genomes) * gen;
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
        for snake in self.snakes:
            snake.test();
            self.results.append((snake.results, snake.genome))

    def getResults(self):
        return self.results;
