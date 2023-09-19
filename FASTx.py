"""
FASTx.py

I am a library for working with FASTA and FASTQ files.
"""
import operator
import pathlib
import base64
import hashlib

SIGSIZE = 16

from .common import *


class RxFASTA(tuple):
	"""
	I am a FASTA record instance.
	"""
	def __new__(cls, header, dna):
		seq = NUCLS(dna)

		tokens = header.split( )
		OID    = tokens[0]

		return tuple.__new__(cls, (DRuID(OID), header, seq))

	ID        = property(operator.itemgetter(0))
	header    = property(operator.itemgetter(1))
	sequence  = property(operator.itemgetter(2))

	def toSqRL(self, **kwargs):
		return SqRL(self.ID, self.sequence, **kwargs)

	@property
	def signature(self):
		return self.DASH

	@property
	def DASH(self):
		if getattr(self, '_DASH', None) is None:
			self._DASH = DASH(self.sequence)
		return self._DASH

	@classmethod
	def read_from(cls, fin):

		header = None
		seqlns = [ ]

		state   = 'SKIPPING'
		while state != 'DONE':
			fmark   = fin.tell( )
			txtln   = fin.readline( )

			if txtln:
				txtln = txtln.strip( )

				if state == 'SKIPPING':
					if txtln[0] == '>':
						header = txtln[1:]
						nxtstate = 'SEQUENCE'

				elif state == 'SEQUENCE':
					if txtln[0] == '>':
						fin.seek(fmark)
						nxtstate = 'DONE'
					else:
						seqlns.append ( txtln )
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
		about     = FASTQ.parse_header(header)
		OID       = about['OID']
		
		return tuple.__new__(cls, (OID, header, NUCLS(dna), quals))

	ID        = property(operator.itemgetter(0))
	header    = property(operator.itemgetter(1))
	sequence  = property(operator.itemgetter(2))
	quality   = property(operator.itemgetter(3))

	@property
	def DASH(self):
		return self.sequence.DASH

	@property
	def signature(self):
		return self.sequence.DASH

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
	def parse_header(header):

		info = { }
		header = header[1:]
		i = header.find(' ')

		if i >= 0:
			runfo = header[:i]
			xtra  = header[i+1:]
			
			info['OID']     = runfo
			
			run_fields = ['instrument', 'run', 'flowcell', 'lane', 'tile', 'x', 'y']
			run_dex = dict( zip(run_fields, runfo.split(':')) )

			xtra_fields = ['member', 'filtered', 'control', 'indexseq']
			xtra_dex = dict( zip(xtra_fields, xtra.split(':')) )

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
		#-- read four lines from the text file and strip the trailing newline characters.
		stanza = [fin.readline( ).strip( ) for i in range(4)]
		if all(stanza):
			#-- build a new instance of my class only if all 4 lines are non-empty.
			return cls.from_lines( stanza )
		else:
			return None

	@classmethod
	def from_stanza(cls, text):
		return cls.from_lines( text.split('\n') )

	@classmethod
	def from_lines(cls, lines):
		if len(lines) >= 4:
			header   = lines[0].strip( )
			sequence = lines[1].strip( )
			comment  = lines[2].strip( )
			quals    = lines[3].strip( )
			if all([len(ln) > 0 for ln in [header, sequence, comment, quals]]):
				return cls(header, sequence, quals)
			else:
				raise ValueError


class Reader:
	def __init__(self, istream, rxcls):
		"""
		I am a FASTx reader that iterates over FASTA or FASTQ files.
		I should be constructed as ...
		Reader( f, RxFASTA )
		Reader( f, RxFASTQ )
		...or using my class methods like ...
		Reader.FASTA( f )
		Reader.FASTQ( f )
		"""
		self.istream = istream
		self.rxcls   = rxcls

	def __iter__(self):
		return self

	def __next__(self):
		obj = self.rxcls.read_from(self.istream)
		if obj:
			return obj
		else:
			raise StopIteration

	def close(self):
		self.istream.close( )

	@classmethod
	def FASTA(cls, fp):
		return cls(fp, RxFASTA)

	@classmethod
	def FASTQ(cls, fp):
		return cls(fp, RxFASTQ)

	@classmethod
	def open(cls, path, fformat = None):
		path = pathlib.Path(path)

		fformat = fformat.lower( ) if (fformat is not None) else path.suffix

		loaders = {
			'fasta': RxFASTA,
			'fastq': RxFASTQ,
			'.fasta': RxFASTA,
			'.fastq': RxFASTQ
		}

		if fformat in loaders:
			rxcls = loaders[fformat]
		else:
			raise ValueError("file {} has unknown format '{}'".format(str(path), fformat))

		src = open(path, 'rt')
		return cls(src, rxcls)



TESTFILE = '/depot/agdata/data/users/ndenny/microbiome/stability.trim.contigs.fasta'
