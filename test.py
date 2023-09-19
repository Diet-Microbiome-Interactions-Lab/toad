'''
Hello
'''
import common

myclass = common.DASH("ATGCATGCATGC")
print(myclass)


druida = common.DRuID("seqA")
druidb = common.DRuID("seqB")

grin1 = common.GrIN("Group A")
grin2 = common.GrIN("Group B")
print(grin1)

mygrove = common.Grove()

grove2 = common.Grove(members=[druida, druidb], frozen=False)
print(grove2.frozen)
print(grove2.members)


nucls = common.NUCLS("ATGCA")
print(nucls)

nucls = common.NUCLS("aalksa", "ATGC", b'akx')
print(nucls)
print(nucls[0])
print(nucls[1])
print(nucls[2])