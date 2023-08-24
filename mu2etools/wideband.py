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
    def __init__(self, usexroot=False, fixtimes=True, runlist=BAD_RUNS, userunlist=True, remove=True, treename="runSummary", filter_name="*"):
        self.usexroot = usexroot
        self.runlist = runlist
        self.fixtimes = fixtimes
        self.userunlist = userunlist
        self.remove = remove
        self.treename = treename
        self.filter_name = filter_name


    def getData(self, defname):
        # Create filelist with full path in dCache
        filelist = self.getFilelist(defname)
        file_list_ = ["{}{}".format(i, ":%s"%self.treename) for i in filelist]
        ar = uproot.concatenate(file_list_, xrootdsource={"timeout": 720}, filter_name=self.filter_name)

        #Fill all timestamps with subruns!=0 to  timestamps with subruns==0. FIXME
        if self.fixtimes:
            for run in ar["runNumber", (ar["subrunNumber"]==0)]:
                np.asarray(ar["timestamp"])[(ar["runNumber"]==run)] = (ar["timestamp", (ar["runNumber"]==run) & (ar["subrunNumber"]==0)])

        return ar

    def getFilelist(self, defname):
        # Get the list of files with full pathnames
	commands = ("source /cvmfs/mu2e.opensciencegrid.org/setupmu2e-art.sh; "
            	    "setup mdh; setup dhtools; ")
	if self.usexroot:
    	    commands = commands + "samweb list-definition-files %s | mdh file-url -s root -" % defname
	else:
    	    commands = commands + "samweb list-definition-files %s | mdh file-url -" % defname

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

    def plotFits(self, ar, xvar, yvar, febid, minrun, nofit=False, debug=False):
        np.set_printoptions(precision=1)
        df = pd.DataFrame(columns=['slope', 'offset', 'chan', 'feb'])
        ar_ = ar[ar['runNumber']>minrun] # Select only data after electronics rack was installed
        for idx, feb in enumerate(febid):
            fig, axes = plt.subplots(nrows=1, ncols=16, figsize=(24, 2), sharey='row')
            plt.subplots_adjust(wspace=0)
            axes[0].set_ylabel('SPE | FEB%d'%feb)
            for chan in range(NCHAN_FEB): # Loop through sipms
                sipm = chan % 4
                ax = axes[chan//4]
                cut = ar_['stddevTemperatures'][:, idx, chan] > 0.01

                x = ar_[xvar, cut][:, idx, chan].to_numpy()
                y = ar_[yvar, cut][:, idx, chan].to_numpy()

                if np.any(x<0.1) or np.any(y<0.1):
                    print(feb, chan, x, y)
                    continue
                if debug:
                    print(feb, chan, x, y)

                linmodel = np.poly1d(np.polyfit(x, y, 1))
                xline = np.linspace(17, 25, 100)
                ax.plot(xline, linmodel(xline), 'r--', linewidth=0.5)
                ax.plot(x,y, '.--', linewidth=0.5, markersize=3, label='Ch%d: %.2f'%(chan, linmodel.coeffs[0]))
                ax.set_xlabel('Temp [C]', fontsize=10)
                ax.set_xlim(16, 27)
                ax.legend(prop={'size': 8}, loc='upper right')
                new_row = {'slope': linmodel.coeffs[0], 'offset': linmodel.coeffs[1], 'chan':chan, 'feb':feb}
                df.loc[len(df)] = new_row

        return df
