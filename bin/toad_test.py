from toad.db import mongolia as mx
import logging
import os
import sys

from caragols.lib import clix
# from toad.


class Toad(clix.App):
    DEFAULTS = {
        "log.level": logging.WARNING,
        "log.key": "toad_test",
        "report.form": "prose"
    }

    def __init__(self):
        clix.App.__init__(self, "toad")

    def _get_configuration_folders(self):
        return [os.path.expanduser('~/.config/toad')]  # Talking point

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
        print(self.conf.show())
        scan = self.conf['scan']
        mx.Reader(scan, self.conf)
        self.succeeded(msg="Good job for making the mock work!", dex=[1, 2, 3])
        return 0


if __name__ == "__main__":
    myapp = Toad()
    comargs = sys.argv[1:]
    myapp.conf.sed(comargs)
    print(myapp.conf.show())
