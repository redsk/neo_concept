Neo_Concept
-----------

Sample import for ConceptNet5 dataset as a regular graph. Adapted to Conceptnet 5.3 csv files. Adapted to neo4j 2.1.6

Pre-Requisites
--------------

To regenerate: Download and compile the [Neo4j Batch Importer](https://github.com/jexp/batch-import) and place it in a directory as the same level as this one. 

Or Download the Neo4j [graph.db](https://dl.dropboxusercontent.com/u/57740873/conceptnet.graph.db.zip) from dropbox and place in your Neo4j data directory.

How-To From Scratch
-------------------

    bundle

    download current version of conceptnet 5 from http://conceptnet5.media.mit.edu/downloads/current/ by getting the csv version. Put the file inside the directory neo_concept. 
    tar jxvf conceptnet5_flat_csv_< version >.tar.bz2 
    
    bundle exec rake neo4j:create
    bundle exec rake neo4j:load
    #rake neo4j:start_no_wait


Goto localhost:7474 to see graph.


