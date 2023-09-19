"""
TOAD.py

I work on sqlite3 databases that hold DNA contig strings.
"""
import sqlite3
import gzip
import hashlib
import base64
import operator
import json

"""
## Notes on types and nomenclature
NUCLS  - NUCLeotide Sequence/String

DASH   - DNA Hash
GrIN   - Group Identifying Name
DRuID  - Discrete Run ID - uniquely identifies a single run (i.e. entry in a FASTA/FASTQ file); the ID for a SqRL

SqRL   - Sequence / Run + Labels (DD updates with "entry" as a domain term for the record level content in a fasta/fastq file)

Group  - a named collection of SqRLs
Roster - a lightweight representation of a Group - contains the set of DRuIDs associated with a named Group
Clutch - a collection of DRuIDs for whom the referant sequences all have the same signature.

carrier - a group containing a given NUCLS (as determined by the signature of the NUCLS)

Grove  - abstract base class for collections of DRuIDs
Scurry - abstract base class for collections of SqRLs (not yet implemented)

## Other notes...
JDN - "Javascript Dictionary Normalized" - pronounced "JAY-DEN" is a python dictionary with values that are primitive enough to be directly serialized to JSON.
RDN - Relatively Distinguishing Name - a local ID (NOT a GUID) that is unique relative to other instances of the same class.
"""


class JScribe:
    """
    I am a base class for implementing JDN/JSON serialization / deserialization.
    """
    __slots__ = tuple()

    @property
    def RDN(self):
        """
        I answer a Relative Distinguishing Name ... in this case an object ID that 
        is unique with respect to my type, but may not be globally unique.
        """
        raise NotImplementedError("RDN is subclass responsibility")

    @property
    def CURIE(self):
        return "[{}:{}]".format(self._TYPE, self.RDN)

    def toJDN(self, *args, **kwargs):
        """
        I format myself as a dictionary of (relatively) primitive types.
        """
        jdn = {
            "_type": self._TYPE,
            "_id":   self.CURIE,
            "RDN":   str(self.RDN)
        }
        return self._toJDN(jdn, *args, **kwargs)

    def _toJDN(self, jdn=None, *args, **kwargs):
        """
        I construct a JDN representation of my contents.
        If I am given an existing dictionary, I add my content to it; 
        otherwise, I create a new dictionary.
        """
        raise NotImplementedError("_toJDN is subclass responsibility")

    def toJSON(self, *args, **kwargs):
        """
        I answer a string that encodes my contents in JSON.
        """
        return json.dumps(self.toJDN(*args, **kwargs), sort_keys=True, indent=3)

    @classmethod
    def fromJSON(cls, jdoc, **kwargs):
        """
        I build an instance of my class from the given JSON document.
        """
        return cls.fromJDN(json.loads(jdoc), **kwargs)

    @classmethod
    def fromJDN(cls, jdn, **kwargs):
        """
        I build an instance of my class from the given JDN (Javascript Dictionary - Normalized).
        """
        if '_type' in jdn:
            if jdn['_type'] != cls._TYPE:
                raise ValueError("JDN of type {} is not compatible with {}".format(
                    jdn['_type'], cls._TYPE))

        return cls._fromJDN(jdn, **kwargs)

    @classmethod
    def _fromJDN(cls, jdn, **kwargs):
        raise NotImplementedError("_fromJDN is subclass responsibility")


