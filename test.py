'''
Hello
'''
import common

myclass = common.DnaHash("ATGCATGCATGC")
print(myclass)


UniqueRunIDa = common.UniqueRunID("seqA")
UniqueRunIDb = common.UniqueRunID("seqB")

GroupIdentifier1 = common.GroupIdentifier("Group A")
GroupIdentifier2 = common.GroupIdentifier("Group B")
print(GroupIdentifier1)

myRunsCollection = common.RunsCollection()

RunsCollection2 = common.RunsCollection(
    members=[UniqueRunIDa, UniqueRunIDb], frozen=False)
print(RunsCollection2.frozen)
print(RunsCollection2.members)


nucls = common.Nucleotides("ATGCA")
print(nucls)

nucls = common.Nucleotides("aalksa", "ATGC", b'akx')
print(nucls)
print(nucls[0])
print(nucls[1])
print(nucls[2])

nucls1 = common.Nucleotides("ATGC")
nucls2 = common.Nucleotides("ATGC")
nucls3 = common.Nucleotides("ATGC")

sqrl1 = common.SequenceAndSignature("Identifier1", nucls1, group="The A Team")
sqrl2 = common.SequenceAndSignature("Identifier2", nucls2, group="The A Team")
sqrl3 = common.SequenceAndSignature("Identifier3", nucls3, group="The A Team")
groups = common.RunsWithMetadata(
    name="The A Team", sqrls=[sqrl1, sqrl2, sqrl3])

print(groups._sqrls)
