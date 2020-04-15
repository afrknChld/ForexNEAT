import neat
import pickle
import sys
from snakeRunner import snakeRunner

class populationSave(object):
    def __init__(self, population, gen):
        self.population = population;
        self.gen = gen

def getGenFromFile():
    genFile = open("gen.txt","r")
    genFile.readline()
    genFile.readline()
    gen = genFile.readline()
    genFile.close()
    return gen;

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
    else:
        p = neat.Population(config)
        p.add_reporter(neat.StdOutReporter(False))
        gen = 0;

    # Add a stdout reporter to show progress in the terminal.

    if save:
        s = 1
    else:
        s = 0
    if load:
        l = 1
    else:
        l = 0

    genFile = open("gen.txt","w")
    genFile.truncate()
    genFile.write(str(s) + "\n" + str(l) + "\n" + str(gen))
    genFile.close()


    # Run until we acheive n.
    if n == 0:
        n = None

    winner = p.run(eval_genomes, n=n)

    # dump
    pickle.dump(winner, open('winner.pkl', 'wb'))

    if save:
        gen = getGenFromFile();
        pSave = populationSave(p,gen);
        pickle.dump(pSave, open(savefile,'wb'))


def eval_genomes(genomes, config):
    genFile = open("gen.txt","r")
    s = int(genFile.readline())
    l = int(genFile.readline())
    gen = int(genFile.readline())
    genFile.close()

    # Play game and get results
    idx,genomes = zip(*genomes)

    runner = snakeRunner(genomes, config, gen)
    #runner.configure(False,True)
    runner.run(True)
    results = runner.getResults()

    top_fitness = 0
    for result, genomes in results:
        fitness = result["fitness"];
        balance = result["balance"];
        equity = result["equity"];
        failed = result["failed"];
        genomes.fitness = fitness

        print("fitness for this NN is: " + str(fitness));

        if fitness > top_fitness:
            top_fitness = fitness

    print("The top fitness for this generation is: " + str(top_fitness))

    gen+=1
    genFile = open("gen.txt","w")
    genFile.write(str(s) + "\n" + str(l) + "\n" + str(gen))
    genFile.close()



def main():
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

if __name__ == "__main__":
	main()