class NUCLS(tuple):
    """
    NUCLeotide Sequence/String
    (pronounced like "knuckles")
    Technically, I can be any sequence of nucleotides OR amino acids.
    (See https://en.wikipedia.org/wiki/FASTA_format#Sequence_representation)
    I am a 2-tuple of the form (signature, sequence), where ...
    * signature is an instance of DASH, and ...
    * sequence can be either a string or bytes.

    if sequence is bytes with the first byte being ASCII 'Z', then the sequence should be interpreted as gzsequence (GZIP compressed).
    if sequence is a string, it should be interpreted as the literal nucleotide sequence.
    """
    def __new__(cls, *args):
        if len(args) == 1:
            seq = args[0]
            print(f'Len of args is 1 and seq={seq}')

            if isinstance(seq, cls):
                return seq

            if isinstance(seq, str):
                return tuple.__new__(cls, (DASH(seq), seq, None))

        if len(args) == 2:
            sig = asDASH(args[0])
            dna = args[1]
            if isinstance(dna, bytes):
                if dna.startswith(b'Z'):
                    zseq = dna
                    seq = None
                else:
                    raise ValueError(
                        "can't interpet NUCLS value ... is it a gzsequence?")
            elif isinstance(dna, str):
                seq = dna
                zseq = None

            return tuple.__new__(cls, (sig, seq, zseq))

        if len(args) == 3:
            sig = asDASH(args[0])
            seq = args[1]
            zseq = args[2]

            return tuple.__new__(cls, (sig, seq, zseq))

        raise ValueError("Invalid NUCL processing.")

    signature = property(operator.itemgetter(0))

    @property
    def length(self):
        return len(self.sequence)

    @property
    def sequence(self):
        if self[1] is not None:
            return self[1]
        else:
            if getattr(self, '_sequence', None) is None:
                self._sequence = gzip.decompress(self[2][1:]).decode('utf-8')
            return self._sequence

    @property
    def gzsequence(self):
        if self[2] is not None:
            return self[2]
        else:
            if getattr(self, '_gzsequence', None) is None:
                self._gzsequence = b'Z' + \
                    gzip.compress(self.sequence.encode('utf-8'))
            return self._gzsequence

    def __str__(self):
        return self.sequence


class DRuID(tuple):
    """
    Discrete Run ID
    """
    def __new__(cls, obj):
        if isinstance(obj, DRuID):
            return obj

        if isinstance(obj, SqRL):
            return obj.ID

        if isinstance(obj, str):
            return tuple.__new__(cls, (obj,))

    @property
    def ID(self):
        return self

    def __str__(self):
        return self[0]


class GrIN(tuple):
    """
    Group Identifying Name
    """
    def __new__(cls, obj):
        if isinstance(obj, GrIN):
            return obj
        if isinstance(obj, str):
            return tuple.__new__(cls, (obj.strip(),))
        if isinstance(obj, Group):
            return obj.ID

    @property
    def ID(self):
        return self

    def __str__(self):
        return self[0]

    def CURIE(self):
        raise NotImplementedError


class DASH(tuple):
    """
    Dna hASH
    """
    def __new__(cls, *args, **kwargs):
        if len(args) == 0:
            if 'shakeup' in kwargs:
                print(f'Shakeup is in DASH, returning value')
                return tuple.__new__(cls, (kwargs['shakeup'],))

        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, str):
                return tuple.__new__(cls, (DASH.shakeup(arg),))
            if isinstance(arg, cls):
                return arg

        raise ValueError("Do not know how to instantiate DASH class with 2+ args")

    @staticmethod
    def shakeup(dna):
        """
        I answer a base85 encoded SHAKE128 128 bit hash of a given (R|D)NA sequence.
        Here, the (R|D)NA sequence is a simple string of base-pair letters, e.g. GATTACA
        """
        if isinstance(dna, str):
            dnas = str(dna)
        return base64.b85encode(hashlib.shake_128(dnas.encode('utf-8')).digest(16)).decode('utf-8')

    def __str__(self):
        return self[0]


def asDASH(sig):
    """
    I answer a DASH instance using sig as a literal DASH value.
    """
    return DASH(shakeup=sig)


