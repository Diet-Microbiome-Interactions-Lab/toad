"""
TOAD.DB.sqlite

I am the sqlite storage subsystem.
Each project (which can have multiple groups associated) is a single sqlite file.
"""
import sqlite3
import logging

from TOAD.common import *
import TOAD.DB.common

logger = logging.getLogger(__name__)


class axsNucleotides:
    def __init__(self, pi):
        self.pi = pi

    def __getitem__(self, k):
        if isinstance(k, DnaHash):
            c = self.pi.execute(
                "SELECT * FROM axs WHERE DnaHash = ?", (str(k),))
            r = c.fetchone()
            if r is not None:
                return axs(r['DnaHash'], r['gzsequence'])
            else:
                raise KeyError(k)

    def __contains__(self, k):
        return self.pi.exists('axs', 'DnaHash', str(k))

    def __len__(self):
        c = self.pi.execute("SELECT COUNT(*) AS tallied from axs")
        r = c.fetchone()
        return r['tallied']

    def keys(self):
        c = self.pi.execute("SELECT DnaHash FROM axs")
        return [enDnaHash(r['DnaHash']) for r in c]

    def __iter__(self):
        for k in self.keys():
            yield self[as_DnaHash(k)]


class axsRunsWithMetadatas:
    def __init__(self, pi):
        self.pi = pi

    def keys(self):
        c = self.pi.execute(
            "SELECT RunsWithMetadataIdentifier FROM groups ORDER BY RunsWithMetadataIdentifier")
        return [RunsWithMetadataIdentifier(r['RunsWithMetadataIdentifier']) for r in c]

    def __len__(self):
        c = self.pi.execute("SELECT COUNT(*) AS tallied FROM groups")
        r = c.fetchone()
        return r['tallied']

    def __contains__(self, RunsWithMetadataIdentifier):
        return self.pi.exists('groups', 'RunsWithMetadataIdentifier', str(RunsWithMetadataIdentifier))

    def __getitem__(self, RunsWithMetadataIdentifier):
        c = self.pi.execute(
            "SELECT RunsWithMetadataIdentifier, sqrls FROM groups WHERE RunsWithMetadataIdentifier = ?", (str(RunsWithMetadataIdentifier),))
        r = c.fetchone()
        if r is None:
            raise KeyError(str(RunsWithMetadataIdentifier))
        else:
            g = RunsWithMetadata.fromJSON(r['sqrls'])
            return g

    def __iter__(self):
        for k in self.keys():
            yield self[k]


