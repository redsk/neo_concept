#!python

import os
import glob
import re
import operator

nodeid = 0
nodes = {}
nf = 0

sources = {}

def get_node_id(node):
    global nodes
    global nodeid
    global nf
    if node in nodes:
        return nodes[node]
    else:
        nodes[node] = nodeid
        nodeid = nodeid + 1
        nf.write(str(nodes[node]) + '\t' + node + '\n')
    return nodes[node]

def add_node(node):
    global nodes
    global nf
    if node in nodes:
        nodes[node] = nodes[node] + 1
    else:
        nodes[node] = 1
        nf.write(node + '\t' + "Concept\n")

def add_source(source):
    global sources
    if source in sources:
        sources[source] = sources[source] + 1
    else:
        sources[source] = 1

def cn5ToCSV(inputDir):
    global nodes 
    global nodeid 
    global nf
    nodes = {}
    nodeid = 0

    global sources
    sources = {}

    nf = open('../nodes.csv', "w")
    #nf.write('id\tconcept\n')
    nf.write('id:ID\t:LABEL\n')
    ef = open('../edges.csv', "w")
    #ef.write('idfrom\tidto\ttype\tcontext\tweight\tsurface\n')
    ef.write(':START_ID\t:END_ID\t:TYPE\tcontext\tweight:float\tsource\tsurface\n')
    
    for filename in glob.glob(os.path.join(inputDir, '*.csv')):
        with open (filename, "r") as f:
            for line in f:
                #tokens = line[0:-1].split('\t')
                tokens = line[0:-1].split('\t')
                
                #fromN = get_node_id(esc(tokens[2]))
                #toN = get_node_id(esc(tokens[3]))

                fromN = esc(tokens[2])
                toN = esc(tokens[3])
                add_node(fromN)
                add_node(toN)

                source = esc(tokens[8])
                add_source(source)

                ef.write(str(fromN) + '\t' + str(toN) + '\t' + esc(tokens[1]) + '\t' + esc(tokens[4]) + '\t' + escFloat(tokens[5]) + '\t' + source + '\t' + esc(tokens[9]) + '\n')
    
    nf.close()
    ef.close()

    sorted_sources = sorted(sources.items(), key=operator.itemgetter(1))
    sorted_sources.reverse()
    sf = open('../sources.csv', "w")
    for source in sorted_sources:
        sf.write(source[0] + '\t' + str(source[1]) + '\n')
    sf.close()

def esc(s):
    s = re.sub(r"\\", "", s)
    s = re.sub(r"\"", "\\\"", s)
    return '"' + s + '"'
    #return '"' + re.sub(r"([^\\\\])(\")", "\g<1>\\\\\g<2>", s) + '"'

def escFloat(s):
    return re.sub(r"L", "", s)    

def main():
    cn5ToCSV('../csv_current/assertions/')


if __name__ == "__main__":
    main()
