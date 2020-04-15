import neat
import pickle
import sys
import time
from snakeRunner import snakeRunner, snakeNN

print(neat.__file__);

class populationSave(object):
    def __init__(self, population, gen, curID):
        self.population = population;
        self.gen = gen
        self.curID = curID

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
    else:
        p = neat.Population(config)
        p.add_reporter(neat.StdOutReporter(False))
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

    winner = p.run(eval_genomes, n=n)

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
    #runner.configure(False,True)
    runner.run(True)
    results = runner.getResults()

    top_fitness = 0
    for result, genomes in results:
        fitness = result["fitness"];
        balance = result["balance"];
        equity = result["equity"];
        failed = result["failed"];
        id = result["id"];
        genomes.fitness = fitness

        #print("fitness for NN of id "+ str(id) +" is: " + str(fitness));

        if fitness > top_fitness:
            top_fitness = fitness
            winnerID = id

        curID = id

    print("The top fitness for this generation is: " + str(top_fitness))

    gen+=1
    writeToGenFile(s, savefile, l, loadfile, gen, curID,winnerID);





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
