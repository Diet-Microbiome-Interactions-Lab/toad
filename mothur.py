"""
TOAD.mothur

I include some useful helper functions, classes, etc. for working with the external mothur tool.
(see https://mothur.org)
"""
import pathlib
import logging

logger = logging.getLogger(__name__)

class TextInjector:
	def __init__(self, method):
		self.inject = method

	def __lshift__(self, text):
		self.inject(text)

DEBUG = TextInjector(logger.debug)



class Thing:
	pass


class Groupls:
	"""
	I am the files associated with a group.
	"""
	def __init__(self, name):
		self.name = name
		self.files = Thing( )

	@property
	def assets(self):
		collector = [ ]
		for attr in dir(self.files):
			if attr[0] != '_':
				collector.append( getattr(self.files, attr) )
		return tuple(sorted(collector))

	def toJDN(self):
		d = {
			'name': self.name,
			'files': { }
		}

		for attr in dir(self.files):
			if attr[0] != '_':
				d['files'][attr] = getattr(self.files, attr)

		return d


def Cognize(s, pattern, **kwargs):
	"""
	Given a string, s, and a pattern of the form "{varname1}_{}_literal_{varname2}_{}"
	Splits s into tokens and answers a dictionary of the form {'varname1': token1, 'varname2': token2, ...}
	Variables are encapsulated in braces, literals are as-is.
	Token delimeter is assumed to be the single underscore; however, the 'delimiter' kwarg can override this.
	If s is not intelligible to the pattern, then I answer None.
	"""
	sep = kwargs.get('delimiter', '_')
	words = s.split(sep)
	slots = pattern.split(sep)
	if len(slots) == len(words):
		kvs = { }
		for i, word in enumerate(words):
			slot = slots[i]
			if (slot[0] == '{') and (slot[-1] == '}'):
				varname = slot[1:-1]
				if varname:
					kvs[varname] = word
			else:
				if (word != slot):
					return None
		return kvs
	else:
		return None



class MakeFile3:
	def __init__(self, filename):
		self.filename  = filename
		self._groups   = { }
		self._cached   = { }

	def toJDN(self):
		d = { }
		d['groups'] = [ ]
		for group in self.groups:
			d['groups'].append([group.name, group.files.forward, group.files.reverse])
		return d

	@property
	def groups(self):
		if 'groups' not in self._cached:
			self._cached['groups'] = tuple(sorted(self.groups.values( ), key = lambda g: g.name))
		return self._cached['groups']

	def gobble(self, folder, pattern = None, **kwargs):
		"""
		Given a folder, I look for all .fastq and .fastq.gz files in the folder.
		I update my list of triples of the form (group, forward, reverse)
		If pattern is not given, the file name pattern is assumed to be "{group}_{}_{}_{direction}_filtered"
		The file name pattern can also be explicitly set using the simple pattern language or a regex object.
		kwargs can also include ...
		* forward_marker - the literal string to match {direction} for a forward read; defaults to "R1"
		* reverse_marker - the literal string to match {direction} for a reverse read; defaults to "R2"
		"""
		name_pattern   = pattern if (pattern is not None) else "{group}_{}_{}_{direction}_filtered"
		forward_marker = kwargs.get('forward_marker', 'R1')
		reverse_marker = kwargs.get('reverse_marker', 'R2')
		suffixes       = kwargs.get('suffixes', [".fastq", ".fastq.gz"])

		for suffix in suffixes:
			fileq = "*{}".format(suffix)
			DEBUG << "looking for files like {}".format(fileq)
			for path in folder.glob( fileq ):
				DEBUG << "checking file {}".format(path.name)
				lemma = path.name[:-len(suffix)]
				parsed = Cognize(lemma, name_pattern)
				if parsed:
					DEBUG << "file {} successfully parsed as {}".format(path.name, str(parsed))
					group_name     = parsed['group']
					direction_mark = parsed['direction']

					groupls = self._groups.get(group_name, Groupls(group_name))

					if direction_mark == forward_marker:
						groupls.files.forward = path
					if direction_mark == reverse_marker:
						groupls.files.reverse = path

					self._groups[groupls.name] = groupls

					self.changed( )
				else:
					DEBUG << "file {} does not match pattern {}".format(path.name, name_pattern)

		return self

	def changed(self):
		self._cached = { }

	def save(self, filename = None):
		save_filename = self.filename if (filename is None) else filename
		target = pathlib.Path(save_filename)
		with open(target, 'wt') as ostream:
			for group in self.groups:
				ln = "{} {} {}\n".format(group.name, str(group.files.forward), str(group.files.reverse))
				ostream.write(ln)