class Grove:
    """
    I am an abstract base class for collection of DRuIDs.
    I can be "frozen" in which I emulate immutability,
    or I can be "thawed" which allows for updates to my members.
    """

    def __init__(self, members=None, **kwargs):
        if members is not None:
            self.frozen = kwargs.get('frozen', True)
            collect = frozenset if self.frozen else set
            print(members)
            self.members = collect([DRuID(member) for member in members])
        else:
            self.frozen = kwargs.get('frozen', False)
            self.members = set()

    @property
    def is_empty(self):
        return (len(self.members) == 0)

    def thaw(self):
        if self.frozen:
            self.members = set(self.members)
            self.frozen = True

    def __iter__(self):
        return iter(self.members)

    def __len__(self):
        return len(self.members)

    def __contains__(self, obj):
        return (DRuID(obj) in self.members)

    def add(self, member):
        self.members.add(DRuID(member))

    # def clone(self):
    #     """
    #     I answer a frozen copy of myself.
    #     """
    #     return self.__class__.fromJDN(self.toJDN())


class Roster(Grove, JScribe):
    _TYPE = "TOAD.Roster"

    def __init__(self, grin, members=None, **kwargs):
        Grove.__init__(self, members, **kwargs)
        self.grin = GrIN(grin)

    @property
    def RDN(self):
        return str(self.grin)

    #----------------------------------------------
    #-- Implement the needed methods from JScribe |
    #----------------------------------------------
    def _toJDN(self, jdn):
        jdn['grin'] = str(self.RDN)
        jdn['members'] = [str(member) for member in self]
        return jdn

    def _fromJDN(cls, jdn, **kwargs):
        return cls(jdn['grin'], jdn['members'], frozen=kwargs.get('frozen', True))


class Clutch(Grove, JScribe):
    _TYPE = "TOAD.Clutch"

    def __init__(self, sig, members=None, group=None, **kwargs):
        self.signature = DASH(sig)
        self.group = GrIN('???') if (group is None) else GrIN(group)
        Grove.__init__(self, members, **kwargs)

    @property
    def RDN(self):
        return str(self.signature)

    #----------------------------------------------
    #-- Implement the needed methods from JScribe |
    #----------------------------------------------
    def _toJDN(self, jdn):
        jdn['signature'] = self.RDN
        jdn['members'] = sorted([str(member) for member in self])
        return jdn

    @classmethod
    def _fromJDN(cls, jdn):
        return cls(jdn['signature'], jdn['members'])


class SqRL(tuple):
    "SeQuence + Run Labels"
    def __new__(cls, ID, s, **kwargs):
        if isinstance(s, NUCLS):
            seq = s.sequence
            sig = s.signature
        elif isinstance(s, DASH):
            seq = None
            sig = s
        else:
            raise ValueError

        group = kwargs.get('group', '???')

        return tuple.__new__(cls, (DRuID(ID), sig, seq, GrIN(group)))

    ID = property(operator.itemgetter(0))
    signature = property(operator.itemgetter(1))
    sequence = property(operator.itemgetter(2))
    group = property(operator.itemgetter(3))

    @property
    def CURIE(self):
        return "[TOAD.SqRL:{}]".format(str(self.ID))


