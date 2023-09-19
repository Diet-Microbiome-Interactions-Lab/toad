"""
TOAD.DB.common

I hold the common data structures, interfaces, etc. for working with TOAD.DB storage (sub) systems.
"""


class Qi:
    def carriers(self, Nucleotides):
        """
        I answer a list of group IDs (RunsWithMetadataIdentifiers) that contain the given nucleic acid sequence.
        Nucleotides can be an instance of any of Nucleotides, DnaHash, or SequenceAndSignature.
        """
        raise NotImplementedError("subclass responsibility")

    def group(self, RunsWithMetadataIdentifier):
        """
        I answer an instance of RunsWithMetadata, reconstructed from persistent data stored and associated to the given RunsWithMetadataIdentifier (RunsWithMetadataIdentifier)
        """
        raise NotImplementedError("subclass responsibility")

    def SignatureAndRunsWithMetadataes(self, sig, groups_context=None):
        """
        I answer the list of UniqueRunIDs associated to the given signature. (sig is any of Nucleotides|DnaHash|SequenceAndSignature).
        If group_context is given, caller should supply a collection of RunsWithMetadataIdentifiers that should be searched.
        If no group_context is given (the default), ALL groups are searched.
        """
        raise NotImplementedError("subclass responsibility")

    def Nucleotides(self, sig):
        """
        Given an object with a DnaHash (DNA signature), I answer the Nucleotides object associated with the signature.
        """
        raise NotImplementedError("subclass responsibility")


class Pi:
    def update(group):
        """
        Given an instance of TOAD.RunsWithMetadata, I update my storage to reflect the group.
        """
        raise NotImplementedError("subclass responsibility")
