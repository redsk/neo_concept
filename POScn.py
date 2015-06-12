#!python

import os
#import cPickle as pickle
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



#"/c/en/child_car_seat"  "/c/en/backseat_of_car" "/r/AtLocation" 2.0     "/d/conceptnet/4/en"    "*Something you find in [[the backseat of a car]] is [[a child's car seat]]"
#"/c/en/child_country_home"      "/c/en/unite_state"     "/r/AtLocation" 0.5849625007211562      "/d/dbpedia/en" ""



def getSurfaceTexts(inputFilename, surfaceTextFilename):
    ef = open(inputFilename, "r")
    relationLines = ef.readlines()
    ef.close()

    nf = open(surfaceTextFilename, "w")

    relsWithSurface = {}

    for i, line in enumerate(relationLines):
        if i == 0:
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


        #print tokens[5]

        relsWithSurface[i] = True
        # removing the quotes around the surface text and the final '\n'
        surface = tokens[5][1:-2]
        # if there is no dot at the end, we add it:
        if surface[-1] != '.':
            surface = surface + '.'
        # finally, we add a '\n'
        nf.write(surface + '\n')

    nf.close()

    return relationLines, relsWithSurface

    #for i in relsWithSurface:
    #    print i
    #pickle.dump( relsWithSurface, open("test.p", "wb") )



def generatePOSrelationsFile(relationsWithPOSfilename, snlpOutFilename, relationLines, relsWithSurface):
    rf = open(relationsWithPOSfilename, 'w')
    sf = open(snlpOutFilename, 'r')


    rf.write(':START_ID\t:END_ID\t:TYPE\tweight:float\tsource\tsurface\tpos1\tpos2\n')

    for i, relLine in enumerate(relationLines):
        if i is 0:
            continue
        if relsWithSurface[i] is False:
            rf.write(relLine[:-1] + '\t""\t""\n')
        else:
            relsTokens = relLine.split('\t')
            c1 = relsTokens[0][7:-1]
            c2 = relsTokens[1][7:-1]

            wordsFirst = ''
            wordsSecond = ''
            POSfirst = ''
            POSsecond = ''
            
            state = 0 # 0 = before first pair of -LSB-
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
                rf.write(relLine[:-1] + '\t"' + POSfirst + '"\t"' + POSsecond + '"\n')
                #rf.write(relLine[:-1] + '\t"' + POSfirst + '"\t"' + POSsecond + '"\t"' + c1 + '"\t"' + c2 + '"\t"' + wordsFirst + '"\t"' + wordsSecond + '"\n')
            else: # they are inverted!
                rf.write(relLine[:-1] + '\t"' + POSsecond + '"\t"' + POSfirst + '"\n')
                #rf.write(relLine[:-1] + '\t"' + POSsecond + '"\t"' + POSfirst + '"\t"' + c1 + '"\t"' + c2 + '"\t"' + wordsFirst + '"\t"' + wordsSecond + '"\n')


    sf.close()
    rf.close()



def main():
    ################ FILES CONSTANTS
    inputFilename = 'edges.csv'
    surfaceTextFilename = ''
    stanfordNLPdir = "../../stanford-corenlp-python/stanford-corenlp-full-2015-01-30"
    java_memory = '8' # in GB
    ################

    baseName = inputFilename.split('.')[0]
    surfaceTextFilename = baseName + '.txt'
    relationsWithPOSfilename = baseName + 'POS.csv'
    snlpOutFilename = surfaceTextFilename + ".conll"


    relationLines, relsWithSurface = getSurfaceTexts(inputFilename, surfaceTextFilename)

    start_corenlp = 'java -cp "*" -Xmx' + java_memory + 'g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma -file ../../neo4j-conceptnet5/converter/' + surfaceTextFilename + ' -outputFormat conll'
    corenlp = pexpect.spawn(start_corenlp, cwd=stanfordNLPdir)
    corenlp.expect(pexpect.EOF, timeout=14400) # four hours timeout

    old = stanfordNLPdir + "/" + snlpOutFilename
    new = "./" + snlpOutFilename
    #print old
    #print new
    os.rename(old, new)

    generatePOSrelationsFile(relationsWithPOSfilename, snlpOutFilename, relationLines, relsWithSurface)


    #numargs = len(sys.argv)
    #if numargs == 3:
    #    cn5ToCSV(sys.argv[1], True)
    #if numargs == 2:
    #    cn5ToCSV(sys.argv[1], False)
    #if numargs < 2 or numargs > 3:
    #    print "Usage:\npython convertcn.py <input directory> [ALL_LANGUAGES]\n"

if __name__ == "__main__":
    main()
