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
-Get periodic market highs and lows to work
    -Just get first data point and calculate highs and lows as you go
    -Get one datapoint back as well as every other data point and then
    calculate highs and lows over the certain period
work on checkpointing and making winner.pkl into a more useful object
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
import pandas
import quandl
from dbnomics import fetch_series, fetch_series_by_api_link
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.contrib.factories import InstrumentsCandlesFactory



def getDateAhead(year,month,day,hour,minute, dayInterval):
    #gets a data day interval days ahead of the parameters entered
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
    return(year, month, day, hour, minute)

def getRandomDate(dayInterval):
    #returns a random date string formatted to rfc 3339 standard
    # as well as the date dayInterval days ahead
    random.seed(time.time());
    year = "20" + str(random.randrange(10,20,1));
    month = str(random.randrange(1,13,1));
    if int(month) < 10:
        month = "0" + month;
    day = str(random.randrange(1,29));
    if int(day) < 10:
        day = "0" + day;
    hour = "21"
    minute = "00"
    dateString = year+"-"+month+"-"+day+"T"+hour+":"+minute+":00Z";
    year, month, day, hour, minute = getDateAhead(year,month,day,hour,minute, dayInterval);
    nextDayString = year+"-"+month+"-"+day+"T"+hour+":"+minute+":00Z";
    return (dateString,nextDayString)

def initMarketData():
    #gets market data from the oandapy api and initializes the
    #trainingMarketAPI object with the date

    #fix dhkey too small error on google cloud with ssl cyphers
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL:!kRSA:!MD5:!RC4"
    try:
        requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += "HIGH:!aNULL:!kRSA:!MD5:!RC4"
    except AttributeError:
        # no pyopenssl support used / needed / available
        pass

    print("initializing marketData");
    genData = marketData(); #initializes object that gets data for a generation
    trainingMarketAPI.initMarketData(genData); #gives the market data to
    #the trainingMarketAPI object

def debug(vars,pause = True):
    for key in vars:
        print(str(key) + ": " + str(vars[key]))
    if pause:
        input("Press Enter to continue...");


