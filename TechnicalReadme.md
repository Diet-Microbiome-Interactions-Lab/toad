# Guide to the TOAD package

## Classes:

**JScribe**: base class for implementing JDN/JSON serialization / deserialization

**Nucleotides**: Nucleotide Sequence/String. Technically, I can be any sequence of nucleotides OR amino acids.
I am a 3-tuple of the form (signature, sequence, gzipped sequence), where _signature_ is an instance of DnaHash, and _sequence_ can be either a string or bytes.

- If sequence is bytes with the first byte being ASCII 'Z', then the sequence should be interpreted as gzsequence (GZIP compressed).

- If sequence is a string, it should be interpreted as the literal nucleotide sequence.

```python

nucls = common.Nucleotides("ATGCA")
>>> ATGCA
nucls = common.Nucleotides("aalksa", "ATGC", b'akx')
>>> "ATGC"
print(nucls[0])
>>> aalksa
print(nucls[1])
>>> ATGC
print(nucls[2])
>>> b'akx'

```

**DnaHash**: DnA Hash  
Example:

```python

myclass = common.DnaHash("ATGCAA")
>>> `9^)u3U)@}@tKA7Vr;0&  # Hashed DNA
OR
myclass = common.DnaHash(shakeup="ATGCCGGCTA")
>>> `9^)u3U)@}@tKA7Vr;0&  # Hashed DNA

# Using the function:
if isinstance(dna, str):
    dnas = str(dna)
    return base64.b85encode(hashlib.shake_128(dnas.encode('utf-8')).digest(16)).decode('utf-8')
```

**UniqueRunID**: Descrete RUn ID  
Example:

```python
myUniqueRunID = common.UniqueRunID("seqrun1")
>>> seqrun1
```

**GroupIdentifier**: Group Identitying Name  
Example:

```python
myGroupIdentifier = common.GroupIdentifier("New group")
>>> New group
```

**RunsCollection**: Abstract Base Class for a collection of UniqueRunIDs. A collection of UniqueRunIDs represents a discrete run ids.  
Example:

```python
RunsCollection2 = common.RunsCollection(members=[UniqueRunIDa, UniqueRunIDb], frozen=False)
print(RunsCollection2.frozen)
print(RunsCollection2.members)
>>> False
>>> {('seqB',), ('seqA',)}
```

**SequenceAndSignature**: Sequence / Run + Labels (DD updates with "entry" as a domain term for the record level content in a fasta/fastq file)  
Example:

```python

sqrl = common.SequenceAndSignature("Identifier1", Nucleotides)
>>> (('Identifier1',), ('aalksa',), 'ATGC', ('???',))
sqrl = common.SequenceAndSignature("Identifier1", Nucleotides, group="The A Team")
>>> (('Identifier1',), ('aalksa',), 'ATGC', ('The A Team',))

```

This is in the form of:  
(UniqueRunID(ID), sig, seq, GroupIdentifier(group))  
Where sig == NUCL.signature (DnaHash) and seq == NUCL.sequence

**SignatureAndGroup**: Inherits from **RunsCollection** & **JScribe**. Takes in sig, members, groups, and \*\*kwargs and inits (**init**) self.signature == DnaHash(sig) & self.group == GroupIdentifier(group).

A SignatureAndGroup consists of a DNA signature and a Group, as represented by DnaHash(sig) and Group(GroupIdentifier).

```python

class SignatureAndGroup(RunsCollection, JScribe):
    _TYPE = "TOAD.SignatureAndGroup"
    def __init__(self, sig, members=None, group=None, **kwargs):
            self.signature = DnaHash(sig)
            self.group = GroupIdentifier('???') if (group is None) else GroupIdentifier(group)
            RunsCollection.__init__(self, members, **kwargs)
...  # The rest of the methods & properties are not yet supported

```

**Group**: A named collection of SequenceAndSignatures that inherits from the **JScribe** Class. This is a collections of runs and associated metadata  
Example:

