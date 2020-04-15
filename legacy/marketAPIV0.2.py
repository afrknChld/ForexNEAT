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


TO DO:
-Optimize memory usage by getting rid of extraneous data saved in marketData
-Standardize all inputs to mean 0, stddev 1 or figure out different parameters
for selu
-get balance and equity calculation working and add functionality for Opening
and closing positions
-Test test test make sure every little thing works exactly as desired
-Optimize, clean, maybe change variable names
-Add support for progress checking and sending data to other factories
- FBEC [Done with this factory baybeeeeeee]

"""
import sys;
import json
import random
import time
import math
import requests
import pickle
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.contrib.factories import InstrumentsCandlesFactory

def getRandomDate():
    dayInterval = 3;
    random.seed(time.time());
    year = "20" + str(random.randrange(10,20,1));
    month = str(random.randrange(1,13,1));
    if int(month) < 10:
        month = "0" + month;
    day = str(random.randrange(1,29));
    nextDay = str(int(day)+dayInterval);
    if int(nextDay) > 28:
        month = str(int(month)+1);
        nextDay = str(dayInterval-(28 - int(nextDay)));
    if int(day) < 10:
        day = "0" + day;
    if int(nextDay) < 10:
        nextDay = "0" + nextDay;
    hour = str(random.randrange(0,24));
    if int(hour) < 10:
        hour = "0" + hour;
    minute = str(random.randrange(0,60));
    if int(minute) < 10:
        minute = "0" + minute;
    dateString = year+"-"+month+"-"+day+"T"+hour+":"+minute+":00Z";
    nextDayString = year+"-"+month+"-"+nextDay+"T"+hour+":"+minute+":00Z";
    return (dateString,nextDayString)

def initMarketData():
    print("initializing marketData");
    genData = marketData();
    trainingMarketAPI.initMarketData(genData);

def debug(vars):
    for key in vars:
        print(str(key) + ": " + str(vars[key]))
    input("Press Enter to continue...");

class marketData(object):
    granularity = {
        "5second": "S5",
        "Monthly": "M",
        "Weekly": "W",
        "Daily": "D"
    };

    def __init__(self):
        self.access_token = open("oanda_api_key.txt", "r").readline()[:-1];
        self.instrument = "EUR_USD";
        self.client = oandapyV20.API(access_token=self.access_token);
        self.date = getRandomDate();
        self.marketData = self.getAllMarketData();
        for data in self.marketData["secondData"]:
            print(data);
        secondMean = self.getSecondMean();
        secondStdDev = self.getSecondStdDev(secondMean);
        dayMean = self.getPriceMean(self.marketData["dailyData"]);
        dayStdDev = self.getPriceStdDev(self.marketData["dailyData"], dayMean);
        weekMean = self.getPriceMean(self.marketData["weeklyData"]);
        weekStdDev = self.getPriceStdDev(self.marketData["weeklyData"], weekMean);
        monthMean = self.getPriceMean(self.marketData["monthlyData"]);
        monthStdDev = self.getPriceStdDev(self.marketData["monthlyData"], monthMean);
        print("second stats: " + str(secondMean) + " " + str(secondStdDev));
        print("day stats: " + str(dayMean) + " " + str(dayStdDev));
        print("week stats: " + str(weekMean) + " " + str(weekStdDev));
        print("month stats: " + str(monthMean) + " " + str(monthStdDev));
        self.stats ={
            "second": (secondMean, secondStdDev),
            "day": (dayMean, dayStdDev),
            "week": (weekMean, weekStdDev),
            "month": (monthMean, monthStdDev)
        };

    def getPriceStdDev(self, dataset, mean):
        total = 0;
        for point in dataset:
            total += (float(point["mid"]["h"]) - mean) ** 2;
            total += (float(point["mid"]["l"]) - mean) ** 2;
        stdmean = total / (2 * len(dataset));
        print("stddev: " + str(math.sqrt(stdmean)));
        return math.sqrt(stdmean);

    def getPriceMean(self, dataset):
        total = 0;
        print("len: " + str(len(dataset)))
        for data in dataset:
            total += float(data["mid"]["h"])
            print("total: " + str(total))
            total += float(data["mid"]["l"])
            print("total: " + str(total))
        print("divisor: " + str(2*len(dataset)));
        print("Mean: " + str(total / (2*len(dataset))))
        return total/ (2*len(dataset));

    def getSecondMean(self):
        total = 0;
        for point in self.marketData["secondData"]:
            total += float(point["o"]);
        print("mean: " + str(total/len(self.marketData["secondData"])));
        return total/len(self.marketData["secondData"]);

    def getSecondStdDev(self, mean):
        total = 0;
        for point in self.marketData["secondData"]:
            total += (float(point["o"]) - mean) ** 2;
        stdmean = total / len(self.marketData["secondData"]);
        print("stddev: " + str(math.sqrt(stdmean)));
        return math.sqrt(stdmean);

    def getMarketData(self, granularity):
        access_token = self.access_token;
        client = self.client;
        instrument = self.instrument;
        startTimeString,endTimeString = self.date;
        params = {
            "from": startTimeString,
            "to": endTimeString,
            "granularity": granularity,
            "includeFirst": True,
            "count": 5000,
        }
        marketData = [];
        for r in InstrumentsCandlesFactory(instrument=instrument,params=params):
            rv = client.request(r);
            marketData.extend(rv["candles"]);
        return marketData;

    def getAllMarketData(self):
        while True:
            secondData = self.getMarketData("S5");
            monthlyData = self.getMarketData("M");
            weeklyData = self.getMarketData("W");
            dailyData = self.getMarketData("D");
            if len(secondData) > 300:
                break;
            else:
                print("running again");
                self.date = getRandomDate();

        return {
            "secondData": [{
                "o":float(data["mid"]["o"]),
                "time":data["time"]
            } for data in secondData],
            "monthlyData": monthlyData,
            "weeklyData": weeklyData,
            "dailyData": dailyData,
        };

def getStdDev(dataset, mean):
    total = 0;
    print(len(dataset))
    for point in dataset:
        total += (float(point) - mean) ** 2;
    if(total == 0):
        total = 1
    stdmean = total / (len(dataset));
    print("stddev: " + str(math.sqrt(stdmean)));
    return math.sqrt(stdmean);

def getMean(dataset):
    total = 0;
    for data in dataset:
        total += float(data)
    return total/ (len(dataset));

def normalizePriceMA(dataset, type, curIndex, n = 0, spread = 0):
    if spread == 0:
        if type == 0:
            dataPoint = dataset[curIndex]["o"];
        elif type == 1:
            dataPoint = float(dataset[curIndex]["mid"]["h"])
        elif type == 2:
            dataPoint = float(dataset[curIndex]["mid"]["l"])
        else:
            raise Exception("invalid type parameter");
    else:
        dataPoint = dataset[curIndex]["o"]-spread
    startPos = curIndex - n;
    if n == 0 or n > curIndex:
        startPos = 0
    toCalculate = [];
    for i in range(startPos, curIndex+1):
        if type == 0:
            toCalculate.append(dataset[i]["o"]-spread);
        else:
            print("running")
            toCalculate.append(dataset[i]["mid"]["h"])
            toCalculate.append(dataset[i]["mid"]["l"])
    print("\n")
    mean = getMean(toCalculate);
    stdDev = getStdDev(toCalculate, mean);
    return ((dataPoint - mean)/stdDev)

def normalizePriceConstant(dataPoint, stats):
    mean, stdDev = stats;
    return ((dataPoint-mean)/stdDev)


def differenceNormalize(toNormalize):
    return toNormalize * 10000;

class trainingMarketAPI(object):
    open = 1;
    close = 2;
    second = 0;
    high = 1;
    low = 2;
    startingBalance = 1000;
    leverage = 50;
    amtPositions = 10
    spread = 2
    posVolume = (startingBalance * leverage)/ amtPositions;
    marketData = {
        "secondData": None,
        "monthlyData": None,
        "weeklyData": None,
        "dailyData": None,
    }

    @classmethod
    def initMarketData(cls,marketDataObject):
        cls.priceStats = marketDataObject.stats;
        cls.marketData = marketDataObject.marketData;

    def __init__(self):
        self.failed = False;
        self.balance = self.equity = (self.startingBalance * self.leverage);
        self.started = False;
        self.positions = [];
        self.lastAction = 2;
        self.counters = {
            "second": 0,
            "monthly": 0,
            "weekly": 0,
            "daily": 0
        }

    def start(self):
        self.started = True;

    def end(self):
        return (self.started == False);

    def debugPrintOpenPositions(self):
        for pos in self.positions:
            curMoney = self.posVolume * float(self.marketData["secondData"][self.counters["second"]-1]["o"]);
            entryMoney = pos * self.posVolume
            print("\t" + str(curMoney - entryMoney));

    def getInputData(self):
        inputData = [];
        secondCounter = self.counters["second"];
        dayCounter = self.counters["daily"];
        weekCounter = self.counters["weekly"];
        monthCounter = self.counters["monthly"];

        if self.counters["second"] < len(self.marketData["secondData"]):
            secondOpen = float(self.marketData["secondData"][secondCounter]["o"])
            dailyLow = float(self.marketData["dailyData"][dayCounter]["mid"]["l"]);
            dailyHigh = float(self.marketData["dailyData"][dayCounter]["mid"]["h"]);
            weeklyLow = float(self.marketData["weeklyData"][weekCounter]["mid"]["l"]);
            weeklyHigh = float(self.marketData["weeklyData"][weekCounter]["mid"]["h"]);
            monthlyLow = float(self.marketData["monthlyData"][monthCounter]["mid"]["l"]);
            monthlyHigh = float(self.marketData["monthlyData"][monthCounter]["mid"]["h"]);
            inputData.append(normalizePriceMA(self.marketData["secondData"], self.second, secondCounter, 3000));
            inputData.append(normalizePriceMA(self.marketData["secondData"], self.second, secondCounter, 3000, (self.spread * .00001)));
            inputData.append(normalizePriceMA(self.marketData["dailyData"], self.low, dayCounter, 0));
            inputData.append(normalizePriceMA(self.marketData["dailyData"], self.high, dayCounter, 0));
            inputData.append(normalizePriceMA(self.marketData["weeklyData"], self.low, weekCounter, 0));
            inputData.append(normalizePriceMA(self.marketData["weeklyData"], self.high, weekCounter, 0));
            inputData.append(normalizePriceMA(self.marketData["monthlyData"], self.low, monthCounter, 0));
            inputData.append(normalizePriceMA(self.marketData["monthlyData"], self.high, monthCounter, 0));

            secondOpen = float(self.marketData["secondData"][secondCounter]["o"])
            lastOpen = float(self.marketData["secondData"][secondCounter-1]["o"]);
            if self.counters["second"] == 0:
                lastOpen = 0;
            firstDifference = secondOpen - lastOpen;
            inputData.append(differenceNormalize(firstDifference));
            lastLastOpen = float(self.marketData["secondData"][secondCounter-2]["o"]);
            if self.counters["second"] <= 1:
                lastLastOpen = 0;
            secondDifference = lastOpen - lastLastOpen;
            inputData.append(differenceNormalize(secondDifference));
            lastLastLastOpen = float(self.marketData["secondData"][secondCounter-3]["o"]);
            if self.counters["second"] <= 2:
                lastLastLastOpen = 0;
            thirdDifference = lastLastLastOpen - lastLastOpen;
            inputData.append(differenceNormalize(thirdDifference));
            inputData.append(self.getBalance());
            inputData.append(self.getEquity());
            inputData.append(len(self.positions));

            self.counters["second"]+=1;
            if self.counters["second"] < len(self.marketData["secondData"]):
                curSecondTime = self.marketData["secondData"][self.counters["second"]]["time"];
            else:
                self.started = False;
                curSecondTime = "";
            if dayCounter + 1 < len(self.marketData["dailyData"]) and self.marketData["dailyData"][dayCounter+1]["time"] == curSecondTime:
                self.counters["daily"]+=1;

            if weekCounter + 1 < len(self.marketData["weeklyData"]) and self.marketData["weeklyData"][weekCounter+1]["time"] == curSecondTime:
                self.counters["weekly"]+=1;

            if monthCounter + 1 < len(self.marketData["monthlyData"]) and self.marketData["monthlyData"][monthCounter+1]["time"] == curSecondTime:
                self.counters["monthly"]+=1;

            self.calculateEquity();


        else:
            self.started = False;

        return inputData;

    def getBalance(self):
        return self.balance

    def getEquity(self):
        return self.equity;

    def calculateEquity(self):
        curPrice = float(self.marketData["secondData"][self.counters["second"]-1]["o"]) - (self.spread * .00001);
        self.equity = self.balance;
        for p in self.positions:
            self.equity -= p * self.posVolume;
            self.equity += curPrice * self.posVolume;

        if(self.equity  < (self.balance -self.startingBalance)):
            print("Equity:" + str(self.equity) + "Balance: " + str(self.balance));
            self.failed = True;
            self.started = False;

    def openPosition(self):
        if self.lastAction != self.open:
            self.lastAction = self.open;
            self.positions.append(float(self.marketData["secondData"][self.counters["second"]-1]["o"]));
            #print("Opening a position");

    def closePosition(self):
        if self.lastAction != self.close:
            self.lastAction = self.close;
            if len(self.positions) > 0:
                entryPrice = self.positions.pop(0);
                curPrice = float(self.marketData["secondData"][self.counters["second"]-1]["o"]) - (self.spread * .00001);
                self.balance -= entryPrice * self.posVolume;
                self.balance += curPrice * self.posVolume;

    def getFitness(self):
        if self.failed:
            fitness = -self.startingBalance;
        elif self.lastAction == 0:
            fitness = -10;
        else:
            fitness = self.getBalance() - (self.startingBalance * self.leverage);
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
