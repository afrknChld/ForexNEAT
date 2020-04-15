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
import gc
import requests
import pickle
import calendar
import math
import numpy as np
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.contrib.factories import InstrumentsCandlesFactory



def getDateAhead(year,month,day,hour,minute, dayInterval):
    prevDay = int(day)
    day = str(int(day) + dayInterval)
    idx,monthDays = calendar.monthrange(int(year),int(month))
    if int(day) > monthDays:
        day = str(dayInterval - (monthDays - prevDay))
        month = str(int(month)+1)
        if int(month) > 12:
            year = str(int(year) + 1)
            month = str(1)
        if(int(month) < 10):
            month = "0" + month

    if int(day) < 10:
        day = "0" + day
    print("monthdays: " + str(monthDays))
    return(year, month, day, hour, minute)

def getRandomDate():
    dayInterval = 4;
    random.seed(time.time());
    year = "20" + str(random.randrange(10,20,1));
    month = str(random.randrange(1,13,1));
    if int(month) < 10:
        month = "0" + month;
    day = str(random.randrange(1,29));
    if int(day) < 10:
        day = "0" + day;
    hour = str(random.randrange(0,24));
    if int(hour) < 10:
        hour = "0" + hour;
    minute = str(random.randrange(0,60));
    if int(minute) < 10:
        minute = "0" + minute;
    dateString = year+"-"+month+"-"+day+"T"+hour+":"+minute+":00Z";
    print("Day string: " + dateString)
    year, month, day, hour, minute = getDateAhead(year,month,day,hour,minute, dayInterval);
    nextDayString = year+"-"+month+"-"+day+"T"+hour+":"+minute+":00Z";
    print("Next day string: " + nextDayString)
    return (dateString,nextDayString)

def initMarketData():
    print("initializing marketData");
    genData = marketData();
    trainingMarketAPI.initMarketData(genData);

def debug(vars,pause = True):
    for key in vars:
        print(str(key) + ": " + str(vars[key]))
    if pause:
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

def standardize(dataPoint, stats):
    mean, stdDev = stats;
    return ((dataPoint-mean)/stdDev)

