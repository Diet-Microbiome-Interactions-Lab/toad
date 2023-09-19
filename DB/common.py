"""
TOAD.DB.common

I hold the common data structures, interfaces, etc. for working with TOAD.DB storage (sub) systems.
"""
class Qi:
	def carriers(self, nucls):
		"""
		I answer a list of group IDs (GrINs) that contain the given nucleic acid sequence.
		nucls can be an instance of any of NUCLs, DASH, or SqRL.
		"""
		raise NotImplementedError("subclass responsibility")

	def group(self, grin):
		"""
		I answer an instance of Group, reconstructed from persistent data stored and associated to the given grin (GrIN)
		"""
		raise NotImplementedError("subclass responsibility")

	def clutches(self, sig, groups_context = None):
		"""
		I answer the list of DRuIDs associated to the given signature. (sig is any of NUCLs|DASH|SqRL).
		If group_context is given, caller should supply a collection of GrINs that should be searched.
		If no group_context is given (the default), ALL groups are searched.
		"""
		raise NotImplementedError("subclass responsibility")

	def NUCLs(self, sig):
		"""
		Given an object with a DASH (DNA signature), I answer the NUCLs object associated with the signature.
		"""
		raise NotImplementedError("subclass responsibility")



class Pi:
	def update(group):
		"""
		Given an instance of TOAD.Group, I update my storage to reflect the group.
		"""
		raise NotImplementedError("subclass responsibility")
