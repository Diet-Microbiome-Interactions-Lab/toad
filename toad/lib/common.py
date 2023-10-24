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

import Bio

"""
## Notes on types and nomenclature
Nucleotides  - NUCLeotide Sequence/String

DnaHash   - DNA Hash
GroupIdentifier   - Group Identifying Name
UniqueRunID  - Discrete Run ID - uniquely identifies a single run (i.e. entry in a FASTA/FASTQ file); the ID for a SequenceAndSignature

SequenceAndSignature   - Sequence / Run + Labels (DD updates with "entry" as a domain term for the record level content in a fasta/fastq file)

Group  - a named collection of SequenceAndSignatures
RunsRoster - a lightweight representation of a Group - contains the set of UniqueRunIDs associated with a named Group
SignatureAndGroup - a collection of UniqueRunIDs for whom the referant sequences all have the same signature.

carrier - a group containing a given Nucleotides (as determined by the signature of the Nucleotides)

RunsCollection  - abstract base class for collections of UniqueRunIDs
Scurry - abstract base class for collections of SequenceAndSignatures (not yet implemented)

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


class Nucleotides(tuple):
    """
    NUCLeotide Sequence/String
    (pronounced like "knuckles")
    Technically, I can be any sequence of nucleotides OR amino acids.
    (See https://en.wikipedia.org/wiki/FASTA_format#Sequence_representation)
    I am a 2-tuple of the form (signature, sequence), where ...
    * signature is an instance of DnaHash, and ...
    * sequence can be either a string or bytes.

    if sequence is bytes with the first byte being ASCII 'Z', then the sequence should be interpreted as gzsequence (GZIP compressed).
    if sequence is a string, it should be interpreted as the literal nucleotide sequence.
    """
    def __new__(cls, *args):
        if len(args) == 1:
            seq = args[0]

            if isinstance(seq, cls):
                return seq

            if isinstance(seq, str):
                return tuple.__new__(cls, (DnaHash(seq), seq, None))

            if isinstance(seq, Bio.Seq.Seq):
                return tuple.__new__(cls, (DnaHash(str(seq)), str(seq), None))

        if len(args) == 2:
            sig = as_DnaHash(args[0])
            dna = args[1]
            if isinstance(dna, bytes):
                if dna.startswith(b'Z'):
                    zseq = dna
                    seq = None
                else:
                    raise ValueError(
                        "can't interpet Nucleotides value ... is it a gzsequence?")
            elif isinstance(dna, str):
                seq = dna
                zseq = None

            return tuple.__new__(cls, (sig, seq, zseq))

        if len(args) == 3:
            sig = as_DnaHash(args[0])
            seq = args[1]
            zseq = args[2]

            return tuple.__new__(cls, (sig, seq, zseq))

        raise ValueError("Invalid NUCL processing.")

    signature = property(operator.itemgetter(0))

    @staticmethod
    def gzip_str(string_: str) -> bytes:
        return gzip.compress

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


class UniqueRunID(tuple):
    """
    Discrete Run ID
    """
    def __new__(cls, obj):
        if isinstance(obj, UniqueRunID):
            return obj

        if isinstance(obj, SequenceAndSignature):
            return obj.ID

        if isinstance(obj, str):
            return tuple.__new__(cls, (obj,))

    @property
    def ID(self):
        return self

    def __str__(self):
        return self[0]


class GroupIdentifier(tuple):
    """
    Group Identifying Name
    """
    def __new__(cls, obj):
        if isinstance(obj, GroupIdentifier):
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


class DnaHash(tuple):
    """
    Dna hASH
    """
    def __new__(cls, *args, **kwargs):
        if len(args) == 0:
            if 'shakeup' in kwargs:
                return tuple.__new__(cls, (kwargs['shakeup'],))

        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, str):
                return tuple.__new__(cls, (DnaHash.shakeup(arg),))
            if isinstance(arg, cls):
                return arg

        raise ValueError(
            "Do not know how to instantiate DnaHash class with 2+ args")

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


def as_DnaHash(sig):
    """
    I answer a DnaHash instance using sig as a literal DnaHash value.
    """
    return DnaHash(shakeup=sig)


class RunsCollection:
    """
    I am an abstract base class for collection of UniqueRunIDs.
    I can be "frozen" in which I emulate immutability,
    or I can be "thawed" which allows for updates to my members.
    """

    def __init__(self, members=None, **kwargs):
        if members is not None:
            self.frozen = kwargs.get('frozen', True)
            collect = frozenset if self.frozen else set
            print(members)
            self.members = collect([UniqueRunID(member) for member in members])
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
        return (UniqueRunID(obj) in self.members)

    def add(self, member):
        self.members.add(UniqueRunID(member))

    # def clone(self):
    #     """
    #     I answer a frozen copy of myself.
    #     """
    #     return self.__class__.fromJDN(self.toJDN())


class RunsRoster(RunsCollection, JScribe):
    _TYPE = "TOAD.RunsRoster"

    def __init__(self, GroupIdentifier, members=None, **kwargs):
        RunsCollection.__init__(self, members, **kwargs)
        self.GroupIdentifier = GroupIdentifier(GroupIdentifier)

    @property
    def RDN(self):
        return str(self.GroupIdentifier)

    # ----------------------------------------------
    # -- Implement the needed methods from JScribe |
    # ----------------------------------------------
    def _toJDN(self, jdn):
        jdn['GroupIdentifier'] = str(self.RDN)
        jdn['members'] = [str(member) for member in self]
        return jdn

    def _fromJDN(cls, jdn, **kwargs):
        return cls(jdn['GroupIdentifier'], jdn['members'], frozen=kwargs.get('frozen', True))


class SignatureAndGroup(RunsCollection, JScribe):
    _TYPE = "TOAD.SignatureAndGroup"

    def __init__(self, sig, members=None, group=None, **kwargs):
        self.signature = DnaHash(sig)
        self.group = GroupIdentifier('???') if (
            group is None) else GroupIdentifier(group)
        RunsCollection.__init__(self, members, **kwargs)

    @property
    def RDN(self):
        return str(self.signature)

    # ----------------------------------------------
    # -- Implement the needed methods from JScribe |
    # -- Below methods are not yet supported       |
    # ----------------------------------------------
    def _toJDN(self, jdn):
        jdn['signature'] = self.RDN
        jdn['members'] = sorted([str(member) for member in self])
        return jdn

    @classmethod
    def _fromJDN(cls, jdn):
        return cls(jdn['signature'], jdn['members'])


class SequenceAndSignature(tuple):
    "SeQuence + Run Labels"
    def __new__(cls, ID, s, **kwargs):
        if isinstance(s, Nucleotides):
            seq = s.sequence
            sig = s.signature
        elif isinstance(s, DnaHash):
            seq = None
            sig = s
        else:
            raise ValueError

        group = kwargs.get('group', '???')

        return tuple.__new__(cls, (UniqueRunID(ID), sig, seq, GroupIdentifier(group)))

    ID = property(operator.itemgetter(0))
    signature = property(operator.itemgetter(1))
    sequence = property(operator.itemgetter(2))
    group = property(operator.itemgetter(3))

    @property
    def CURIE(self):
        return "[TOAD.SequenceAndSignature:{}]".format(str(self.ID))


class RunsWithMetadata(JScribe):
    """
    I am a collection of runs and associated metadata.
    """
    _TYPE = 'TOAD.Group'

    def __init__(self, name, sqrls=None, **kwargs):
        self.GroupIdentifier = GroupIdentifier(name)
        self._sqrls = {}  # -- a map of {sqrl.ID -> sqrl, ...}
        # -- a map of DnaHash (DNA hash / signature) to an instance of SignatureAndGroup
        self._SignatureAndGroupes = {}

        if sqrls:
            self.extend(sqrls, **kwargs)

    @property
    def RDN(self):
        return str(self.GroupIdentifier)

    @property
    def RunsRoster(self):
        if getattr(self, '_cached_RunsRoster', None) is None:
            self._cached_RunsRoster = RunsRoster(self.GroupIdentifier, self)
        return self._cached_RunsRoster

    def changed(self):
        for cached in ['_cached_SignatureAndGroupes', '_cached_run_IDs', '_cached_RunsRoster', '_cached_hand']:
            if hasattr(self, cached):
                delattr(self, cached)

    def __len__(self):
        return len(self._sqrls)

    def __iter__(self):
        return iter(self._sqrls.values())

    def __getitem__(self, k):
        return self._sqrls[k]

    def __contains__(self, k):
        if isinstance(k, UniqueRunID):
            return (k in self._sqrls)
        if isinstance(k, SequenceAndSignature):
            return (k.ID in self._sqrls)
        if isinstance(k, DnaHash):
            return (k in self.SignatureAndGroupes)
        if isinstance(k, Nucleotides):
            return (DnaHash(k) in self.SignatureAndGroupes)

        raise KeyError(k)

    def runs(self):
        if getattr(self, '_cached_run_IDs', None) is None:
            self._cached_run_IDs = frozenset(self._sqrls.keys())
        return self._cached_run_IDs

    def hand(self):
        """
        I answer the distinct set of Nucleotides in my group as a tuple.
        AKA unique-sequences
        """
        if getattr(self, '_cached_hand', None) is None:
            hand = {}
            for sqrl in self:
                if sqrl.sequence is not None:
                    if sqrl.signature not in hand:
                        hand[sqrl.signature] = Nucleotides(sqrl.sequence)
            self._cached_hand = tuple(hand.values())
        return self._cached_hand

    @property
    def SignatureAndGroupes(self):
        if getattr(self, '_cached_SignatureAndGroupes', None) is None:
            self._cached_SignatureAndGroupes = frozenset(
                self._SignatureAndGroupes.keys())
        return self._cached_SignatureAndGroupes

    def SignatureAndRunsWithMetadata(self, sig):
        sig = DnaHash(sig)
        if sig in self._SignatureAndGroupes:
            return SignatureAndRunsWithMetadata(sig, self._SignatureAndGroupes[sig].members, self.GroupIdentifier)
        else:
            return SignatureAndRunsWithMetadata(sig, [], self.GroupIdentifier)

    def extend(self, sqrls, **kwargs):
        # ---------------------------------------------------------
        # -- Do some validation on the runs that we're given.     |
        # -- Runs without an ID are invalid.                      |
        # -- Runs with embedded group names must match this group |
        # ---------------------------------------------------------
        if not all([(sqrl.ID is not None) for sqrl in sqrls]):
            raise Exception("cannot add an anonymous run to a group")

        if kwargs.get('cross_check', True):
            print(f'Cross_Check is true...')
            print(f'Self.GroupIdentifier == {self.GroupIdentifier}')
            if not all([(sqrl.group == self.GroupIdentifier) for sqrl in sqrls]):
                raise Exception("group <- -> run cross check failed")

        # ------------------------------------------------------------
        # -- Extend the "SignatureAndGroupes" with any ...                      |
        # -- (relatively) new signatures that are in the given sqrls |
        # ------------------------------------------------------------
        sigs = set([sqrl.signature for sqrl in sqrls])
        new_sigs = sigs - set(self._SignatureAndGroupes.keys())
        self._SignatureAndGroupes.update(
            dict([(sig, SignatureAndGroup(sig)) for sig in new_sigs]))

        # -------------------------------------------------
        # -- Add the given sqrls to our internal storage. |
        # -------------------------------------------------
        for sqrl in sqrls:
            # -- Update sqrls
            self._sqrls[sqrl.ID] = sqrl
            # -- Update the SignatureAndGroupes (index of Nucleotides signature to SequenceAndSignatures that have the same signature)
            if sqrl.signature not in self._SignatureAndGroupes:
                self._SignatureAndGroupes[sqrl.signature] = SignatureAndRunsWithMetadata(
                    sqrl.signature)
            self._SignatureAndGroupes[sqrl.signature].add(sqrl.ID)

        # -- call .changed to invalidate any cached data
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

        if sqrl.signature not in self._SignatureAndGroupes:
            self._SignatureAndGroupes[sqrl.signature] = SignatureAndRunsWithMetadata(
                sqrl.signature)
        self._SignatureAndGroupes[sqrl.signature].add(sqrl.ID)

        self.changed()

    def _toJDN(self, jdn, *args, **kwargs):

        section = {}
        for sqrl in self:
            packet = [str(sqrl.signature)]
            if sqrl.sequence is not None:
                packet.append(sqrl.sequence)
            section[str(sqrl.ID)] = packet
        jdn['sqrls'] = section

        if "-Nucleotides" not in args:
            jdn['Nucleotides'] = dict(
                [(str(n.signature), str(n.gzsequence)) for n in self.hand()])

        if "-SignatureAndGroupes" not in args:
            jdn['SignatureAndGroupes'] = {}
            for sig in self.SignatureAndGroupes:
                c = self.SignatureAndRunsWithMetadata(sig)
                jdn['SignatureAndGroupes'][str(c.RDN)] = [
                    str(member) for member in c]

        return jdn

    @classmethod
    def _fromJDN(cls, jdn, **kwargs):
        this = cls(jdn['RDN'])

        sqrls = []
        for k, packet in jdn['sqrls'].items():
            sig = packet[0]
            if len(packet) > 1:
                seq = packet[1]
                sqrl = SequenceAndSignature(
                    k, Nucleotides(seq), group=this.GroupIdentifier)
            else:
                sqrl = SequenceAndSignature(
                    k, as_DnaHash(sig), group=this.GroupIdentifier)
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
