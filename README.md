Neo_Concept
-----------

This software imports the ConceptNet Knowledge Base (version tested: 5.3) into neo4j 2.2.2. 
This project was inspired by [a post from Max De Marzi](http://maxdemarzi.com/2013/05/13/knowledge-bases-in-neo4j/) who also provided [the original software](https://github.com/maxdemarzi/neo_concept).

This rewrite does not use the [Bloom filter](http://en.wikipedia.org/wiki/Bloom_filter) anymore as according to ConceptNet wiki [the uri is unique among assertions](https://github.com/commonsense/conceptnet5/wiki/Edges) and [the provided CSV files](http://conceptnet5.media.mit.edu/downloads/current/) provide a list of assertions. 

Moreover, this software adds relations to nodes in the same hierarchy. For instance, if we have nodes
- A: "/c/en/able"
- B: "/c/en/able/a/having_the_necessary_means_or_skill_or_know-how_or_authority_to_do_something"

normally the latter is **not** connected to the former with a relation. Therefore, we add the following two relations with weight 10.0 between these two nodes:
- A /r/DownHierarchy B
- B /r/UpHierarchy A

Optionally, it is possible to perform Part-Of-Speech (POS) tagging of the two concepts within the surface text of every relation by means of the Stanford CoreNLP software. 

- NEW!: Check out [Neo_Wordnet](https://github.com/redsk/neo_wordnet) to import Wordnet into neo4j!
- NEW!: Check out [Neo_Merger](https://github.com/redsk/neo_merger) to import Conceptnet and Wordnet into the same neo4j graph!

Pre-Requisites
--------------

- neo4j version 2.2.2 (needed for the [new import tool](http://neo4j.com/docs/2.2.2/import-tool.html))
- [ConceptNet 5.3](http://conceptnet5.media.mit.edu/downloads/current/) provides a list of assertions
- regular Python, no dependencies
- optionally, the latest version of [Stanford CoreNLP](http://nlp.stanford.edu/software/corenlp.shtml)

Tested with neo4j-community-2.2.2.

How-To 
-------------------

    mkdir neo4j-kbs
    cd neo4j-kbs
    git clone https://github.com/redsk/neo_concept.git

    # get latest conceptnet from http://conceptnet5.media.mit.edu/downloads/
    mkdir conceptnet
    cd concepnet
    wget http://conceptnet5.media.mit.edu/downloads/current/conceptnet5_flat_csv_5.3.tar.bz2
    tar jxvf conceptnet5_flat_csv_5.3.tar.bz2
    ln -s csv_<version> csv_current
    cd ..

    # Usage:
    # python convertcn.py <input directory> [ALL_LANGUAGES]
    # If the flag ALL_LANGUAGES is not set, only English concepts will be converted
    # this will take a while
    python neo_concept/convertcn.py conceptnet/csv_current/assertions/

    # optionally, you can get the POS tags. This assumes that stanford nlp is installed in
    # stanfordNLPdir = "../stanford-corenlp-python/stanford-corenlp-full-2015-01-30"
    # neoConceptRootForSNLP = '../../neo4j-kbs/conceptnet/'
    # modify the two variables above in POScn.py to fit your stanford nlp installation
    # the following commands will take a while and were tested with a java memory of 2GB
    python neo_concept/POScn.py surface conceptnet/edges.csv
    python neo_concept/POScn.py genpos conceptnet/edges.csv 50000
    python neo_concept/POScn.py poscount conceptnet/edges.csv

    # get latest neo4j (tested with neo4j-community-2.2.2)
    curl -O -J -L http://neo4j.com/artifact.php?name=neo4j-community-2.2.2-unix.tar.gz
    tar zxf neo4j-community-2.2.2-unix.tar.gz

    # do only one of the two import commands below. If you calculated the POS tags, edges.csv is no longer needed

    # import nodes.csv and edges.csv using the new import tool (WITHOUT POS TAGS!) -- this will take a while too
    neo4j-community-2.2.2/bin/neo4j-import --into neo4j-community-2.2.2/data/graph.db --nodes conceptnet/nodes.csv --relationships conceptnet/edges.csv --delimiter "TAB"

    # import nodes.csv and edges.csv using the new import tool (WITH POS TAGS!) -- this will take a while too
    neo4j-community-2.2.2/bin/neo4j-import --into neo4j-community-2.2.2/data/graph.db --nodes conceptnet/nodes.csv --relationships conceptnet/edgesPOS.csv --delimiter "TAB"

    # start neo4j
    neo4j-community-2.2.2/bin/neo4j start


Goto localhost:7474 to see the graph. Create and index on Concepts for performance reasons:

    CREATE INDEX ON :Concept(id)

You can now query the database. Example:

    MATCH (sushi {id:"/c/en/sushi"}), sushi-[r]->other_concepts
    RETURN sushi.id, other_concepts.id, type(r), r.context, r.weight, r.surface
