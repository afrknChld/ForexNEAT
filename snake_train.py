import neat
import pickle
import sys
import os
import json
import time
import gzip
import random
import requests
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from snakeRunner import snakeRunner, snakeNN

print(neat.__file__);

class populationSave(object):
    def __init__(self, population, gen, curID):
        self.population = population;
        self.gen = gen
        self.curID = curID
        self.rndstate = random.getState()

def writeErrorLog(e):
    URL = "https://forexnntracker.herokuapp.com/errorlog"
    data = {"error": str(e)}
    r = requests.post(URL, data = data)



def readFromGenFile():
    genFile = open("gen.txt","r")
    toReturn = {
        "s": int(genFile.readline()),
        "l": int(genFile.readline()),
        "gen": int(genFile.readline()),
        "savefile": genFile.readline(),
        "loadfile": genFile.readline(),
        "curID": int(genFile.readline()),
        "winnerID": int(genFile.readline())
    };
    genFile.close()
    return toReturn;

def writeToGenFile(s,savefile,l,loadfile,gen,curID,winnerID = 0):
    if(savefile == ""):
        savefile = "None\n"
    elif(savefile[-1] != '\n'):
        savefile = savefile + "\n"
    if(loadfile == ""):
        loadfile = "None\n"
    elif(loadfile[-1] != '\n'):
        loadfile = loadfile + "\n"
    genFile = open("gen.txt","w")
    genFile.truncate()
    genFile.write(str(s) + "\n" + str(l) + "\n" + str(gen) + "\n");
    genFile.write(str(savefile) + str(loadfile) + str(curID) + "\n" + str(winnerID));
    genFile.close()

def sendUpdateToServer(info):
    dataString = json.dumps(info)
    updateURL = "https://forexnntracker.herokuapp.com/trainingfactoryupdate"
    data = {"info": dataString}
    r = requests.post(updateURL, data = data)

def sendToTestingFacility(info, filename):
    exIP = "ec2-3-23-59-116.us-east-2.compute.amazonaws.com"
    user = "ec2-user"
    pickle.dump(info, open(filename,"wb"))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file("/home/cole/.ssh/id_rsa")
    ssh.connect(exIP, pkey = key, username = user)
    scp = SCPClient(ssh.get_transport())
    scp.put(filename, remote_path = "/home/ec2-user/forexNEAT-testing-factory/toTestingFactory")
    scp.close()
    print("removing: " + str(filename))
    os.remove("/home/cole/forex/" + str(filename))


# Driver for NEAT solution to FlapPyBird
def evolutionary_driver(n=0,load = False, loadfile = "", save = False, savefile = ""):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         'config')

    # Create the population, which is the top-level object for a NEAT run.
    if load:
        pSave = pickle.load(open(loadfile,'rb'))
        p = pSave.population;
        gen = pSave.gen
        curID = pSave.curID
        random.setstate(pSave.rndstate)
    else:
        p = neat.Population(config)
        p.add_reporter(neat.StdOutReporter(False))
        if save:
            p.add_reporter(neat.Checkpointer(generation_interval = 5,
                                        filename_prefix = savefile,
                                        test_check = 0));
        gen = 0;
        curID = 0;

    # Add a stdout reporter to show progress in the terminal.

    if save:
        s = 1
    else:
        s = 0
    if load:
        l = 1
    else:
        l = 0

    writeToGenFile(s, savefile, l, loadfile, gen, curID);

    # Run until we acheive n.
    if n == 0:
        n = None

    run_loop2 = True
    while(run_loop2):
        try:
            winner = p.run(eval_genomes, n=n)
            run_loop2 = False
        except Exception as e:
            print(e)
            writeErrorLog(e)

    winnerID = readFromGenFile()["winnerID"];

    winnerSnake = snakeNN(winner, config, winnerID);
    # dump
    pickle.dump(winnerSnake, open('winner.pkl', 'wb'))

    if save:
        genFileResults = readFromGenFile()
        gen = genFileResults["gen"]
        curID = genFileResults["curID"];
        pSave = populationSave(p,gen, curID);
        pickle.dump(pSave, open(savefile,'wb'))


