import subprocess
import uproot
import numpy as np


BAD_RUNS=[42, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 64, 67, 68, 69, 80, 83, 87, 88, 89, 91, 96, 101, 105, 110, 115, 1027, 1066, 1084, 1134, 1173, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1173, 1178, 1209, 1374]
XROOT = False

class DataProcessor:
    def __init__(self, xroot, fixtimes):
        self.xroot = xroot
        self.fixtimes = fixtimes

    def getData(self, defname):
        # Define bad runs
        badruns = [str(x).zfill(6) for x in BAD_RUNS]
        # Create filelist with full path in dCache
        filelist = self.getFilelist(defname)
        
        #Remove bad runs from the list
        def select_good_runs(badruns, filelist):
            return [item for item in filelist if not any(badrun in item for badrun in badruns)]        
        filelist = select_good_runs(badruns, filelist)

        #Optionally, change the filelist to xroot locations
        good_run_list = []
        for root_file in filelist:
            if self.xroot:
                root_file = 'root://fndca1.fnal.gov'+root_file[:5]+'/fnal.gov/usr/'+root_file[6:]
            good_run_list.append(root_file)

        file_list_ = ["{}{}".format(i, ":runSummary") for i in good_run_list]
        ar = uproot.concatenate(file_list_, xrootdsource={"timeout": 720})

        file_list_ = ["{}{}".format(i, ":spills") for i in good_run_list]
        arSpills = uproot.concatenate(file_list_, xrootdsource={"timeout": 720})

        #Fill all timestamps with subruns!=0 to  timestamps with subruns==0. FIXME
        if self.fixtimes:
            for run in ar["runNumber", (ar["subrunNumber"]==0)]:
                np.asarray(ar["timestamp"])[(ar["runNumber"]==run)] = (ar["timestamp", (ar["runNumber"]==run) & (ar["subrunNumber"]==0)])

        return ar, arSpills

    def getFilelist(self, defname):
        # Get the list of files with full pathnames
        commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh; "
                    "setup mu2efiletools; setup dhtools; "
                    "samListLocations --defname %s" % defname)
        filelist = subprocess.check_output(commands, shell=True, universal_newlines=True)
        filelist = filelist.splitlines()
        return filelist
