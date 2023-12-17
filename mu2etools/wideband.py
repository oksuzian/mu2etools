NCHAN_FEB = 64
NCHAN_CMB = 4
SEC_YEAR=3.154e+7
MIN_TEMP=18
MAX_TEMP=21
BAD_RUNS=[42, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 
          55, 56, 57, 58, 59, 60, 61, 62, 64, 67, 68, 69, 
          80, 83, 87, 88, 89, 91, 96, 101, 105, 110, 115, 
          1027, 1066, 1084, 1134, 1173, 1037, 1038, 1039, 
          1040, 1041, 1042, 1043, 1173, 1178, 1209, 1311,
          1340, 1374, 1377, 1378]

import subprocess
import uproot
import numpy as np
import pandas as pd
import awkward as ak
import matplotlib.pyplot as plt

class DataProcessor:
    def __init__(self, usexroot=False, fixtimes=True, runlist=BAD_RUNS, userunlist=True, remove=True, treename="runSummary", filter_name="*", debug=False):
        self.usexroot = usexroot
        self.runlist = runlist
        self.fixtimes = fixtimes
        self.userunlist = userunlist
        self.remove = remove
        self.treename = treename
        self.filter_name = filter_name
        self.debug = debug


    def getData(self, defname):
        # Create filelist with full path in dCache
        filelist = self.getFilelist(defname)
        file_list_ = ["{}{}".format(i, ":%s"%self.treename) for i in filelist]
        if self.debug:
            print(file_list_)
        ar = uproot.concatenate(file_list_, xrootdsource={"timeout": 720}, filter_name=self.filter_name)

        #Fill all timestamps with subruns!=0 to  timestamps with subruns==0. FIXME
        if self.fixtimes:
            for run in ar["runNumber", (ar["subrunNumber"]==0)]:
                np.asarray(ar["timestamp"])[(ar["runNumber"]==run)] = (ar["timestamp", (ar["runNumber"]==run) & (ar["subrunNumber"]==0)])

        return ar

    def getFilelist(self, defname):
        # Get the list of files with full pathnames
        commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh; "
                    "setup mdh; setup dhtools; setup mu2efiletools")
        if self.usexroot:
#            commands = commands + "samweb list-definition-files %s | sort | mdh print-url -s root -" % defname
            commands = commands + "mu2eDatasetFileList %s | xargs -I{} basename {} | mdh print-url -s root -" % defname
        else:
#            commands = commands + "samweb list-definition-files %s | sort | mdh print-url -" % defname
            commands = commands + "mu2eDatasetFileList %s " % defname

        filelist = subprocess.check_output(commands, shell=True, universal_newlines=True)
        filelist = filelist.splitlines()

        # Prepend zeros
        runs = [str(x).zfill(6) for x in self.runlist]
        #Select runs from the list
        def select_good_runs(runs, filelist):
            if self.remove:
                return [item for item in filelist if not any(run in item for run in runs)]
            else:
                return [item for item in filelist if any(run in item for run in runs)]

        if self.userunlist:        
            filelist = select_good_runs(runs, filelist)
        return filelist

    def listBadRuns(self):
        print(BAD_RUNS)

