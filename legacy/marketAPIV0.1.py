"""
plan:

-test marketAPI which pretends to execute real market orders
    and calculates balance, equity, etc based off backtest or current price data
    assuming that OANDA api will not allow creating encapsulated backtesting
    environments
    OR
    use spotware or other api if possible to create encapsulated
    backtesting environment and execute market orders and get balance and
    equity from that environment

    each individual in the population will get a static amount of time to make
    money in the forex market. The market's behavior will be random; either
    using the current market behavior or using a randomly selected interval of
    time from the past backtesting data

-live marketAPI which will execute real market orders using the
    authentication information given and whichever api is optimal

-may make two objects for each of the above scenarios and store as a field of
the marketAPI class and use the principles of polymorphism

fields needed
end
    boolean, whether or not the current test simulation has ended
methods needed

__init__()
start()
    start the test run for the allotted time
end()
    boolean, returns whether the test simulation is over yet
getInputData()
    get input data and format it for the NN. If it is in danger of exceeding
    the api limits, it will return the input data from the last request
openPosition()
closePosition()
getFitness()
    fitness = ending balance - starting balance after all positions are closed
get balance, equity, etc


"""
import random;
import time;

class trainingMarketAPI(object):
    def __init__(self):
        self.failed = False;
        self.startingBalance = 1000;
        self.started = False;
        self.counter = 0;

    def start(self):
        self.started = True;

    def end(self):
        return (self.started == False);

    def getInputData(self):
        self.counter+=1;
        if self.counter >= 1000:
            self.started = False;
        return [0,0,0,0,0,0,0,0,0,0,0,0,0];

    def getBalance(self):
        return self.startingBalance;

    def getEquity(self):
        return self.startingBalance;

    def openPosition(self):
        #print("Market API is opening A position");
        pass

    def closePosition(self):
        #print("marketAPI is closing A position");
        pass

    def getFitness(self):
        """if self.failed:
            fitness = -self.startingBalance;
        else:
            fitness = self.getBalance() - self.startingBalance;"""
        random.seed(time.time())
        fitness = random.choice(range(0,1000));
        return fitness;

    def getResults(self):
        results = {
            "fitness": self.getFitness(),
            "balance": self.getBalance(),
            "equity": self.getEquity(),
            "failed": self.failed
        };
        return results;

class liveMarketAPI(object):
    def __init__(self):
        pass;
