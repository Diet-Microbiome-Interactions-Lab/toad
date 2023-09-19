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


class axsNUCLS:
	def __init__(self, pi):
		self.pi = pi

	def __getitem__(self, k):
		if isinstance(k, DASH):
			c = self.pi.execute("SELECT * FROM axs WHERE dash = ?", (str(k),))
			r = c.fetchone( )
			if r is not None:
				return axs(r['dash'], r['gzsequence'])
			else:
				raise KeyError(k)

	def __contains__(self, k):
		return self.pi.exists('axs', 'dash', str(k))

	def __len__(self):
		c = self.pi.execute("SELECT COUNT(*) AS tallied from axs")
		r = c.fetchone( )
		return r['tallied']

	def keys(self):
		c = self.pi.execute("SELECT dash FROM axs")
		return [enDASH(r['dash']) for r in c]

	def __iter__(self):
		for k in self.keys( ):
			yield self[asDASH(k)]


class axsGroups:
	def __init__(self, pi):
		self.pi = pi

	def keys(self):
		c = self.pi.execute("SELECT grin FROM groups ORDER BY grin")
		return [GrIN(r['grin']) for r in c]

	def __len__(self):
		c = self.pi.execute("SELECT COUNT(*) AS tallied FROM groups")
		r = c.fetchone( )
		return r['tallied']

	def __contains__(self, grin):
		return self.pi.exists('groups', 'grin', str(grin))

	def __getitem__(self, grin):
		c = self.pi.execute("SELECT grin, sqrls FROM groups WHERE grin = ?", (str(grin),))
		r = c.fetchone( )
		if r is None:
			raise KeyError(str(grin))
		else:
			g = Group.fromJSON(r['sqrls'])
			return g

	def __iter__(self):
		for k in self.keys( ):
			yield self[k]
		


class Pi(TOAD.DB.common.Pi):
	def __init__(self, db_path):
		logger.debug("opening db at {}".format(db_path))
		self.db = sqlite3.connect(db_path)
		self.db.row_factory = sqlite3.Row
		self.provision( )

		#-----------------------------
		#-- Some special accessors...|
		#-----------------------------
		self.axs  = axsaxs(self)
		self.groups = axsGroups(self)

	def execute(self, query, quargs = None):
		c = self.db.cursor( )
		if quargs:
			return c.execute(query, quargs)
		else:
			return c.execute(query)

	def commit(self):
		self.db.commit( )

	def close(self):
		self.db.close( )

	def provision(self):
		self.db.execute("CREATE TABLE IF NOT EXISTS nucls   (dash  TEXT PRIMARY KEY, gzsequence BLOB)")
#		self.db.execute("CREATE TABLE IF NOT EXISTS sqrls   (druid TEXT PRIMARY KEY, grin TEXT, sig TEXT)")
		self.db.execute("CREATE TABLE IF NOT EXISTS groups  (grin  TEXT PRIMARY KEY, sqrls BLOB)")

		self.db.execute("CREATE TABLE IF NOT EXISTS clutches(dash TEXT, grin TEXT, members BLOB)")
		self.db.execute("CREATE INDEX IF NOT EXISTS clutches_dashes ON clutches(dash)")
		self.db.execute("CREATE INDEX IF NOT EXISTS clutches_grins ON clutches(grin)")

#		self.db.execute("CREATE TABLE IF NOT EXISTS carriers(dash TEXT, grins BLOB)")
#		self.db.execute("CREATE INDEX IF NOT EXISTS carriers_dashes ON carriers(dash)")

	def find_one(self, tbl, k, v):
		"""
		Answers a single row from the given table (tbl) where column (k) has value (v).
		If no such row exists, I answer None.
		"""
		c = self.execute("SELECT {} FROM {} WHERE ({} = ?) LIMIT 1".format(tbl, k, v), v)
		return c.fetchone( )

	def exists(self, tbl, k, v):
		"""
		Performs a simple existence query that table (tbl) has at least one row where column (k) has value (v).
		"""
		r = self.lookup(tbl, k, v)
		if r is not None:
			return True
		else:
			return False

	def carriers(self, dash):
		"""
		I answer the set of all groups that have at least one instance of the given NUCLS.
		"""
		c = self.execute("SELECT grin FROM clutches WHERE (dash = ?)", (str(dash),))
		return [GrIN(r['grin']) for r in c]

	def dashes(self, pagenum, n = 1000000):
		"""
		I query the NUCLS collection and answer a page of DASH instances of size <= n.
		pagenum is the query page (increments of n) starting from 0.
		"""
		c = self.execute("SELECT dash FROM nucls ORDER BY DASH LIMIT {} OFFSET {}".format(n, pagenum*n))
		page = set( [DASH(row['dash']) for row in c] )
		return page

	def extend(self, nucls_collection):
		"""
		Given a collection of NUCLS instances, 
		I add any new (relative to the state of my current NUCLS table) NUCLS instances to my persistent collection.
		"""
		#-- First, we'll filter the given nucls_collection by removing any nucls that we have already stored.
		i = 0
		page = self.dashes(i)
		keepers = list(nucls_collection)
		while page:
			considering = keepers
			keepers     = [nucls for nucls in considering if nucls.signature not in page]
			i += 1
			page = self.dashes(i)
		
		#-- by the time we get here, the "keepers" list should include only those ...
		#-- ... NUCLS that we do not already have stored.
		inset = [(str(nucls.signature), nucls.gzsequence) for nucls in keepers]
		c = self.db.cursor( )
		c.executemany("INSERT OR IGNORE INTO nucls (dash, gzsequence) VALUES (?, ?)", inset) 

	def keep(self, group):
		"""
		I add a given instance of TOAD.Group to my persistent storage.
		"""
		#--------------
		#-- Add NUCLS |
		#--------------
		self.extend( group.hand( ) )

		#---------------------
		#-- Add group roster |
		#---------------------
		doc = group.toJSON("-nucls", "-clutches")
		self.execute("INSERT OR REPLACE INTO groups (grin, sqrls) VALUES (?, ?)", (group.RDN, doc))

		#--------------------------------------------------
		#-- Add clutches for fast look up / census taking |
		#--------------------------------------------------
		self.execute("DELETE FROM clutches WHERE grin = ?", (group.RDN,))
		blocks = [ ]
		for sig in group.clutches:
			clutch = group.clutch(sig)
			blocks.append( (clutch.RDN, str(clutch.group), clutch.toJSON( )) )
		c = self.db.cursor( )
		c.executemany("INSERT INTO clutches (dash, grin, members) VALUES (?, ?, ?)", blocks)

	def __getitem__(self, oid):
		if isinstance(oid, DRuID):
			#-- look for a sqrl...
			return self.SqRL(oid)

		if isinstance(oid, GrIN):
			#-- look for a group...
			return self.group(oid)

		if isinstance(oid, DASH):
			#-- look for a NUCLS
			return self.NUCLS(oid)

		raise ValueError("{} is not associated with any persistent object type".format(str(oid)))

	def __contains__(self, oid):
		if isinstance(oid, DRuID):
			#-- look for a sqrl...
			return self.exists("sqrls", "druid", str(oid))

		if isinstance(oid, GrIN):
			#-- look for a group...
			return self.exists("groups", "grin", str(oid))

		if isinstance(oid, DASH):
			#-- look for a NUCLS
			return self.exists("nucls", "dash", str(oid))

		raise ValueError("{} is not associated with any persistent object type".format(str(oid)))