def eval_genomes(genomes, config):
    genFileResults = readFromGenFile();
    s = genFileResults["s"];
    l = genFileResults["l"];
    gen = genFileResults["gen"];
    savefile = genFileResults["savefile"];
    loadfile = genFileResults["loadfile"];
    curID = genFileResults["curID"];

    idx,genomes = zip(*genomes)

    runner = snakeRunner(genomes, config, gen, curID);
    run_loop = True
    while(run_loop):
        try:
            runner.run(True)
            results = runner.getResults()
            run_loop = False
        except Exception as e:
            print(e)
            writeErrorLog(e)

    top_fitness = 0
    failed_count = 0
    fitness_total = 0
    money_made_total = 0
    top_money_made = 0
    runner_up_fitness = [0,0,0,0]
    winners = [None,None,None,None,None]
    positive_money_count = 0
    for result, genomes in results:
        money_made = result["fitness"];
        balance = result["balance"];
        equity = result["equity"];
        failed = result["failed"];
        id = result["id"];
        totalLoss = result["totalLoss"]
        totalProfit = result["totalProfit"]
        max_drawdown = result["max_drawdown"]
        balance_equity_disparity = equity-balance

        fitness = money_made + (balance_equity_disparity * .1) - (totalLoss * .1) - (max_drawdown * 100)
        if failed:
            failed_count += 1
            fitness = -2000

        genomes.fitness = fitness

        #print("fitness for NN of id "+ str(id) +" is: " + str(fitness));
        fitness_total += fitness

        money_made_total += money_made

        if money_made > 0:
            positive_money_count += 1
        if money_made > top_money_made:
            top_money_made = money_made

        if fitness > top_fitness:
            top_fitness = fitness
            winnerID = id
            if fitness > 0 :
                winners[0] = {
                    "id": id,
                    "genome": genomes,
                }
        elif fitness > runner_up_fitness[0]:
            runner_up_fitness[0] = fitness
            if fitness > 0 :
                winners[1] = {
                    "id": id,
                    "genome": genomes,
                }
        elif fitness > runner_up_fitness[1]:
            runner_up_fitness[1] = fitness
            if fitness > 0 :
                winners[2] = {
                    "id": id,
                    "genome": genomes,
                }
        elif fitness > runner_up_fitness[2]:
            runner_up_fitness[2] = fitness
            if fitness > 0 :
                winners[3] = {
                    "id": id,
                    "genome": genomes,
                }
        elif fitness > runner_up_fitness[3]:
            runner_up_fitness[3] = fitness
            if fitness > 0 :
                winners[4] = {
                    "id": id,
                    "genome": genomes,
                }

        curID = id

    average_fitness = fitness_total / len(results)
    average_money_made = money_made / len(results)
    print("The top fitness for this generation is: " + str(top_fitness))

    gen+=1
    writeToGenFile(s, savefile, l, loadfile, gen, curID,winnerID);

    for winner in winners:
        if winner == None:
            winners.remove(winner)



    sendToTestingFacility({
        "config": config,
        "winners": winners
    }, "toTestingFacility" + str(gen) + ".pkl")

    sendUpdateToServer({
        "average_money_made": average_money_made,
        "top_money_made": top_money_made,
        "gen": gen-1,
        "num_snakes_trained": curID,
        "positive_money_count": positive_money_count,
        "failed_count": failed_count,
        "average_fitness": average_fitness,
        "top_fitness": top_fitness,
        "gen_size": len(results),
    })



def main():
    start_time = time.time()
    if len(sys.argv)>1:
        n = 0;
        load = False
        save = False
        loadfile = "";
        savefile = "";
        try:
            n = int(sys.argv[1]);
            print("stopping after " + str(n) + " generations");
        except ValueError:
            n = 0;

        for i in range(0,len(sys.argv)):
            arg = sys.argv[i];
            if arg == "-l":
                load = True
                loadfile = sys.argv[i+1];
                print("loading from " + loadfile);
            if arg == "-s":
                save = True
                savefile = sys.argv[i+1]
                print("saving to " + savefile)
        evolutionary_driver(n,load,loadfile,save, savefile);
    else:
        evolutionary_driver()
    print("Time to Execute: " + str(time.time()-start_time) + " seconds");

if __name__ == "__main__":
	main()
