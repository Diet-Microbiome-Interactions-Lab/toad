# Tidy Organization and Analysis of DNA (TOAD) :mushroom:  
## Start Here :smiley:
<span style="color:red">Configuration</span>  
By default, TOAD searches for configuration files in the location: ~/.config/toad/*.yml, where the tilde (~) represents the user's home directory and the asterisk (\*) followed by .yml represents any file with the .yml extension. TOAD has a hierarchy of configuration settings, where at the base level it grabs config variables from this location.  
The user can also specify via the COMMAND LINE more configuration parameters, as well as more configuration (\*.yml) files. For example, the default config.yml may specify:  

```yaml
db : toad_test_db
lab: Smith_Lab
project: ProjectX
```  

The user can come to the command line and execute TOAD, overriding default configuration variables and extending variables as such:  

```bash
$ TOAD ingest reads scan: fasta_files/ collection: fasta_reads db: toad_NEW_db
```  

Above, the user specified 2 new configuration parameters using the KEYWORD: VALUE syntax ---> <code>collection: fasta_reads</code> & <code>scan: fasta\_files</code>. The user also overrided the variable db via the command line syntax <code>db: toad\_NEW\_db</code>.

<span style="color:orange">Before running TOAD the first time</span>, create a config.yml file and put it in the following location ~/.config/toad/config.yml. **If you do not, you must specify all required default configuration parameters EVERY TIME from the command line.**  
### Default Configuration variables:  

```yaml
db: "toad_test"
db_address: "localhost"
lab: "Smith"
port: 27017
project: "Project X"
user: "CHANGEME"
```

Of course, you can add as many other configuration variable as you wish, such as standard metadata that you want to ensure gets attached to all actions for logging and auditing purposes.

##<span style="color:green">User Guide</span> 

###Consuming READ data into your database:  
Reads come hot off the press from sequencing machines. Thus, metadata about the sequencing run is required.  
<code style="color : black">\$ python toad_test.py ingest reads scan: ../test/fastqs</code>  
If you want to specify which fastq files you want to read, you can also do that with:  


###Consuming CONTIG data into your database:  
Contigs are generated downstream of Reads and require metadata about how they were created.  
<code>$ python toad_test.py ingest contigs scan: ../test/fastas</code>

###Querying reads based on any number of exact matches to read documents:  
Example 1:  
<code>python toad_test.py vomit reads filter.lab: lindemann filter.project: X</code>  

Above, use the syntax <code>filter.KEYWORD</code> in order to filter your results.  

Example 2:  
<code>python toad_test.py vomit reads filter.lab: lindemann dna: ATGCCGGACAGGC</code>  

###
