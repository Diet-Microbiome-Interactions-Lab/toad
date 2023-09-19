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

## Mongolia.py
