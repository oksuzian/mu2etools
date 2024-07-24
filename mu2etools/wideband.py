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
    def __init__(self, fixtimes=True, runlist=BAD_RUNS, userunlist=True, remove=True, treename="runSummary", filter_name="*", debug=False, filter_func=None):
        self.runlist = runlist
        self.fixtimes = fixtimes
        self.userunlist = userunlist
        self.remove = remove
        self.treename = treename
        self.filter_name = filter_name
        self.debug = debug
        self.filter_func = filter_func or self.defaultFilter

    def defaultFilter(self, arr):
        return arr
        
    def getData(self, defname):
        # Create filelist with full path in dCache
        filelist = self.getFilelist(defname)
        if self.debug:
            print(filelist)
        ar_skim_list = []
        for idx, filename in enumerate(filelist):
            percent_complete = (idx + 1)/len(filelist) * 100
            print("\rProcessing file: %s - %.1f%% complete" % (filename, percent_complete), end='', flush=True)
            file = self.openFile(filename)
            ar = file[self.treename].arrays(filter_name=self.filter_name)
            ar_filtered = self.filter_func(ar)
            ar_skim_list.append(ar_filtered)
            
        ar = ak.concatenate(ar_skim_list, axis=0)
        #Fill all timestamps with subruns!=0 to  timestamps with subruns==0. FIXME
        if self.fixtimes:
            for run in ar["runNumber", (ar["subrunNumber"]==0)]:
                np.asarray(ar["timestamp"])[(ar["runNumber"]==run)] = (ar["timestamp", (ar["runNumber"]==run) & (ar["subrunNumber"]==0)])
        return ar
    
    def openFile(self, filename):
        # Try to open a file 10 times
        for i in range(0,10):
            while True:
                try:
                    commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh; muse setup ops;")
                    commands = commands + "echo %s | mdh print-url -s root -" % filename
                    filename = subprocess.check_output(commands, shell=True, universal_newlines=True)
                    file = uproot.open("%s"%filename)
                    return file
                except OSError as e:
                    print("Exception timeout opening file with xroot: Retrying localy: %s"%filename)                    
                    commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh;"
                    "muse setup ops;")
                    commands = commands + "echo %s | mdh copy-file -s tape -l local -" % filename
                    subprocess.check_output(commands, shell=True, universal_newlines=True)
                    file = uproot.open("%s"%filename)
                    return file                
                    continue
                break

    
    def getEffData(self, defname, varlist, nfiles=10000, timeout=7200, step_size="10MB"):
        filelist = self.getFilelist(defname)
            
        ar_skim_list = []
        for idx, filename in enumerate(filelist[0:nfiles]):
            percent_complete = (idx + 1) / len(filelist) * 100
            print("\rProcessing file: %s - %.1f%% complete" % (filename, percent_complete), end='', flush=True)
            ar_skim_list.append(self.processFile(filename, varlist, timeout, step_size))
        ar = ak.concatenate(ar_skim_list, axis=0)
        return ar

    def processBatch(self, ar):
        
        all_layers = np.arange(0,16) 
        test_layers = np.arange(2,6) # Test layers are 2 through 6
        trig_layers = all_layers[~np.isin(all_layers, test_layers)]
        
        # Set PEs to zero for aging and quad-counters
        ak.to_numpy(ar['PEs'])[:, 0, 0:8] = 0
        ak.to_numpy(ar['PEs'])[:, 3, 0:8] = 0
        ak.to_numpy(ar['PEs'])[:, 7, 0:8] = 0
        # Filter out hits below 5PE
        ar_trig_filt = ak.where(ar['PEs'] >= 5, ar['PEs'], 0)
        # Calculate PEs for even and odd layers
        PEs_even_layers = ak.sum(ar_trig_filt[:, :, 0:32], axis=-1).to_numpy()
        PEs_odd_layers = ak.sum(ar_trig_filt[:, :, 32:64], axis=-1).to_numpy()        
        # Interleave the elements from even and odd arrays
        PEs_interleaved = np.concatenate((PEs_even_layers[:, :, np.newaxis], PEs_odd_layers[:, :, np.newaxis]), axis=2)
        # Reshape the interleaved array to match the desired shape
        PEs_stacked = PEs_interleaved.reshape(-1, 16)        
        # Add PEs for even and odd layers to the original array
        ar['PEsAllLayer'] = PEs_stacked
        # Count the number of triggered layers
        ar['nTrigHits'] = ak.sum(ar['PEsAllLayer'][:, trig_layers] > 10, axis=-1)
        # Filter out events with more than 10 triggered layers        
        ar = ar[ar['nTrigHits'] > 8]
        # Extract PEsTestLayers and PEsTrigLayers
        ar['PEsTestLayers'] = ar['PEsAllLayer'][:, test_layers]
        ar['PEsTrigLayers'] = ar['PEsAllLayer'][:, trig_layers]

        return ar 
    
    def processFile(self, filename, varlist, timeout=7200, step_size="10MB"):
        ar_skim_list = []
        file = self.openFile(filename)
        for ar in uproot.iterate(file, step_size=step_size, 
                               filter_name=['PEs', varlist], 
                               library='ak', options={"timeout": timeout}):
            ar = self.processBatch(ar)
            ar_skim_list.append(ar[varlist])
            
        ar_skim = ak.concatenate(ar_skim_list, axis=0)            
        return ar_skim
        
    def getFilelist(self, defname, root_schema=False):
        # Get the list of files with full pathnames
        commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh; "
                    "muse setup ops;")
        if root_schema:
            commands = commands + "samweb list-files 'defname: %s with availability anylocation' | sort | mdh print-url -s root -" % defname
        else:
            commands = commands + "samweb list-files 'defname: %s with availability anylocation' | sort " % defname

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