class marketData(object):
    #gets market data from oanda api
    granularity = {
        "5second": "S5",
        "Monthly": "M",
        "Weekly": "W",
        "Daily": "D"
    };

    def __init__(self):
        self.dayInterval = 5 # the generation will run this many days
        self.access_token = open("oanda_api_key.txt", "r").readline()[:-1];
        self.instrument = "EUR_USD";
        self.client = oandapyV20.API(access_token=self.access_token);
        self.date = getRandomDate(self.dayInterval); #gets date for
        self.marketData = self.getAllMarketData();
        self.weekExtremes = self.calculateExtremes(self.marketData["dailyData"])
        self.fundamentalData = self.getFundamentalAnalysisData()

    def calculateExtremes(self, dataSet):
        high = float(dataSet[0]["mid"]["h"])
        low = float(dataSet[0]["mid"]["l"])
        for point in dataSet:
            curHigh = float(point["mid"]["h"])
            curLow = float(point["mid"]["l"])
            if curHigh > high:
                high = curHigh
            if curLow < low:
                low = curLow
        return (high, low)

    def getFundamentalAnalysisData(self):
        endDate, idx = self.date
        startDate = marketData.parseMonthsBack(endDate, self.dayInterval);
        quandl.ApiConfig.api_key = "kkPxNpCyfyzE6SyadrVc"
        usaExports = quandl.get("FRED/IEAXGSN",start_date = startDate[:10], end_date = endDate[:10], returns = "numpy")
        usaGDP = quandl.get("FRED/NGDPPOT", start_date = startDate[:10], end_date = endDate[:10], returns = "numpy");
        usaExports = usaExports[-1][-1]
        usaGDP = usaGDP[-1][-1]
        usaGDP = usaGDP * 1000

        fullEurData = pickle.load(open('euroFundamentalData.pkl','rb'))
        queryString = "period > '" + startDate[:10] + "' and period <= '" + endDate[:10] +"'"
        for data in fullEurData:
            data.query(queryString, inplace = True)
        ukGDP = fullEurData[0]["value"].iat[-1]
        ukExports = fullEurData[1]["value"].iat[-1]
        franceGDP = fullEurData[2]["value"].iat[-1]
        franceExports = fullEurData[3]["value"].iat[-1]
        swedenGDP = fullEurData[4]["value"].iat[-1]
        swedenExports = fullEurData[5]["value"].iat[-1]
        greeceGDP = fullEurData[6]["value"].iat[-1]
        greeceExports = fullEurData[7]["value"].iat[-1]
        luxGDP = fullEurData[8]["value"].iat[-1]
        luxExports = fullEurData[9]["value"].iat[-1]
        spainGDP = fullEurData[8]["value"].iat[-1]
        spainExports = fullEurData[9]["value"].iat[-1]
        netherlandsGDP = fullEurData[10]["value"].iat[-1]
        netherlandsExports = fullEurData[11]["value"].iat[-1]

        oldEurExports = ukExports + franceExports
        oldEurGDP = ukGDP + franceGDP
        eurExports = ukExports + franceExports + swedenExports + greeceExports + luxExports + spainExports + netherlandsExports
        eurGDP = ukGDP + franceGDP + swedenGDP + greeceGDP + luxGDP + spainGDP + netherlandsGDP

        eurData = {
            "exports": eurExports,
            "gdp": eurGDP
        }

        usaData = {
            "exports": usaExports,
            "gdp": usaGDP
        }

        return usaData, eurData


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

        if granularity == "D":
            newCandles = []
            toAdd = []
            endTimeString = startTimeString
            startTimeString = self.parseMonthsBack(startTimeString,2)
            params = {
                "from": startTimeString,
                "to": endTimeString,
                "granularity": granularity,
                "includeFirst": True,
                "count": 5000,
            }
            for r in InstrumentsCandlesFactory(instrument=instrument,params=params):
                rv = client.request(r);
                newCandles.extend(rv["candles"])
            daysToAdd = 7 - (self.dayInterval%7)
            toMinus = 2 + daysToAdd
            for i in range(daysToAdd):
                toAdd.append(newCandles[len(newCandles)-toMinus])
                toMinus -= 1

            marketData = toAdd
        return marketData;

    def getAllMarketData(self):
        while True:
            secondData = self.getMarketData("S5");
            dailyData = self.getMarketData("D");
            if len(secondData) > 300:
                break;
            else:
                print("running again");
                self.date = getRandomDate(self.dayInterval);

        return {
            "secondData": [{
                "o":float(data["mid"]["o"]),
                "time":data["time"]
            } for data in secondData],
            "dailyData": dailyData,
        };

    @staticmethod
    def parseMonthsBack(dateString, numMonths):
        date = int(dateString[5:7])
        date =  str(date - numMonths)
        if int(date) <= 0:
            date = str(12 - (2 - (int(date)+2)))
            year = int(dateString[:4])
            year -= 1
            dateString = str(year) + dateString[4:]
        if int(date) < 10:
            date = "0" + date
        newDateString = dateString[:5] + str(date) + dateString[7:]
        return newDateString


