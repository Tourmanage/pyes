# -*- coding: utf-8 -*-
from __future__ import absolute_import
from pyes.tests import ESTestCase
from pyes import exceptions

class ErrorReportingTestCase(ESTestCase):
    def setUp(self):
        super(ErrorReportingTestCase, self).setUp()
        #self.conn.indices.set_alias('test-alias', ['_river'])
        #self.conn.indices.delete_alias('test-alias', ['_river'])
        self.conn.indices.delete_index_if_exists('test-index2')

    def tearDown(self):
        #self.conn.indices.set_alias('test-alias', ['_river'])
        #self.conn.indices.delete_alias('test-alias', ['_river'])
        self.conn.indices.delete_index_if_exists('test-index2')

    def testCreateDeleteAliases(self):
        """Test errors thrown when creating or deleting aliases.

        """
        self.assertTrue('acknowledged' in self.conn.indices.create_index(self.index_name))

        # Check initial output of get_indices.
        result = self.conn.indices.get_indices(include_aliases=True)
        self.assertTrue('test-index' in result)
        self.assertEqual(result['test-index'], {'num_docs': 0})
        self.assertTrue('test-alias' not in result)

        # Check getting a missing alias.
        err = self.checkRaises(exceptions.IndexMissingException,
            self.conn.indices.get_alias, 'test-alias')
        self.assertEqual(str(err), '[test-alias] missing')

        # Check deleting a missing alias (doesn't return a error).
        self.conn.indices.delete_alias("test-alias", self.index_name)

        # Add an alias from test-alias to test-index
        self.conn.indices.change_aliases([['add', 'test-index', 'test-alias', {}]])
        self.assertEqual(self.conn.indices.get_alias("test-alias"), ['test-index'])

        # Adding an alias to a missing index fails
        err = self.checkRaises(exceptions.IndexMissingException,
            self.conn.indices.change_aliases,
            [['add', 'test-missing-index', 'test-alias', {}]])
        self.assertEqual(str(err), '[test-missing-index] missing')
        self.assertEqual(self.conn.indices.get_alias("test-alias"), ['test-index'])

        #        # An alias can't be deleted using delete_index.
        #        err = self.checkRaises(exceptions.NotFoundException,
        #                               self.conn.delete_index, 'test-alias')
        #        self.assertEqual(str(err), '[test-alias] missing')

        # Check return value from indices.get_indices now.
        result = self.conn.indices.get_indices(include_aliases=True)
        self.assertTrue('test-index' in result)
        self.assertEqual(result['test-index'], {'num_docs': 0})
        self.assertTrue('test-alias' in result)
        self.assertEqual(result['test-alias'], {'alias_for': ['test-index'], 'num_docs': 0})

        result = self.conn.indices.get_indices(include_aliases=False)
        self.assertTrue('test-index' in result)
        self.assertEqual(result['test-index'], {'num_docs': 0})
        self.assertTrue('test-alias' not in result)

        # Add an alias to test-index2.
        self.assertTrue('ok' in self.conn.indices.create_index("test-index2"))
        self.conn.indices.change_aliases([['add', 'test-index2', 'test-alias', {}]])
        self.assertEqual(sorted(self.conn.indices.get_alias("test-alias")),
            ['test-index', 'test-index2'])

        # Check deleting multiple indices from an alias.
        self.conn.indices.delete_alias("test-alias", [self.index_name, "test-index2"])
        self.checkRaises(exceptions.IndexMissingException, self.conn.indices.get_alias, 'test-alias')

        # Check deleting multiple indices from a missing alias (still no error)
        self.conn.indices.delete_alias("test-alias", [self.index_name, "test-index2"])

        # Check that we still get an error for a missing alias.
        err = self.checkRaises(exceptions.IndexMissingException,
            self.conn.indices.get_alias, 'test-alias')
        self.assertEqual(str(err), '[test-alias] missing')

    def testWriteToAlias(self):
        self.assertTrue('acknowledged' in self.conn.indices.create_index(self.index_name))
        self.assertTrue('acknowledged' in self.conn.indices.create_index("test-index2"))
        self.assertTrue('acknowledged' in self.conn.indices.set_alias("test-alias", ['test-index']))
        self.assertTrue('acknowledged' in self.conn.indices.set_alias("test-alias2", ['test-index', 'test-index2']))

        # Can write to indices.aliases only if they point to exactly one index.
        self.conn.index(dict(title='doc1'), 'test-index', 'testtype')
        self.conn.index(dict(title='doc1'), 'test-index2', 'testtype')
        self.conn.index(dict(title='doc1'), 'test-alias', 'testtype')
        self.checkRaises(exceptions.ElasticSearchIllegalArgumentException,
            self.conn.index, dict(title='doc1'),
            'test-alias2', 'testtype')

        self.conn.indices.refresh() # ensure that the documents have been indexed.
        # Check the document counts for each index or alias.
        result = self.conn.indices.get_indices(include_aliases=True)
        self.assertEqual(result['test-index'], {'num_docs': 2})
        self.assertEqual(result['test-index2'], {'num_docs': 1})
        self.assertEqual(result['test-alias'], {'alias_for': ['test-index'], 'num_docs': 2})
        self.assertEqual(result['test-alias2'], {'alias_for': ['test-index', 'test-index2'], 'num_docs': 3})

if __name__ == "__main__":
    import unittest
    unittest.main()

