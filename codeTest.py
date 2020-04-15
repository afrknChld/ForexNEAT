import sys;
import json
import random
import time
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
from marketAPI import trainingMarketAPI, initMarketData, marketData
import neat
import quandl


def FundamentalsTest():
    fad = marketData.getFundamentalAnalysisData()
    print(fad)

def testRun():
    initMarketData();
    marketAPI = trainingMarketAPI();
    marketAPI.start()

    counter = 0
    while marketAPI.end() == False:
        NNinput = marketAPI.getInputData();
        for index in range(len(NNinput)):
            print(str(index) + ": " + str(NNinput[index]))
        random.seed(time.time())
        choice = random.randint(0,100)
        if choice == 1:
            marketAPI.openPosition()
        elif choice == 2:
            marketAPI.closePosition()

    results = marketAPI.getResults();
    #print("results:" + str(results));

def EMATest():
    dataset = [1,3,6,8,4,9,3,6,2,8]
    EMA = trainingMarketAPI.getExpMovingAverageAtPoint(4,dataset,5)
    print(EMA)

def ADXTest():
    secondDataArray = [1,2,3,4,5,6,7,8,9,10]
    EMAWindow = 5
    emaData = trainingMarketAPI.ExpMovingAverage(secondDataArray, EMAWindow);
    hl, atrData = trainingMarketAPI.getATR(secondDataArray, EMAWindow)
    dm = trainingMarketAPI.getDM(hl)
    diDifArray, pdiData,ndiData = trainingMarketAPI.getDI(dm,atrData, int(EMAWindow/2))
    adxData = trainingMarketAPI.getADX(diDifArray, pdiData, ndiData, int(EMAWindow/2))
    print(hl)
    print(dm)
    print(atrData)
    print(pdiData)
    print(ndiData)
    print(str(adxData))

def main():
    FundamentalsTest()


if __name__ == "__main__":
	main()
