'''
Test suite for TOAD
'''
import logging
import os
import sys

from caragols.lib import clix

from toad.db import mongolia as mx


class Toad(clix.App):
    DEFAULTS = {
        "log.level": logging.WARNING,
        "log.key": "toad_test",
        "report.form": "prose"
    }

    def __init__(self, run_mode="cli", comargs=sys.argv[1:]):
        self.run_mode = run_mode
        clix.App.__init__(self, name="toad",
                          run_mode=run_mode, comargs=comargs)

    def _get_configuration_folders(self):
        return [os.path.expanduser('~/.config/toad')]  # Talking point

    def do_show_config(self, barewords, **kwargs):
        self.conf.show()
        return self.succeeded(msg="Configuration shown.")

    def do_mock_test(self, barewords, **kwargs):
        # toadstool mock test scan: /data/folder job.file: $HOME/job1
        target_file = self.conf['job.file']
        data_folder = self.conf['scan']
        # print(f'Target file: {target_file}')
        # print(f'Data folder: {data_folder}')
        # print(f'Barewords: {barewords}, args: {kwargs}')
        # for bareword in barewords:
        #     print(f'In mock test, running {bareword}')

        self.succeeded(msg="Good job for making the mock work!", dex=[1, 2, 3])
        return 0

    def do_ingest_reads(self, barewords, **kwargs):
        # python toad_test.py ingest reads scan: ../toad/tests/ collection: fastq_tests
        # Each DO_X_Y has required params --> need a way to see this
        print(self.conf.show())
        scan = self.conf['scan']
        mx.Reader(scan, self.conf)
        self.succeeded(msg="Good job for making the mock work!", dex=[1, 2, 3])
        return 0

    def do_show_fasta(self, barewords, **kwargs):
        api_prefix = self.conf.get('api_prefix')
        response = mx.query_fasta(api_prefix=api_prefix)
        print(f'Returned data:\n{response}')
        self.succeeded(
            msg="Test to grab 1 fasta file from the API call", dex=response)
        return 0

    def do_ingest_contigs(self, barewords, **kwargs):
        scan = self.conf.get('scan', [])
        files = self.conf.get('files', [])
        print(f'Going into mx.Reader')
        mx.Reader(scan, files, self.conf)
        self.succeeded(msg="Fasta job succeeded.")

    def do_vomit_reads(self, barewords, **kwargs):
        '''
        Vomit reads docline
        '''
        # python toad_test.py vomit reads seq: sequence
        filter_args = {}
        for value in self.conf['filter']:
            print(f'Running through {value}')
            k, v = value[0], value[1]
            filter_args[k] = v
        print(f'filter_args={filter_args}')
        # print(f'Vomitting:\n{self.conf.show()}')
        print(filter_args)
        mx.MongoQuery(**filter_args)
        self.succeeded(msg="Good job, success")
        return 0

    def do_test_ingest_reads(self, barewords, **kwargs):
        api_prefix = self.conf.get('api_prefix')
        response = mx.post_fasta(api_prefix=api_prefix)
        # Report creation
        self.succeeded(
            msg="Successfully posted through the api", dex=response)
        print(self.conf.show())
        return 0