def getStdDev(dataset, mean):
    total = 0;
    for point in dataset:
        total += (float(point) - mean) ** 2;
    if(total == 0):
        total = 1
    stdmean = total / (len(dataset));
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
        "dailyData": None,
    }
    @classmethod
    def getSecondDataArray(cls, spread = 0):
        toReturn = [(float(point["o"])-spread) for point in cls.marketData["secondData"]]
        return toReturn

    @classmethod
    def initMarketData(cls,marketDataObject):
        cls.secondStart = (cls.EMAWindow * 2) - 1
        cls.marketData = marketDataObject.marketData;
        cls.weekExtremesInit = marketDataObject.weekExtremes
        cls.fundamentalData = marketDataObject.fundamentalData
        cls.supportandResistanceInit = cls.calculateSupportandResistance()
        cls.SRTouchesInit = (0,(0,0,0),(0,0,0))
        cls.SRStrengthsInit = (0,(0,0,0),(0,0,0))
        secondDataArray = cls.getSecondDataArray()
        cls.dayExtremesInit = cls.initDailyExtremes(secondDataArray, cls.secondStart)
        cls.emaData = trainingMarketAPI.ExpMovingAverage(secondDataArray, cls.EMAWindow);
        cls.macdData = trainingMarketAPI.getMACD(secondDataArray, cls.emaData,cls.EMAWindow)
        hl, cls.atrData = trainingMarketAPI.getATR(secondDataArray, cls.EMAWindow)
        dm = cls.getDM(hl)
        diDifArray, cls.pdiData,cls.ndiData = trainingMarketAPI.getDI(dm,cls.atrData, cls.EMAWindow)
        cls.adxData = trainingMarketAPI.getADX(diDifArray, cls.pdiData, cls.ndiData, cls.EMAWindow)

    @classmethod
    def initSRTouches(cls,price):
        SR = cls.supportandResistanceInit
        PP, S, R = SR
        touches = [0,0,0,0,0,0,0]
        S1, S2, S3 = S
        R1, R2, R3 = R
        all = (S1,S2,S3,R1,R2,R3,PP)
        for index, point in enumerate(all):
            if price == point:
                touches[index] += 1
        TS1,TS2,TS3,TR1,TR2,TR3,TP = trainingMarketAPI.listToTuple(touches)
        cls.SRTouchesInit = (TP, (TS1,TS2,TS3), (TR1,TR2,TR3))

    @classmethod
    def calculateSupportandResistance(cls, close = 0, high = 0, low = 0):
        if close == 0:
            day = cls.marketData["dailyData"][-1]
            high = float(day["mid"]["h"])
            low = float(day["mid"]["l"])
            close = float(day["mid"]["c"])
        else:
            high = high
            low = low
            close = close

        PP = (high + low + close) / 3
        R1 = (2*PP) - low
        S1 = (2*PP) - high
        R2 = PP + (high-low)
        S2 = PP - (high-low)
        R3 = high + (2 * (PP - low))
        S3 = low - (2 * (high - PP))

        return (PP,(S1,S2,S3),(R1,R2,R3))

    @classmethod
    def initDailyExtremes(cls,dataset,limit):
        high = dataset[0]
        low = dataset[0]
        for index in range(limit):
            cls.initSRTouches(dataset[index])
            if dataset[index] > high:
                high = dataset[index]
            if dataset[index] < low:
                low = dataset[index]

        return (high, low)

    def normalizePrice(self, price):
        curEMA = self.emaData[self.counters["second"]];
        return (price - curEMA) * 300

    def normalizeBalance(self, balance):
        toReturn =  balance - (self.startingBalance * self.leverage)
        toReturn = toReturn / (self.startingBalance * self.leverage)
        return toReturn;

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
        elif type == "di":
            toReturn = self.standardizeBounds(value,0,1000)
        elif type == "-inftoinf":
            toReturn = self.normalizeInverseLogit(value)
        elif type == "0toinf":
            toReturn = self.normalizeInverseLogitAfterLog(value)
        elif type == "exports":
            toReturn = value / 50000
        elif type == "gdp":
            toReturn = -( (value - 17000000) / 2000000)
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
        return 1/(1+np.exp(-value))

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
        counter = 0
        mcounter = 0
        for index in range(len(values)):
            if index == 0:
                pdm = 0
                ndm = 0
            else:
                upMove = 0
                downMove = 0
                high,low = values[index]
                lasthigh, lastlow = values[index-1]
                upMove = high-lasthigh
                downMove = lastlow - low
                if downMove > upMove:
                    ndm = downMove
                    pdm = 0
                elif upMove > downMove:
                    pdm = upMove
                    ndm = 0
                else:
                    pdm,ndm = last

                last = (pdm,ndm)

            if counter >= 11 or index == len(values)-1:
                counter = 0
                pdmarray.append(pdm)
                ndmarray.append(ndm)
                mcounter+=1
            else:
                counter += 1
        return (pdmarray,ndmarray)

    @staticmethod
    def getDI(dm, atr, window):
        pdm,ndm = dm
        pdmEMA = trainingMarketAPI.ExpMovingAverage(pdm,int(window/12))
        ndmEMA = trainingMarketAPI.ExpMovingAverage(ndm,int(window/12))
        pdiArray = []
        ndiArray = []
        diDifArray = []
        dmIndex = 0
        counter = 0
        for index in range(len(atr)):
            curATR = atr[index]
            if curATR == 0:
                pdi = 0
                ndi = 0
            else:
                pdi = 100 * (pdmEMA[dmIndex] / atr[index])
                ndi = 100 * (ndmEMA[dmIndex] / atr[index])
            pdiArray.append(pdi)
            ndiArray.append(ndi)

            if counter >= 11 or index == len(atr)-1:
                diDif = abs(pdi-ndi)
                diDifArray.append(diDif)
                counter = 0
                dmIndex += 1
            else:
                counter += 1

        return (diDifArray,pdiArray,ndiArray)

    @staticmethod
    def getADX(diDif,pdi,ndi,window):
        diDifEMA = trainingMarketAPI.ExpMovingAverage(diDif,int(window/12))
        adxArray = []
        difIndex = 0
        counter = 0
        for index in range(len(pdi)):
            denom = (pdi[index] + ndi[index])
            if denom == 0:
                adx = 0
            else:
                adx = 100 * (diDifEMA[difIndex] / (pdi[index] + ndi[index]))
            adxArray.append(adx)

            if counter >= 11:
                counter = 0
                difIndex += 1
            else:
                counter += 1

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
                    low = low2
                    low2 = values[index-window]

            if counter >= 11:
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
                if index+1 < len(values):
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

    @staticmethod
    def listToTuple(list):
        return(l for l in list)

    def __init__(self):
        self.failed = False;
        self.balance = self.equity = (self.startingBalance * self.leverage);
        self.started = False;
        self.positions = [];
        self.lastAction = 2;
        self.dayCounter = self.secondStart
        self.weekExtremes = self.weekExtremesInit
        self.dayExtremes = self.dayExtremesInit
        self.supportandResistance = self.supportandResistanceInit
        self.SRStrengths = self.SRStrengthsInit
        self.SRTouches = self.SRTouchesInit
        self.totalProfit = 0
        self.totalLoss = 0
        self.maxEquity = 0
        self.minEquity = 1000000
        self.maxDrawdown = 0
        self.counters = {
            "second": self.secondStart,
            "monthly": 0,
            "weekly": 0,
            "daily": 0
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

    def calculateSRTouches(self,price):
        SR = self.supportandResistance
        TP, TS, TR = self.SRTouches
        TS1, TS2, TS3 = TS
        TR1, TR2, TR3 = TR
        touches = [TP, TS1, TS2, TS3, TR1, TR2, TR3]
        PP, S, R = SR
        S1, S2, S3 = S
        R1, R2, R3 = R
        all = (PP,S1,S2,S3,R1,R2,R3)
        for index, point in enumerate(all):
            if price == point:
                touches[index] += 1
        TP,TS1,TS2,TS3,TR1,TR2,TR3 = trainingMarketAPI.listToTuple(touches)
        return (TP, (TS1,TS2,TS3), (TR1,TR2,TR3))

    def calculateSRStrenths(self, price, dayCounter):
        self.SRTouches = self.calculateSRTouches(price)
        TP, TS, TR = self.SRTouches
        TS1, TS2, TS3 = TS
        TR1, TR2, TR3 = TR
        strengths = [0,0,0,0,0,0,0]
        touches = [TP, TS1, TS2, TS3, TR1, TR2, TR3]
        for index, point in enumerate(touches):
            strength = ((17280/2) - dayCounter - point * 30) / (17280/2)
            if strength > 1:
                strength = 1
            elif strength < -1:
                strength = -1
            strengths[index] = strength
        SP, SS1, SS2, SS3, SR1, SR2, SR3 = trainingMarketAPI.listToTuple(strengths)
        self.SRStrengths = (SP, (SS1,SS2,SS3), (SR1, SR2, SR3))

    def calculateExtremes(self, price):
        weeklyHigh, weeklyLow = self.weekExtremes
        dailyHigh, dailyLow = self.dayExtremes

        if price > dailyHigh:
            dailyHigh = price
        if price < dailyLow:
            dailyLow = price

        if dailyHigh > weeklyHigh:
            weeklyHigh = dailyHigh
        if dailyLow < weeklyLow:
            weeklyLow = dailyLow

        self.calculateSRStrenths(price, self.dayCounter)
        if self.dayCounter == 17280:
            self.supportandResistance = self.calculateSupportandResistance(
                    close = price, high = dailyHigh, low = dailyLow)
            self.dayCounter = 0
            dailyHigh = price
            dailyLow = price
        self.dayCounter+=1

        self.weekExtremes = (weeklyHigh, weeklyLow)
        self.dayExtremes = (dailyHigh, dailyLow)

        return (self.dayExtremes, self.weekExtremes)

    def calculateFundamentals(self, price):
        usaData, eurData = self.fundamentalData
        usaGDP = usaData["gdp"]
        usaExports = usaData["exports"]
        eurGDP = eurData["gdp"] * price
        eurExports = eurData["exports"] * price
        gdpDif = usaGDP - eurGDP
        exportsDif = usaExports - eurExports
        return (gdpDif, exportsDif)

    def checkFundamentalData(self, time):
        if time[11:] == "00T00:00:00.000000000Z" :
            month = time[5:7]
            if month == "04" or month == "07" or month == "09" or month == "01":
                useTime = time[:11] + "05T00:00:00.000000000Z"
                self.fundamentalData = marketData.getFundamentalAnalysisData((useTime, idx))


    def getInputData(self):
        inputData = [];
        secondCounter = self.counters["second"];
        dayCounter = self.counters["daily"];
        weekCounter = self.counters["weekly"];
        monthCounter = self.counters["monthly"];

        #self.checkFundamentalData(self.marketData["secondData"][secondCounter]["time"])

        secondOpen = float(self.marketData["secondData"][secondCounter]["o"]);
        secondClose = secondOpen - (self.spread * .00001);
        dailyExtremes, weeklyExtremes = self.calculateExtremes(secondOpen)
        dailyHigh, dailyLow = dailyExtremes
        weeklyHigh,weeklyLow = weeklyExtremes

        inputData.append(self.normalize(secondOpen,"price"));
        inputData.append(self.normalize(secondClose,"price"));
        inputData.append(self.normalize(dailyLow,"price"));
        inputData.append(self.normalize(dailyHigh,"price"));
        inputData.append(self.normalize(weeklyLow,"price"));
        inputData.append(self.normalize(weeklyHigh,"price"));

        EMA = self.emaData[secondCounter];
        inputData.append(self.normalize(EMA,"0toinf"));
        ATR = self.atrData[secondCounter]
        inputData.append(self.normalize(ATR))
        PDI = self.pdiData[secondCounter]
        inputData.append(self.normalize(PDI, "di"))
        NDI = self.ndiData[secondCounter]
        inputData.append(self.normalize(NDI, "di"))
        DIDifference = PDI - NDI
        inputData.append(self.normalize(DIDifference, "di"))
        ADX = self.adxData[secondCounter]
        inputData.append(self.normalize(ADX,"adx"))
        MACD = self.macdData[secondCounter]
        inputData.append(self.normalize(MACD))

        PP, supports, resistances = self.supportandResistance
        SP, SS, SR = self.SRStrengths
        inputData.append(self.normalize(PP, "price"))
        inputData.append(self.normalize(SP, "none"))
        S1,S2,S3 = supports
        SS1, SS2, SS3 = SS
        inputData.append(self.normalize(S1, "price"))
        inputData.append(self.normalize(SS1, "none"))
        inputData.append(self.normalize(S2, "price"))
        inputData.append(self.normalize(SS2, "none"))
        inputData.append(self.normalize(S3, "price"))
        inputData.append(self.normalize(SS3, "none"))
        R1, R2, R3 = resistances
        SR1, SR2, SR3 = SR
        inputData.append(self.normalize(R1, "price"))
        inputData.append(self.normalize(SR1, "none"))
        inputData.append(self.normalize(R2, "price"))
        inputData.append(self.normalize(SR2, "none"))
        inputData.append(self.normalize(R3, "price"))
        inputData.append(self.normalize(SR3, "none"))


        gdp, exports = self.calculateFundamentals(secondOpen)
        inputData.append(self.normalize(gdp, "gdp"))
        inputData.append(self.normalize(exports, "exports"))

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
        self.calculateEquity();

        """debug({
            "price": self.marketData["secondData"][secondCounter]["o"],
            "counter": self.counters["second"],
            "balance": self.getBalance(),
            "equity": self.getEquity(),
            "Positions": self.debugGetOpenPositions(),
            "Weekly Extremes": self.weekExtremes,
            "Daily Extremes": self.dayExtremes,
            "atr": self.atrData[self.counters["second"]-1],
            "pdi": self.pdiData[self.counters["second"]-1],
            "ndi": self.ndiData[self.counters["second"]-1],
            "adx": self.adxData[self.counters["second"]-1],
            "macd": self.macdData[self.counters["second"]-1],
            "SR": self.supportandResistance,
            "SR Strengths": self.SRStrengths,
            "SR Touches": self.SRTouches
        });"""


        if not (self.counters["second"] < len(self.marketData["secondData"])):
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

        if(self.balance < 0 or (self.equity  < (self.balance -self.startingBalance))):
            print("Equity:" + str(self.equity) + "Balance: " + str(self.balance));
            self.failed = True;
            self.started = False;

        if self.equity < self.minEquity:
            self.minEquity = self.equity
        if self.equity > self.maxEquity:
            self.maxEquity = self.equity
            drawdown = ((self.maxEquity - self.minEquity) / self.maxEquity)
            if drawdown > self.maxDrawdown:
                self.maxDrawdown = drawdown
            self.minEquity = 1000000 #important to note here that min equity is
            #not minimum equity over the entire run, just the lowest point in the
            #current trough

    def openPosition(self):
        self.positions.append(float(self.marketData["secondData"][self.counters["second"]-1]["o"]));
        #print("Opening a position");

    def closePosition(self):
        if len(self.positions) > 0:
            entryPrice = self.positions.pop(0);
            curPrice = float(self.marketData["secondData"][self.counters["second"]-1]["o"]) - (self.spread * .00001);
            self.balance -= entryPrice * self.posVolume;
            self.balance += curPrice * self.posVolume;
            changeInMoney = (curPrice * self.posVolume) - (entryPrice* self.posVolume)
            if (changeInMoney > 0):
                self.totalProfit += changeInMoney
            elif(changeInMoney < 0):
                self.totalLoss += abs(changeInMoney)

    def getFitness(self):
        if self.failed:
            fitness = -self.startingBalance;
        elif self.lastAction == 0:
            fitness = -100;
        else:
            fitness = self.getBalance() - (self.startingBalance * self.leverage);
        return fitness;

    def getResults(self):
        results = {
            "fitness": self.getFitness(),
            "balance": self.getBalance(),
            "equity": self.getEquity(),
            "failed": self.failed,
            "totalProfit": self.totalProfit,
            "totalLoss": self.totalLoss,
            "max_drawdown": self.maxDrawdown
        };
        return results;



class liveMarketAPI(object):
    def __init__(self):
        pass;