class Group(JScribe):
    """
    I am a collection of runs and associated metadata.
    """
    _TYPE = 'TOAD.Group'

    def __init__(self, name, sqrls=None, **kwargs):
        self.grin = GrIN(name)
        self._sqrls = {}  # -- a map of {sqrl.ID -> sqrl, ...}
        # -- a map of DASH (DNA hash / signature) to an instance of Clutch
        self._clutches = {}

        if sqrls:
            self.extend(sqrls, **kwargs)

    @property
    def RDN(self):
        return str(self.grin)

    @property
    def roster(self):
        if getattr(self, '_cached_roster', None) is None:
            self._cached_roster = Roster(self.grin, self)
        return self._cached_roster

    def changed(self):
        for cached in ['_cached_clutches', '_cached_run_IDs', '_cached_roster', '_cached_hand']:
            if hasattr(self, cached):
                delattr(self, cached)

    def __len__(self):
        return len(self._sqrls)

    def __iter__(self):
        return iter(self._sqrls.values())

    def __getitem__(self, k):
        return self._sqrls[k]

    def __contains__(self, k):
        if isinstance(k, DRuID):
            return (k in self._sqrls)
        if isinstance(k, SqRL):
            return (k.ID in self._sqrls)
        if isinstance(k, DASH):
            return (k in self.clutches)
        if isinstance(k, NUCLs):
            return (DASH(k) in self.clutches)

        raise KeyError(k)

    def runs(self):
        if getattr(self, '_cached_run_IDs', None) is None:
            self._cached_run_IDs = frozenset(self._sqrls.keys())
        return self._cached_run_IDs

    def hand(self):
        """
        I answer the distinct set of NUCLS in my group as a tuple.
        AKA unique-sequences
        """
        if getattr(self, '_cached_hand', None) is None:
            hand = {}
            for sqrl in self:
                if sqrl.sequence is not None:
                    if sqrl.signature not in hand:
                        hand[sqrl.signature] = NUCLS(sqrl.sequence)
            self._cached_hand = tuple(hand.values())
        return self._cached_hand

    @property
    def clutches(self):
        if getattr(self, '_cached_clutches', None) is None:
            self._cached_clutches = frozenset(self._clutches.keys())
        return self._cached_clutches

    def clutch(self, sig):
        sig = DASH(sig)
        if sig in self._clutches:
            return Clutch(sig, self._clutches[sig].members, self.grin)
        else:
            return Clutch(sig, [], self.grin)

    def extend(self, sqrls, **kwargs):
        #---------------------------------------------------------
        #-- Do some validation on the runs that we're given.     |
        #-- Runs without an ID are invalid.                      |
        #-- Runs with embedded group names must match this group |
        #---------------------------------------------------------
        if not all([(sqrl.ID is not None) for sqrl in sqrls]):
            raise Exception("cannot add an anonymous run to a group")

        if kwargs.get('cross_check', True):
            if not all([(sqrl.group == self.grin) for sqrl in sqrls]):
                raise Exception("group <- -> run cross check failed")

        #------------------------------------------------------------
        #-- Extend the "clutches" with any ...                      |
        #-- (relatively) new signatures that are in the given sqrls |
        #------------------------------------------------------------
        sigs = set([sqrl.signature for sqrl in sqrls])
        new_sigs = sigs - set(self._clutches.keys())
        self._clutches.update(dict([(sig, Clutch(sig)) for sig in new_sigs]))

        #-------------------------------------------------
        #-- Add the given sqrls to our internal storage. |
        #-------------------------------------------------
        for sqrl in sqrls:
            #-- Update sqrls
            self._sqrls[sqrl.ID] = sqrl
            #-- Update the clutches (index of NUCLS signature to SqRLs that have the same signature)
            if sqrl.signature not in self._clutches:
                self._clutches[sqrl.signature] = Clutch(sqrl.signature)
            self._clutches[sqrl.signature].add(sqrl.ID)

        #-- call .changed to invalidate any cached data
        self.changed()

    def add(self, sqrl, **kwargs):
        """
        I add the given sqrl to my group.
        I do some consistency checking, just to be sure.
        If you want to add lots of sqrls, use the .extend method, instead - it's more efficient for collections.
        """
        if sqrl.ID is None:
            raise Exception("cannot add an anonymous run to a group")

        if kwargs.get('cross_check', True):
            if (sqrl.group != self.name):
                raise Exception("group <- -> run cross check failed")

        self._sqrls[sqrl.ID] = sqrl

        if sqrl.signature not in self._clutches:
            self._clutches[sqrl.signature] = Clutch(sqrl.signature)
        self._clutches[sqrl.signature].add(sqrl.ID)

        self.changed()

    def _toJDN(self, jdn, *args, **kwargs):

        section = {}
        for sqrl in self:
            packet = [str(sqrl.signature)]
            if sqrl.sequence is not None:
                packet.append(sqrl.sequence)
            section[str(sqrl.ID)] = packet
        jdn['sqrls'] = section

        if "-nucls" not in args:
            jdn['nucls'] = dict(
                [(str(n.signature), str(n.gzsequence)) for n in self.hand()])

        if "-clutches" not in args:
            jdn['clutches'] = {}
            for sig in self.clutches:
                c = self.clutch(sig)
                jdn['clutches'][str(c.RDN)] = [str(member) for member in c]

        return jdn

    @classmethod
    def _fromJDN(cls, jdn, **kwargs):
        this = cls(jdn['RDN'])

        sqrls = []
        for k, packet in jdn['sqrls'].items():
            sig = packet[0]
            if len(packet) > 1:
                seq = packet[1]
                sqrl = SqRL(k, NUCLS(seq), group=this.grin)
            else:
                sqrl = SqRL(k, asDASH(sig), group=this.grin)
            sqrls.append(sqrl)

        this.extend(sqrls)

        return this

    def save_as(self, dst):
        with open(dst, 'wt') as ostream:
            json.dump(self.toJDN(), ostream, sort_keys=True, indent=3)

    @classmethod
    def loaded_from(cls, src_path, **kwargs):
        with open(src_path, 'rt') as istream:
            jdn = json.load(istream)
            return cls.fromJDN(jdn, **kwargs)


