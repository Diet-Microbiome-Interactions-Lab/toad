# Guide to the TOAD package

## Classes:  
**JScribe**: base class for implementing JDN/JSON serialization / deserialization  

**NUCLS**: NUCLeotide Sequence/String  (pronounced like "knuckles"). Technically, I can be any sequence of nucleotides OR amino acids.
I am a 2-tuple of the form (signature, sequence), where *signature* is an instance of DASH, and *sequence* can be either a string or bytes.  

- If sequence is bytes with the first byte being ASCII 'Z', then the sequence should be interpreted as gzsequence (GZIP compressed).  

- If sequence is a string, it should be interpreted as the literal nucleotide sequence.  

``` python

nucls = common.NUCLS("ATGCA")
>>> ATGCA
nucls = common.NUCLS("aalksa", "ATGC", b'akx')
>>> "ATGC"
print(nucls[0])
>>> aalksa
print(nucls[1])
>>> ATGC
print(nucls[2])
>>> b'akx'

```

**DASH**: DnA Hash  
Example:  

``` python

myclass = common.DASH("ATGCAA")
>>> `9^)u3U)@}@tKA7Vr;0&  # Hashed DNA
OR
myclass = common.DASH(shakeup="ATGCCGGCTA")
>>> `9^)u3U)@}@tKA7Vr;0&  # Hashed DNA

# Using the function:  
if isinstance(dna, str):
    dnas = str(dna)
    return base64.b85encode(hashlib.shake_128(dnas.encode('utf-8')).digest(16)).decode('utf-8')
```

**DRuID**: Descrete RUn ID  
Example:  

``` python
mydruid = common.DRuID("seqrun1")
>>> seqrun1
```

**GrIN**: Group Identitying Name  
Example:  

``` python
mygrin = common.GrIN("New group")
>>> New group
```

**Grove**: Abstract Base Class for a collection of DRuIDs. A collection of druids represents a discrete run ids.  
Example:  

``` python
grove2 = common.Grove(members=[druida, druidb], frozen=False)
print(grove2.frozen)
print(grove2.members)
>>> False  
>>> {('seqB',), ('seqA',)}
```

**SqRL**: Sequence / Run + Labels (DD updates with "entry" as a domain term for the record level content in a fasta/fastq file)  

**Group**: a named collection of SqRLs  

**Roster**: a lightweight representation of a Group - contains the set of DRuIDs associated with a named Group.