class trainingMarketAPI(object):
    open = 1;
    close = 2;
    second = 0;
    high = 1;
    low = 2;
    EMAWindow = 3000;
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
    def getSecondDataArray(cls, spread = 0):
        toReturn = [(float(point["o"])-spread) for point in cls.marketData["secondData"]]
        return toReturn

    @classmethod
    def initMarketData(cls,marketDataObject):
        cls.marketData = marketDataObject.marketData;
        print("dataset_length: " + str(len(marketDataObject.marketData["secondData"])))
        secondDataArray = cls.getSecondDataArray()
        cls.emaData = trainingMarketAPI.ExpMovingAverage(secondDataArray, cls.EMAWindow);
        cls.macdData = trainingMarketAPI.getMACD(secondDataArray, cls.emaData,cls.EMAWindow)
        hl, cls.atrData = trainingMarketAPI.getATR(secondDataArray, cls.EMAWindow)
        dm = cls.getDM(hl)
        diDifArray, cls.pdiData,cls.ndiData = trainingMarketAPI.getDI(dm,cls.atrData, cls.EMAWindow)
        cls.adxData = trainingMarketAPI.getADX(diDifArray, cls.pdiData, cls.ndiData, cls.EMAWindow)

        for point in cls.marketData["dailyData"]:
            print(point)
        print()
        for point in cls.marketData["monthlyData"]:
            print(point)
        print()
        for point in cls.marketData["weeklyData"]:
            print(point)
        print()

    """     weeklyHigh = float(self.marketData["weeklyData"][0]["mid"]["h"])
            weeklyLow = float(self.marketData["weeklyData"][0]["mid"]["l"])
            weeklyAverage = (weeklyHigh+weeklyLow)/2"""
    def normalizePrice(self, price):
        curEMA = self.emaData[self.counters["second"]];
        return (price - curEMA) * 300

    def normalizeBalance(self, balance):
        return balance - (self.startingBalance * self.leverage)

    def normalize(self, value, type = ""):
        toReturn = 0
        if type == "price":
            toReturn = self.normalizePrice(value)
        elif type == "balance":
            toReturn = self.normalizeBalance(value)
        elif type == "difference":
            toReturn = self.normalizeDifference(value)
        elif type == "adx":
            toReturn = self.standardizeBounds(value,0,100)
        elif type == "-inftoinf":
            toReturn = self.normalizeInverseLogit(value)
        elif type == "0toinf":
            toReturn = self.normalizeInverseLogitAfterLog(value)
        elif type == "none":
            toReturn = value
        else:
            toReturn = self.normalizeInverseLogit(value)

        return toReturn

    @staticmethod
    def normalizeInverseLogitAfterLog(value):
        return value / (1+value)

    @staticmethod
    def normalizeInverseLogit(value):
        return 1/(1+math.exp(-value))

    @staticmethod
    def standardizeBounds(val,min,max):
        return (val - min) / (max - min);


    @staticmethod
    def normalizeDifference(toNormalize):
        return toNormalize * 10000;

    @staticmethod
    def movingAverage(values,window):
        weights = np.repeat(1.0, window)/window
        smas = np.convolve(values, weights,'valid')
        return smas

    @staticmethod
    def ExpMovingAverage(values, window):
        weights = np.exp(np.linspace(-1.,0.,window))
        weights /= weights.sum()

        a = np.convolve(values, weights)[:len(values)]
        a[:window] = a[window]
        return a

    @staticmethod
    def ExpMovingAverageSingle(values, window):
        weights = np.exp(np.linspace(-1.,0.,window))
        weights /= weights.sum()

        a = np.convolve(values, weights,'valid')[:len(values)]
        return a

    @staticmethod
    def getExpMovingAverageAtPoint(index,data,window):
        startIndex = index-(window-1)
        if startIndex < 0:
            raise Exception("not enough data to calculate EMA")
        dataset = data[startIndex:index+1]
        a = trainingMarketAPI.ExpMovingAverageSingle(dataset, window)
        return a[len(a)-1]


    @staticmethod
    def getMACD(values, shortEMA, window):
        longwindow = window * 2
        longEMA = trainingMarketAPI.ExpMovingAverage(values,longwindow)
        toReturn = []
        for index in range(len(values)):
            macd = shortEMA[index] - longEMA[index]
            toReturn.append(macd)
        return toReturn

    @staticmethod
    def getDM(values):
        pdmarray = []
        ndmarray = []
        last = (0,0)
        for index in range(len(values)):
            if index == 0:
                pdm = 0
                ndm = 0
            else:
                upMove = 0
                downMove = 0
                counter = index
                high,low = values[counter]
                lasthigh, lastlow = values[counter-1]
                upMove = high-lasthigh
                downMove = lastlow-low
                if upMove > downMove:
                    pdm = upMove
                    ndm = 0
                elif downMove > upMove:
                    ndm = downMove
                    pdm = 0
                else:
                    pdm,ndm = last

                last = (pdm,ndm)
            pdmarray.append(pdm)
            ndmarray.append(ndm)
        return (pdmarray,ndmarray)

    def getDI(dm, atr, window):
        pdm,ndm = dm
        pdmEMA = trainingMarketAPI.ExpMovingAverage(pdm,window)
        ndmEMA = trainingMarketAPI.ExpMovingAverage(ndm,window)
        pdiArray = []
        ndiArray = []
        diDifArray = []
        for index in range(len(atr)):
            curATR = atr[index]
            if curATR == 0:
                pdi = 0
                ndi = 0
            else:
                pdi = 100 * (pdmEMA[index] / atr[index])
                ndi = 100 * (ndmEMA[index] / atr[index])
            diDif = abs(pdi-ndi)
            pdiArray.append(pdi)
            ndiArray.append(ndi)
            diDifArray.append(diDif)

        return (diDifArray,pdiArray,ndiArray)

    @staticmethod
    def getADX(diDif,pdi,ndi,window):
        diDifEMA = trainingMarketAPI.ExpMovingAverage(diDif,window)
        adxArray = []
        for index in range(len(pdi)):
            denom = (pdi[index] + ndi[index])
            if denom == 0:
                adx = 0
            else:
                adx = 100 * (diDifEMA[index] / (pdi[index] + ndi[index]))
            adxArray.append(adx)

        return adxArray




    @staticmethod
    def getATR(values, window):
        TR = []
        toReturn = []
        highandlow = []
        high = values[0]
        low = values[0]
        high2 = values[0]
        low2 = values[0]
        TRtotal = 0
        counter = 0
        toAddATR = 0
        toAddHL = (0,0)
        curTR = 0
        for index in range(len(values)):
            if values[index] > high:
                high = values[index]
                high2=high
            elif values[index] > high2:
                high2 = values[index]
            if values[index] < low:
                low = values[index]
                low2 = low
            elif values[index] < low2:
                low2 = values[index]

            if index+1 > window:

                if values[index] == high:
                    high = high2
                    high2 = values[index-window]
                elif values[index] == low:
                    high = low2
                    low2 = values[index-window]

            if counter >= 12:
                r = high-low
                lastClose = values[index]
                highClose = abs(high - lastClose)
                lowClose = abs(low-lastClose)
                curTR = max(r,highClose,lowClose)
                TRtotal += curTR
                ATR = TRtotal / window
                toAddATR = ATR
                toAddHL = (high,low)

                if index+1 > window:
                    TRtotal -= TR[index-window-1]

                counter = 0
                if index < len(values):
                    high = values[index+1]
                    low = values[index+1]
                    high2 = values[index+1]
                    low2 = values[index+1]
            else:
                counter += 1

            TR.append(curTR)
            toReturn.append(toAddATR)
            highandlow.append(toAddHL)
        return (highandlow,toReturn)




    def __init__(self):
        self.failed = False;
        self.balance = self.equity = (self.startingBalance * self.leverage);
        self.started = False;
        self.positions = [];
        self.lastAction = 2;
        self.counters = {
            "second": (self.EMAWindow*2)-1,
            "monthly": 0,
            "weekly": 0,
            "daily": 0
        }
        self.high = {
            "second": self.marketData["secondData"][self.counters["second"]]["o"],
            "month": self.marketData["monthlyData"][self.counters["monthly"]]["mid"]["h"],
            "weekly": self.marketData["weeklyData"][self.counters["weekly"]]["mid"]["h"],
            "daily": self.marketData["dailyData"][self.counters["daily"]]["mid"]["h"]
        }

    def start(self):
        self.started = True;

    def end(self):
        return (self.started == False);

    def debugGetOpenPositions(self):
        toReturn = []
        for pos in self.positions:
            curMoney = self.posVolume * (float(self.marketData["secondData"][self.counters["second"]-1]["o"]) - (self.spread * .00001));
            entryMoney = pos * self.posVolume
            toReturn.append(curMoney - entryMoney)

        return toReturn


    def debugPrintOpenPositions(self):
        debugPosData = self.debugGetOpenPositions
        for pos in debugPosData:
            print("\t" + str(pos))


    def getInputData(self):
        inputData = [];
        secondCounter = self.counters["second"];
        dayCounter = self.counters["daily"];
        weekCounter = self.counters["weekly"];
        monthCounter = self.counters["monthly"];

        if self.counters["second"] < len(self.marketData["secondData"]):
            secondOpen = float(self.marketData["secondData"][secondCounter]["o"]);
            secondClose = secondOpen - (self.spread * .00001);
            dailyLow = float(self.marketData["dailyData"][dayCounter]["mid"]["l"]);
            dailyHigh = float(self.marketData["dailyData"][dayCounter]["mid"]["h"]);
            weeklyLow = float(self.marketData["weeklyData"][weekCounter]["mid"]["l"]);
            weeklyHigh = float(self.marketData["weeklyData"][weekCounter]["mid"]["h"]);
            monthlyLow = float(self.marketData["monthlyData"][monthCounter]["mid"]["l"]);
            monthlyHigh = float(self.marketData["monthlyData"][monthCounter]["mid"]["h"]);
            inputData.append(self.normalize(secondOpen,"price"));
            inputData.append(self.normalize(secondClose,"price"));
            inputData.append(self.normalize(dailyLow,"price"));
            inputData.append(self.normalize(dailyHigh,"price"));
            inputData.append(self.normalize(weeklyLow,"price"));
            inputData.append(self.normalize(weeklyHigh,"price"));
            inputData.append(self.normalize(monthlyLow,"price"));
            inputData.append(self.normalize(monthlyHigh,"price"));

            EMA = self.emaData[secondCounter];
            inputData.append(self.normalize(EMA,"0toinf"));
            ATR = self.atrData[secondCounter]
            inputData.append(self.normalize(ATR))
            PDI = self.pdiData[secondCounter]
            inputData.append(self.normalize(PDI))
            NDI = self.ndiData[secondCounter]
            inputData.append(self.normalize(NDI))
            DIDifference = PDI - NDI
            inputData.append(self.normalize(DIDifference))
            ADX = self.adxData[secondCounter]
            inputData.append(self.normalize(ADX,"adx"))
            MACD = self.macdData[secondCounter]
            inputData.append(self.normalize(MACD))


            lastOpen = float(self.marketData["secondData"][secondCounter-1]["o"]);
            if self.counters["second"] == 0:
                lastOpen = 0;
            firstDifference = secondOpen - lastOpen;
            inputData.append(self.normalize(firstDifference,"difference"));
            lastLastOpen = float(self.marketData["secondData"][secondCounter-2]["o"]);
            if self.counters["second"] <= 1:
                lastLastOpen = 0;
            secondDifference = lastOpen - lastLastOpen;
            inputData.append(self.normalize(secondDifference,"difference"));
            lastLastLastOpen = float(self.marketData["secondData"][secondCounter-3]["o"]);
            if self.counters["second"] <= 2:
                lastLastLastOpen = 0;
            thirdDifference = lastLastLastOpen - lastLastOpen;
            inputData.append(self.normalize(thirdDifference,"difference"));
            inputData.append(self.normalize(self.getBalance(),"balance"));
            inputData.append(self.normalize(self.getEquity(),"balance"));
            inputData.append(len(self.positions));

            self.counters["second"]+=1;
            if self.counters["second"] < len(self.marketData["secondData"]):
                curSecondTime = self.marketData["secondData"][self.counters["second"]]["time"];
            else:
                self.started = False;
                curSecondTime = "";
            if dayCounter + 1 < len(self.marketData["dailyData"]):
                for data in self.marketData["dailyData"]:
                    if data["time"] == curSecondTime:
                        self.counters["daily"]+=1;

            if weekCounter + 1 < len(self.marketData["weeklyData"]):
                for data in self.marketData["weeklyData"]:
                    if data["time"] == curSecondTime:
                        self.counters["weekly"]+=1;

            if monthCounter + 1 < len(self.marketData["monthlyData"]):
                for data in self.marketData["monthlyData"]:
                    if data["time"] == curSecondTime:
                        self.counters["monthly"]+=1;

            self.calculateEquity();

            """debug({
                "price": self.marketData["secondData"][secondCounter]["o"],
                "counter": self.counters["second"],
                "balance": self.getBalance(),
                "equity": self.getEquity(),
                "Positions": self.debugGetOpenPositions(),
                "atr": self.atrData[self.counters["second"]-1],
                "pdi": self.pdiData[self.counters["second"]-1],
                "ndi": self.ndiData[self.counters["second"]-1],
                "adx": self.adxData[self.counters["second"]-1],
                "macd": self.macdData[self.counters["second"]-1]
            });"""


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
        self.positions.append(float(self.marketData["secondData"][self.counters["second"]-1]["o"]));
        #print("Opening a position");

    def closePosition(self):
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