```python
nucls1 = common.Nucleotides("ATGC")
nucls2 = common.Nucleotides("ATGC")
nucls3 = common.Nucleotides("ATGC")

sqrl1 = common.SequenceAndSignature("Identifier1", nucls1, group="The A Team")
sqrl2 = common.SequenceAndSignature("Identifier2", nucls2, group="The A Team")
sqrl3 = common.SequenceAndSignature("Identifier3", nucls3, group="The A Team")
groups = common.Group(name="The A Team", sqrls=[sqrl1, sqrl2, sqrl3])

print(groups._sqrls)
>>> {('Identifier1',): (('Identifier1',), ('R*%10?aYYjRnEN)_(dH1',), 'ATGC', ('The A Team',)), ('Identifier2',): (('Identifier2',), ('R*%10?aYYjRnEN)_(dH1',), 'ATGC', ('The A Team',)), ('Identifier3',): (('Identifier3',), ('R*%10?aYYjRnEN)_(dH1',), 'ATGC', ('The A Team',))}
```

Note: All sqrl.group (i.e., group="The A Team") must be identice in order to be processed in the same group. This is validated in the **new** method.

**RunsRoster**: a lightweight representation of a Group - contains the set of UniqueRunIDs associated with a named Group.
Example:

```python

class RunsRoster(RunsCollection, JScribe):
    _TYPE = "TOAD.RunsRoster"

    def __init__(self, GroupIdentifier, members=None, **kwargs):
        RunsCollection.__init__(self, members, **kwargs)
        self.GroupIdentifier = GroupIdentifier(GroupIdentifier)

```

---

---

## FASTx.py

**RxFASTA**: Requires a header and dna sequencing for **new**. Splits up the header into various tokens usng the native header.split() method (space splitter). **TODO**: This should be more accepting to other formats.

Here's what's going on:

- RxFASTA takes in header and DNA
  - Header is the defline of a fasta file
  - dna is either a string or a Nucleotide(dna) instance  
    The header gets split into tokens (' ' separated) and the value returns:

```python

(UniqueRunID(OID), header, seq)

```

The difference between UniqueRunID(OID) and header is UniqueRunID is the first space-split string used as the instantiator for UniqueRunID.

**RxFASTQ**: The difference from **RxFASTA** is also requiring quals:

```python

def __new__(cls, header, dna, quals):
        about = FASTQ.parse_header(header)
        OID = about['OID']

        return tuple.__new__(cls, (OID, header, Nucleotides(dna), quals))

```

One unique thing is the parse_header method:

```python

@staticmethod
def parse_header(header):

    info = {}
    header = header[1:]  # Getting rid of the @ sign
    i = header.find(' ')

    if i >= 0:
        runfo = header[:i]
        xtra = header[i+1:]

        info['OID'] = runfo

        run_fields = ['instrument', 'run',
                        'flowcell', 'lane', 'tile', 'x', 'y']
        run_dex = dict(zip(run_fields, runfo.split(':')))

        xtra_fields = ['member', 'filtered', 'control', 'indexseq']
        xtra_dex = dict(zip(xtra_fields, xtra.split(':')))

        info.update(run_dex)
        info.update(xtra_dex)

    else:
        info['ID'] = header

    return info

# Example Header:
@M00649:185:000000000-KKYND:1:1101:15855:1733 1:N:0:GTCGTGAT+TGAACCTT
```

runfo == M00649:185:000000000-KKYND:1:1101:15855:1733  
xtra = 1:N:0:GTCGTGAT+TGAACCTT

```JSON
{
    "OID": "M006....1733",
    "instrument": "M00649",
    "run": 185
}

```

...and so on.

The full return value of the **RxFASTQ** class is:

```python

(OID, header, Nucleotides(dna), quals)
# Example
('M00649:185:000000000-KKYND:1:1101:15855:1733', '@M00649:185:000000000-KKYND:1:1101:15855:1733 1:N:0:GTCGTGAT+TGAACCTT', (('C^Gel37@>3SBXkt5tFE)',), 'GTGTCAGCAGCCGCGGTAATACGTAGGTGGCAAGCGTTATCCGGAATCATTGGGCGTAAAGGGTGCGTAGGTGGCGTACTAAG', None), 'ABBBBFFFFFFBGGGGGGGGGGHHHHGGHGHHHGHGGG2GHHGGGGGGHHHHGHHGGEGHHHGFFFGFEFFFGGHEGGGHHHG')

```