class Pi(TOAD.DB.common.Pi):
    def __init__(self, db_path):
        logger.debug("opening db at {}".format(db_path))
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.provision()

        # -----------------------------
        # -- Some special accessors...|
        # -----------------------------
        self.axs = axsaxs(self)
        self.groups = axsRunsWithMetadatas(self)

    def execute(self, query, quargs=None):
        c = self.db.cursor()
        if quargs:
            return c.execute(query, quargs)
        else:
            return c.execute(query)

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.close()

    def provision(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS Nucleotides   (DnaHash  TEXT PRIMARY KEY, gzsequence BLOB)")
# self.db.execute("CREATE TABLE IF NOT EXISTS sqrls   (UniqueRunID TEXT PRIMARY KEY, RunsWithMetadataIdentifier TEXT, sig TEXT)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS groups  (RunsWithMetadataIdentifier  TEXT PRIMARY KEY, sqrls BLOB)")

        self.db.execute(
            "CREATE TABLE IF NOT EXISTS SignatureAndRunsWithMetadataes(DnaHash TEXT, RunsWithMetadataIdentifier TEXT, members BLOB)")
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS SignatureAndRunsWithMetadataes_DnaHashes ON SignatureAndRunsWithMetadataes(DnaHash)")
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS SignatureAndRunsWithMetadataes_RunsWithMetadataIdentifiers ON SignatureAndRunsWithMetadataes(RunsWithMetadataIdentifier)")

# self.db.execute("CREATE TABLE IF NOT EXISTS carriers(DnaHash TEXT, RunsWithMetadataIdentifiers BLOB)")
# self.db.execute("CREATE INDEX IF NOT EXISTS carriers_DnaHashes ON carriers(DnaHash)")

    def find_one(self, tbl, k, v):
        """
        Answers a single row from the given table (tbl) where column (k) has value (v).
        If no such row exists, I answer None.
        """
        c = self.execute(
            "SELECT {} FROM {} WHERE ({} = ?) LIMIT 1".format(tbl, k, v), v)
        return c.fetchone()

    def exists(self, tbl, k, v):
        """
        Performs a simple existence query that table (tbl) has at least one row where column (k) has value (v).
        """
        r = self.lookup(tbl, k, v)
        if r is not None:
            return True
        else:
            return False

    def carriers(self, DnaHash):
        """
        I answer the set of all groups that have at least one instance of the given Nucleotides.
        """
        c = self.execute(
            "SELECT RunsWithMetadataIdentifier FROM SignatureAndRunsWithMetadataes WHERE (DnaHash = ?)", (str(DnaHash),))
        return [RunsWithMetadataIdentifier(r['RunsWithMetadataIdentifier']) for r in c]

    def DnaHashes(self, pagenum, n=1000000):
        """
        I query the Nucleotides collection and answer a page of DnaHash instances of size <= n.
        pagenum is the query page (increments of n) starting from 0.
        """
        c = self.execute(
            "SELECT DnaHash FROM Nucleotides ORDER BY DnaHash LIMIT {} OFFSET {}".format(n, pagenum*n))
        page = set([DnaHash(row['DnaHash']) for row in c])
        return page

    def extend(self, Nucleotides_collection):
        """
        Given a collection of Nucleotides instances, 
        I add any new (relative to the state of my current Nucleotides table) Nucleotides instances to my persistent collection.
        """
        # -- First, we'll filter the given Nucleotides_collection by removing any Nucleotides that we have already stored.
        i = 0
        page = self.DnaHashes(i)
        keepers = list(Nucleotides_collection)
        while page:
            considering = keepers
            keepers = [
                Nucleotides for Nucleotides in considering if Nucleotides.signature not in page]
            i += 1
            page = self.DnaHashes(i)

        # -- by the time we get here, the "keepers" list should include only those ...
        # -- ... Nucleotides that we do not already have stored.
        inset = [(str(Nucleotides.signature), Nucleotides.gzsequence)
                 for Nucleotides in keepers]
        c = self.db.cursor()
        c.executemany(
            "INSERT OR IGNORE INTO Nucleotides (DnaHash, gzsequence) VALUES (?, ?)", inset)

    def keep(self, group):
        """
        I add a given instance of TOAD.RunsWithMetadata to my persistent storage.
        """
        # --------------
        # -- Add Nucleotides |
        # --------------
        self.extend(group.hand())

        # ---------------------
        # -- Add group RunsRoster |
        # ---------------------
        doc = group.toJSON("-Nucleotides", "-SignatureAndRunsWithMetadataes")
        self.execute(
            "INSERT OR REPLACE INTO groups (RunsWithMetadataIdentifier, sqrls) VALUES (?, ?)", (group.RDN, doc))

        # --------------------------------------------------
        # -- Add SignatureAndRunsWithMetadataes for fast look up / census taking |
        # --------------------------------------------------
        self.execute(
            "DELETE FROM SignatureAndRunsWithMetadataes WHERE RunsWithMetadataIdentifier = ?", (group.RDN,))
        blocks = []
        for sig in group.SignatureAndRunsWithMetadataes:
            SignatureAndRunsWithMetadata = group.SignatureAndRunsWithMetadata(
                sig)
            blocks.append((SignatureAndRunsWithMetadata.RDN, str(
                SignatureAndRunsWithMetadata.group), SignatureAndRunsWithMetadata.toJSON()))
        c = self.db.cursor()
        c.executemany(
            "INSERT INTO SignatureAndRunsWithMetadataes (DnaHash, RunsWithMetadataIdentifier, members) VALUES (?, ?, ?)", blocks)

    def __getitem__(self, oid):
        if isinstance(oid, UniqueRunID):
            # -- look for a sqrl...
            return self.SequenceAndSignature(oid)

        if isinstance(oid, RunsWithMetadataIdentifier):
            # -- look for a group...
            return self.group(oid)

        if isinstance(oid, DnaHash):
            # -- look for a Nucleotides
            return self.Nucleotides(oid)

        raise ValueError(
            "{} is not associated with any persistent object type".format(str(oid)))

    def __contains__(self, oid):
        if isinstance(oid, UniqueRunID):
            # -- look for a sqrl...
            return self.exists("sqrls", "UniqueRunID", str(oid))

        if isinstance(oid, RunsWithMetadataIdentifier):
            # -- look for a group...
            return self.exists("groups", "RunsWithMetadataIdentifier", str(oid))

        if isinstance(oid, DnaHash):
            # -- look for a Nucleotides
            return self.exists("Nucleotides", "DnaHash", str(oid))

        raise ValueError(
            "{} is not associated with any persistent object type".format(str(oid)))