# class OLD_Contigalog:
    # def __init__(self, db):
        # """
        # I implement that catalog in a given sqlite3 connection.
        # """
        # self.db = db
        # self.install( )

    # def install(self):
        # c = self.db.cursor( )
        # c.execute("CREATE TABLE IF NOT EXISTS contigalog (run TEXT PRIMARY KEY, signature TEXT, group TEXT, gzsequence BLOB, note TEXT)")
        # c.execute("CREATE INDEX IF NOT EXISTS contigalog_groups ON contigalog (group)")
        # c.execute("CREATE INDEX IF NOT EXISTS contigalog_sigs ON contigalog (signature)")

    # def census(self):
        # """
        # I answer a dictionary of {sig: [run, ...]}
        # """
        # census = { }
        # c = self.db.cursor( )
        # c.execute("SELECT run, signature FROM contigalog")
        # for row in c:
            # run, sig = row
            # if sig not in census:
            # census[sig] = [ ]
            # census[sig].append(run)
        # return census

    # def __getitem__(self, run):
        # c = self.db.cursor( )
        # c.execute("SELECT * FROM contigalog WHERE run = ?", (run,))
        # rows = c.fetchall( )
        # if rows:
            # return GATTACA(*rows[0])
        # else:
            # raise KeyError(run)

    # def add(self, duhna):
        # """
        # Given duhna (a reference to the movie Zootopia) as an instance of GATTACA,
        # I add the given instance to the contigalog.
        # """
        # c = self.db.cursor( )
        # c.execute("INSERT INTO contigalog (run, signature, group, gzsequence) VALUES (?, ?, ?, ?)", duhna)

    # def groups(self):
        # """
        # I answer the set of distinct group names that are seen in the contigalog.
        # """
        # c = self.db.cursor( )
        # c.execute("SELECT DISTINCT group FROM contigalog")
        # return set([row[0] for row in c])

    # def members(self, group):
        # """
        # Given a group, I answer a collection of runs that are part of the given group.
        # """
        # c = self.db.cursor( )
        # c.execute("SELECT run FROM contigalog WHERE group = ?", (group,))
        # return set([row[0] for row in c])

    # def sames(self, target, **kwargs):
        # """
        # Given a target as one of...
        # * a literal DNA sequence string, or ...
        # * a GATTACA instance.
        # I answer the set of runs that have the same signature as the given target.
        # """
        # if isinstance(target, GATTACA):
            # return self.sames(signature = target.signature)
        # elif isinstance(target, str):
            # #-- Interpret this as a literal DNA sequence string.
            # sig = GATTACA.shakeup(target)
            # return self.members(sig)

    # def tenants(self, spec):
        # """
        # I answer the set of groups that contain the given specimen sequence.
        # spec can be either a DNA string or an instance of GATTACA.
        # """
        # raise NotImplementedError
