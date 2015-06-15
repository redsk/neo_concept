#!python

import os
import cPickle as pickle
import pexpect
import sys


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
 
    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)
 
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
 
    return previous_row[-1]



class POScn():
    def __init__(self, filename, batch_size, total_size):
        ################ FILES CONSTANTS
        self.inputFilename = filename
        self.stanfordNLPdir = "../../stanford-corenlp-python/stanford-corenlp-full-2015-01-30"
        self.neoConceptRootForSNLP = '../../neo4j-conceptnet5/converter/'
        self.java_memory = '2' # in GB
        ################

        self.baseName = self.inputFilename.split('.')[0]
        self.surfaceTextFilename = self.baseName + '.txt'
        self.surfaceTextFilenameBatch = self.baseName + '.batch.txt'
        self.relsWithSurfaceFilename = self.baseName + '.p'
        self.relationsWithPOSfilename = self.baseName + 'POS.csv'
        self.snlpOutFilename = self.surfaceTextFilename + ".conll"
        self.snlpOutFilenameBatch = self.surfaceTextFilenameBatch + ".conll"

        self.batch_size = batch_size
        self.total_size = total_size

#"/c/en/child_car_seat"  "/c/en/backseat_of_car" "/r/AtLocation" 2.0     "/d/conceptnet/4/en"    "*Something you find in [[the backseat of a car]] is [[a child's car seat]]"
#"/c/en/child_country_home"      "/c/en/unite_state"     "/r/AtLocation" 0.5849625007211562      "/d/dbpedia/en" ""

    def getSurfaceTexts(self):
        ef = open(self.inputFilename, "r")
        relationLines = ef.readlines()
        ef.close()

        nf = open(self.surfaceTextFilename, "w")

        relsWithSurface = {}

        for i, line in enumerate(relationLines):
            if i == 0:
                relsWithSurface[i] = False
                continue

            tokens = line.split('\t')

            # surface is at tokens[5], '""' means no surface text
            try:
                if tokens[5] == '""\n':
                    relsWithSurface[i] = False
                    continue
            except:
                print i, line
                sys.exit("Error!!!")

            relsWithSurface[i] = True
            # removing the quotes around the surface text and the final '\n'
            surface = tokens[5][1:-2]
            # if there is no dot at the end, we add it:
            if surface[-1] != '.':
                surface = surface + '.'
            # finally, we add a '\n'
            nf.write(surface + '\n')

        nf.close()


        pickle.dump( relsWithSurface, open(self.relsWithSurfaceFilename, "wb") )

        #return relationLines, relsWithSurface
        #return relsWithSurface

    def countWithSurface(self):
        rf = None
        self.rfCounter = 0
        self.rfCounterWithSurface = 0

        try:
            rf = open(self.relationsWithPOSfilename, 'r')
            for line in rf:
                if relsWithSurface[self.rfCounter] is True:
                    self.rfCounterWithSurface = self.rfCounterWithSurface + 1
                self.rfCounter = self.rfCounter + 1
            rf.close()
        except:
            pass


        print "self.rfCounter =", self.rfCounter
        print "self.rfCounterWithSurface = ", self.rfCounterWithSurface

    def checkSurfaceTextFile(self, maxCheck = None):
        stats = {}
        numberOfLines = 0
        f = open(self.surfaceTextFilename)
        for idx, l in enumerate(f):
            numberOfLines = numberOfLines + 1
            n = l.count('.')
            if n != 1:
                if n in stats.keys():
                    stats[n] = stats[n] + 1
                else:
                    stats[n] = 1
                print idx, n, l,
            if maxCheck is not None:
                if idx >= maxCheck:
                    break
        f.close()

        tot = 0
        print 'Numbers of "." where != 1:'
        for i in stats:
            print i, stats[i]
            tot = tot + stats[i]
        print tot, 'out of', numberOfLines


    def generatePOSrelationsFile(self):
        self.relsWithSurface = pickle.load( open( self.relsWithSurfaceFilename, "rb" ) )

        self.rf = None
        self.rfCounter = 0
        self.rfCounterWithSurface = 0

        try:
            self.rf = open(self.relationsWithPOSfilename, 'r')
            for line in self.rf:
                if self.relsWithSurface[self.rfCounter] is True:
                    self.rfCounterWithSurface = self.rfCounterWithSurface + 1
                self.rfCounter = self.rfCounter + 1
            self.rf.close()
        except:
            pass


        self.rf = open(self.relationsWithPOSfilename, 'a+')
        self.nf = open(self.surfaceTextFilename, "r")

        for i in range(0, self.rfCounterWithSurface):
            self.nf.readline()


        while True:
            print "rfCounter =", self.rfCounter
            print "rfCounterWithSurface = ", self.rfCounterWithSurface

            self.rfCounter, writtenSurfaceRels = self.generatePOSrelationsFileBatch()
            self.rfCounterWithSurface = self.rfCounterWithSurface + writtenSurfaceRels

            if self.batch_size == 0: # finished...
                break

            if self.rfCounterWithSurface == self.total_size:
                break

        self.nf.close()
        self.rf.close()

        print "rfCounter =", self.rfCounter
        print "rfCounterWithSurface = ", self.rfCounterWithSurface



    def generatePOSrelationsFileBatch(self):
        bf = open(self.surfaceTextFilenameBatch, "w")
        for i in range(0, self.batch_size):
            l = self.nf.readline()
            if l == '':
                self.batch_size = i
                break
            else:
                bf.write(l)
        bf.close()

        if self.batch_size == 0: # we have finished
            return self.rfCounter, 0
        
        start_corenlp = 'java -cp "*" -Xmx' + self.java_memory + 'g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma -ssplit.eolonly -file ' + self.neoConceptRootForSNLP + self.surfaceTextFilenameBatch + ' -outputFormat conll'
        #print start_corenlp
        corenlp = pexpect.spawn(start_corenlp, cwd=self.stanfordNLPdir)
        corenlp.expect(pexpect.EOF, timeout=14400) # four hours timeout

        old = self.stanfordNLPdir + "/" + self.snlpOutFilenameBatch
        new = "./" + self.snlpOutFilenameBatch
        #print old
        #print new
        os.rename(old, new)


        sf = open(self.snlpOutFilenameBatch, 'r')

        if self.rfCounter == 0:
            self.rf.write(':START_ID\t:END_ID\t:TYPE\tweight:float\tsource\tsurface\tpos1\tpos2\n')

        inf = open(self.inputFilename, "r")
        for i in range(0, self.rfCounter):
            inf.readline()

        #for i, relLine in enumerate(relationLines):
        #for n in range(0, self.batch_size):
        writtenSurfaceRels = 0
        n = 0
        while True:
            if writtenSurfaceRels == self.batch_size:
                break
            if self.rfCounterWithSurface + writtenSurfaceRels == self.total_size:
                break
            i = self.rfCounter + n
            n = n + 1
            relLine = inf.readline()
            if i is 0: # it's the header
                continue
            if self.relsWithSurface[i] is False:
                self.rf.write(relLine[:-1] + '\t""\t""\n')
            else:
                writtenSurfaceRels = writtenSurfaceRels + 1
                relsTokens = relLine.split('\t')
                c1 = relsTokens[0][7:-1]
                c2 = relsTokens[1][7:-1]

                wordsFirst = ''
                wordsSecond = ''
                POSfirst = ''
                POSsecond = ''
                
                state = 0  # 0 = before first pair of -LSB-
                           # 1 = on first pair of -LSB-
                           # 2 = on first set of words
                           # 3 = after first set of words
                           # 4 = on second pair of -LSB-
                           # 5 = on second set of words
                           # 6 = after second set of words

                # AN EXAMPLE OF THE OUTPUT OF SNLP
                # 1   -LSB-   -lsb-   -LRB-   _   _   _
                # 2   -LSB-   -lsb-   -LRB-   _   _   _
                # 3   abdication  abdication  NN  _   _   _
                # 4   -RSB-   -rsb-   -RRB-   _   _   _
                # 5   -RSB-   -rsb-   -RRB-   _   _   _
                # 6   is  be  VBZ _   _   _
                # 7   the the DT  _   _   _
                # 8   opposite    opposite    NN  _   _   _
                # 9   of  of  IN  _   _   _
                # 10  -LSB-   -lsb-   -LRB-   _   _   _
                # 11  -LSB-   -lsb-   -LRB-   _   _   _
                # 12  power   power   NN  _   _   _
                # 13  -RSB-   -rsb-   -RRB-   _   _   _
                # 14  -RSB-   -rsb-   -RRB-   _   _   _
                # 15  .   .   .   _   _   _
                #     <- EMPTY LINE HERE!
                # 1 .... OUTPUT FOR NEXT SENTENCE

                while True:
                    l = sf.readline()
                    #print 'l = "' + l + '"'
                    if l == '\n' or l == '':
                        break
                    else:
                        snlpTokens = l.split('\t')
                        if state is 0:
                            if snlpTokens[1] == '-LSB-':
                                state = 1
                            continue

                        if state is 1:
                            if snlpTokens[1] == '-LSB-':
                                continue
                            else:
                                state = 2
                                # no continue here, we go to state 2

                        if state is 2:
                            if snlpTokens[1] == '-RSB-':
                                state = 3
                                continue
                            else:
                                wordsFirst = wordsFirst + snlpTokens[1] + " "
                                POSfirst = POSfirst + snlpTokens[3] + " "

                        if state is 3:
                            if snlpTokens[1] == '-LSB-':
                                state = 4
                            continue

                        if state is 4:
                            if snlpTokens[1] == '-LSB-':
                                continue
                            else:
                                state = 5
                                # no continue here, we go to state 5

                        if state is 5:
                            if snlpTokens[1] == '-RSB-':
                                state = 6
                                continue
                            else:
                                wordsSecond = wordsSecond + snlpTokens[1] + " "
                                POSsecond = POSsecond + snlpTokens[3] + " "

                        if state is 6:
                            continue

                # there is an extra space after all of them
                wordsFirst = wordsFirst[:-1]
                wordsSecond = wordsSecond[:-1]
                POSfirst = POSfirst[:-1]
                POSsecond = POSsecond[:-1]


                # we are not sure whether wordsFirst corresponds to c1 and 
                # wordsSecond corresponds to c2: they could be inverted in the sentence!
                lw1c1 = levenshtein(c1, wordsFirst)
                lw1c2 = levenshtein(c2, wordsFirst)

                if (lw1c1 < lw1c2): # they are not inverted
                    self.rf.write(relLine[:-1] + '\t"' + POSfirst + '"\t"' + POSsecond + '"\n')
                    #rf.write(relLine[:-1] + '\t"' + POSfirst + '"\t"' + POSsecond + '"\t"' + c1 + '"\t"' + c2 + '"\t"' + wordsFirst + '"\t"' + wordsSecond + '"\n')
                else: # they are inverted!
                    self.rf.write(relLine[:-1] + '\t"' + POSsecond + '"\t"' + POSfirst + '"\n')
                    #rf.write(relLine[:-1] + '\t"' + POSsecond + '"\t"' + POSfirst + '"\t"' + c1 + '"\t"' + c2 + '"\t"' + wordsFirst + '"\t"' + wordsSecond + '"\n')

        sf.close()
        return i + 1, writtenSurfaceRels # i + 1 because we have already done line i
        



if __name__ == "__main__":
    numargs = len(sys.argv)

    batch_size = 10000
    total_size = None

    if numargs >= 4:
        batch_size = int(sys.argv[3])
    if numargs == 5:
        total_size = int(sys.argv[4])

        # elif sys.argv[1] == 'check':
        #     poscn = POScn(sys.argv[2])
        #     poscn.checkSurfaceTextFile(int(sys.argv[3]))


    if numargs >= 3:
        if sys.argv[1] == 'surface':
            poscn = POScn(sys.argv[2], batch_size, total_size)
            poscn.getSurfaceTexts()
        elif sys.argv[1] == 'genpos':
            poscn = POScn(sys.argv[2], batch_size, total_size)
            poscn.generatePOSrelationsFile()
        # elif sys.argv[1] == 'count':
        #     poscn = POScn(sys.argv[2])
        #     poscn.countWithSurface()
        # elif sys.argv[1] == 'check':
        #     poscn = POScn(sys.argv[2])
        #     poscn.checkSurfaceTextFile()



    if numargs < 3 or numargs > 5:
       print "Usage:\npython POScn.py {surface, genpos} <input file> [batch_size]\n"
    #main()






