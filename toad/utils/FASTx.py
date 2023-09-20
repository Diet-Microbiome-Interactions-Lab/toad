"""
FASTx.py

I am a library for working with FASTA and FASTQ files.
"""
import base64
import hashlib
import operator
import pathlib

import common as cx

from Bio.SeqIO.FastaIO import SimpleFastaParser

SIGSIZE = 16


class RxFASTA(tuple):
    """
    I am a FASTA record instance.
    """
    def __new__(cls, header, dna):
        seq = Nucleotides(dna)

        tokens = header.split()
        OID = tokens[0]

        return tuple.__new__(cls, (UniqueRunID(OID), header, seq))

    ID = property(operator.itemgetter(0))
    header = property(operator.itemgetter(1))
    sequence = property(operator.itemgetter(2))

    def toSequenceAndSignature(self, **kwargs):
        return SequenceAndSignature(self.ID, self.sequence, **kwargs)

    @property
    def signature(self):
        return self.DnaHash

    @property
    def DnaHash(self):
        if getattr(self, '_DnaHash', None) is None:
            self._DnaHash = DnaHash(self.sequence)
        return self._DnaHash

    @classmethod
    def read_from(cls, fin):

        header = None
        seqlns = []

        state = 'SKIPPING'
        while state != 'DONE':
            fmark = fin.tell()
            txtln = fin.readline()

            if txtln:
                txtln = txtln.strip()

                if state == 'SKIPPING':
                    if txtln[0] == '>':
                        header = txtln[1:]  # Strips the '>' from the header
                        nxtstate = 'SEQUENCE'

                elif state == 'SEQUENCE':
                    if txtln[0] == '>':
                        fin.seek(fmark)
                        nxtstate = 'DONE'
                    else:
                        seqlns.append(txtln)
            else:
                nxtstate = 'DONE'

            state = nxtstate

        if header and seqlns:
            return cls(header, ''.join(seqlns))
        else:
            return None


class RxFASTQ(tuple):
    """
    I am a FASTQ record instance.
    """
    def __new__(cls, header, dna, quals):
        about = RxFASTQ.parse_header(header)
        OID = about['OID']

        return tuple.__new__(cls, (OID, header, Nucleotides(dna), quals))

    ID = property(operator.itemgetter(0))
    header = property(operator.itemgetter(1))
    sequence = property(operator.itemgetter(2))
    quality = property(operator.itemgetter(3))

    @property
    def to_mongo(self):
        data = {
            "mongo_collection": "Fastqs",
            "type_": "Fastq",
            "header": self.header,
            "dna": self.sequence,
            "quality": self.quality
        }
        return data

    @property
    def DnaHash(self):
        return self.sequence.DnaHash

    @property
    def signature(self):
        return self.sequence.DnaHash

    @property
    def instrument(self):
        return self.meta['instrument']

    @property
    def run(self):
        return self.meta['run']

    @property
    def meta(self):
        return DONNA.parse_header(self.header)

    def to_stanza(self):
        return "{}\n{}\n+\n{}\n".format(self.header, self.sequence, self.quality)

    @staticmethod
    def parse_header(header, default=True):

        info = {}

        if not default:
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

    @classmethod
    def read_from(cls, fin):
        """
        Given a file object (fin), I read from the file and answer either...
        a new instance of cls, or None (if the file ended ).
        """
        # -- read four lines from the text file and strip the trailing newline characters.
        stanza = [fin.readline().strip() for i in range(4)]
        if all(stanza):
            # -- build a new instance of my class only if all 4 lines are non-empty.
            return cls.from_lines(stanza)
        else:
            return None

    @classmethod
    def from_stanza(cls, text):
        return cls.from_lines(text.split('\n'))

    @classmethod
    def from_lines(cls, lines):
        if len(lines) >= 4:
            header = lines[0].strip()
            sequence = lines[1].strip()
            comment = lines[2].strip()
            quals = lines[3].strip()
            if all([len(ln) > 0 for ln in [header, sequence, comment, quals]]):
                return cls(header, sequence, quals)
            else:
                raise ValueError
