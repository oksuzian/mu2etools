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
    
    def openFile(self, filename):
        for i in range(0,100):
            while True:
                try:
                    file = uproot.open(filename)
                    return file
                except OSError as e:
                    print("Exception timeout opening file: Retrying...%d"%i)
                    continue
                break

    
    def getEffData(self, defname, nfiles=10000, data_type=-1, timeout=7200, step_size="10MB", keep_trig=False):
        # Create filelist with full path in dCache
        filelist = self.getFilelist(defname)
        file_list_ = ["{}{}".format(i, ":%s"%self.treename) for i in filelist]
        if self.debug:
            print(file_list_)
            
        ar_skim_list = []
        for idx, filename in enumerate(file_list_[0:nfiles]):
            if idx%25 == 0:
                print("Processing file: %s"%filename)
            file = self.openFile(filename)
            ar_skim_list.append(self.processFile(file, data_type, timeout, step_size, keep_trig))
        ar_skim = ak.concatenate(ar_skim_list, axis=0)
        # Number of layer hits in the test module
        ar_skim['nTestHits'] = ak.sum(ar_skim['PEsTestLayers'] > 10, axis=-1)
        # Chi2NDF only if denominator if > 0
        ar_skim['trackChi2NDF'] = ak.where(ar_skim['trackPoints'] > 2, ar_skim['trackChi2'] / (ar_skim['trackPoints'] - 2), -999)
        return ar_skim
            
    def processFile(self, file, data_type=-1, timeout=7200, step_size="10MB", keep_trig=False):
        
        #List of variable to export to a skimmed array
        varlist=['spillNumber', 'eventNumber','runNumber', 'subrunNumber',
                 'trackPEs', 'trackPoints', 'trackChi2', 'trackIntercept', 'trackSlope']

        all_layers = np.arange(0,16) 
        test_layers = np.arange(2,6) # Test layers are 2 through 6
        trig_layers = all_layers[~np.isin(all_layers, test_layers)]
        varlist.extend(['nTrigHits', 'PEsTestLayers', 'dataType'])
        if keep_trig:
            varlist.extend(['PEsTrigLayers'])

        ar_skim_list = []            
        for i in range(0,100):
            while True:
                try:
                    for ar in uproot.iterate(file, step_size=step_size, 
                                           filter_name=['PEs', varlist, 'coincidencePosX'], 
                                           library='ak', options={"timeout": timeout}):
                        # Set PEs to zero for aging and quad-counters
                        ak.to_numpy(ar['PEs'])[:,0,0:8] = 0
                        ak.to_numpy(ar['PEs'])[:,3,0:8] = 0
                        ak.to_numpy(ar['PEs'])[:,7,0:8] = 0
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
                        # Extract only PEsTestLayers to save memory
                        ar['PEsTestLayers'] = ar['PEsAllLayer'][:, test_layers]
                        ar['PEsTrigLayers'] = ar['PEsAllLayer'][:, trig_layers]
                        ar['dataType'] = data_type        

                        if data_type > 0: # means MC samples is provided
                            ar['trackIntercept'] = ar['trackIntercept'] - 20950.0
                            # Mimic the trigger paddles
                            trigPad_cut = (abs(ar["coincidencePosX"][:,1]+5604) < 50) & (abs(ar["coincidencePosX"][:,4] + 5604) < 50)
                            ar = ar[trigPad_cut]
                        return ar[varlist]

                except OSError as e:
                    print("Exception timeout opening batch: Retrying...%d"%i)
                    continue
                break

            
            
        
    def getFilelist(self, defname):
        # Get the list of files with full pathnames
        commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh; "
                    "setup mdh; setup dhtools;")
        if self.usexroot:
            commands = commands + "samweb list-files 'defname: %s with availability anylocation' | sort | mdh print-url -s root -" % defname
        else:
            commands = commands + "samweb list-files 'defname: %s with availability anylocation' | sort | mdh print-url -" % defname

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

