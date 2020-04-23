import sys;
import json
import random
import time
import pickle
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
from marketAPI import trainingMarketAPI, initMarketData, marketData
from dbnomics import fetch_series, fetch_series_by_api_link
from snake_train import sendUpdateToServer, sendToTestingFacility
import neat
import quandl
import pandas

def updateTest():
    sendUpdateToServer({
        "data1": 5,
        "data2": 19,
        "data3": 100000,
        "data4": "bruh"
    })

def sendToTestingFacilityTest():
    random.seed(time.time())
    choice = random.randint(0,100)
    filename = "toTestingFacility" + str(choice) + ".pkl"
    info = pickle.load(open("toTestingFacility.pkl","rb"))
    sendToTestingFacility(info,filename)

def getEuroFundamentals():
    print()
    ukGDP = fetch_series('Eurostat/namq_10_gdp/Q.CLV05_MEUR.NSA.B1GQ.UK')
    ukExports = fetch_series('Eurostat/namq_10_exi/Q.CLV05_MEUR.NSA.P6.UK')
    franceGDP = fetch_series('Eurostat/namq_10_gdp/Q.CLV05_MEUR.NSA.B1GQ.FR')
    franceExports = fetch_series('Eurostat/namq_10_exi/Q.CLV05_MEUR.NSA.P6.FR')
    ukGDP = ukGDP.query("period >= '2010'")
    ukExports = ukExports.query("period >= '2010'")
    franceGDP = franceGDP.query("period >= '2010'")
    franceExports = franceExports.query("period >= '2010'")
    toSave = (ukGDP, ukExports, franceGDP, franceExports)
    for ukGDP in toSave:
        #yes it's bad form to name my variables this way, but I first
        #had to test to see if this would work for one dataFrame before making
        #a for loop and I didn't wanna go and change every single name
        ukGDP.drop('National accounts indicator (ESA 2010)', axis = 1, inplace = True)
        ukGDP.drop('Geopolitical entity (reporting)', axis = 1, inplace = True)
        ukGDP.drop('Seasonal adjustment', axis = 1, inplace = True)
        ukGDP.drop('Unit of measure', axis = 1, inplace = True)
        ukGDP.drop('@frequency', axis = 1, inplace = True)
        ukGDP.drop('provider_code', axis = 1, inplace = True)
        ukGDP.drop('dataset_code', axis = 1, inplace = True)
        ukGDP.drop('dataset_name', axis = 1, inplace = True)
        ukGDP.drop('series_code', axis = 1, inplace = True)
        ukGDP.drop('series_name', axis = 1, inplace = True)
        ukGDP.drop('original_period', axis = 1, inplace = True)
        ukGDP.drop('Frequency', axis = 1, inplace = True)
        ukGDP.drop('FREQ', axis = 1, inplace = True)
        ukGDP.drop('unit', axis = 1, inplace = True)
        ukGDP.drop('s_adj', axis = 1, inplace = True)
        ukGDP.drop('na_item', axis = 1, inplace = True)
        ukGDP.drop('geo', axis = 1, inplace = True)
        ukGDP.drop('original_value', axis =1, inplace = True)
    pandas.set_option('display.max_rows',None)
    pandas.set_option('display.max_columns', None)
    print(toSave)
    pickle.dump(toSave, open('euroFundamentalData.pkl','wb'))


def FundamentalsTest():
    print("running FundamentalsTest")
    mData = marketData()
    startTime = time.time();
    fad = mData.getFundamentalAnalysisData()
    print(fad)
    endTime = time.time() - startTime;
    print("Time to finish: " + str(endTime));

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

def maxTest():
    print(max(1,1));

def main():
    sendToTestingFacilityTest()


if __name__ == "__main__":
	main()
