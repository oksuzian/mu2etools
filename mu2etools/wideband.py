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
from concurrent.futures import ThreadPoolExecutor, as_completed

class DataProcessor:
    def __init__(self, fixtimes=True, runlist=BAD_RUNS, userunlist=True, remove=True, treename="runSummary", filter_name="*", debug=False, filter_func=None, filter_args=(), infile_location='tape'):
        self.runlist = runlist
        self.fixtimes = fixtimes
        self.userunlist = userunlist
        self.remove = remove
        self.treename = treename
        self.filter_name = filter_name
        self.debug = debug
        self.filter_func = filter_func or self.defaultFilter
        self.filter_args = filter_args
        self.infile_location = infile_location

    def defaultFilter(self, arr):
        return arr
        
    def getData(self, defname, max_workers=10, step_size="10MB", nfiles=-1):
        # Create filelist with full path in dCache
        filelist = self.getFilelist(defname)
        if nfiles>0:
            filelist=filelist[:nfiles]        
        if self.debug:
            print(filelist)

        def process_file(filename):
            # Attempt to open the file with retries
            try:
                file = self.openFile(filename)
                # Load the array in chunks using step_size to limit memory use
                ar_chunks = []
                for chunk in uproot.iterate(file[self.treename], step_size=step_size, filter_name=self.filter_name, library="ak"):
                    filtered_chunk = self.filter_func(chunk, *self.filter_args)                    
                    ar_chunks.append(filtered_chunk)
                # Concatenate chunks for a single file
                return ak.concatenate(ar_chunks) if ar_chunks else None
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                return None
    
        ar_skim_list = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_file, filename): filename for filename in filelist}
            
            for idx, future in enumerate(as_completed(futures)):
                filename = futures[future]
                try:
                    ar_filtered = future.result()
                    ar_skim_list.append(ar_filtered)
                    percent_complete = (idx + 1) / len(filelist) * 100
                    print("\rProcessing file: %s - %.1f%% complete" % (filename, percent_complete), end='', flush=True)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
    
        ar = ak.concatenate(ar_skim_list, axis=0)
        
        # Fill all timestamps with subruns != 0 to timestamps with subruns == 0
        if self.fixtimes:
            for run in ar["runNumber", (ar["subrunNumber"] == 0)]:
                np.asarray(ar["timestamp"])[(ar["runNumber"] == run)] = (
                    ar["timestamp", (ar["runNumber"] == run) & (ar["subrunNumber"] == 0)]
                )
        
        return ar
    
    def openFile(self, filename):
        # Try to open a file 10 times
        for i in range(0,10):
            while True:
                try:
                    commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh; muse setup ops;")
                    commands = commands + "mdh print-url -s root -l %s %s" % (self.infile_location, filename)
                    filename = subprocess.check_output(commands, shell=True, universal_newlines=True)
                    file = uproot.open("%s"%filename)
                    return file
                except OSError as e:
                    print("Exception timeout opening file with xroot: Retrying localy: %s"%filename)                    
                    commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh;"
                    "muse setup ops;")
                    commands = commands + "mdh copy-file -s %s -l local %s" % (self.infile_location, filename)
                    subprocess.check_output(commands, shell=True, universal_newlines=True)
                    file = uproot.open("%s"%filename)
                    return file                
                    continue
                break
        
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

