hep.style.use('ATLAS')  # or ATLAS/LHCb2

NCHAN_FEB = 64
NCHAN_CMB = 4
SEC_YEAR=3.154e+7
MIN_TEMP=18
MAX_TEMP=21



BAD_RUNS=[42, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 
          55, 56, 57, 58, 59, 60, 61, 62, 64, 67, 68, 69, 
          80, 83, 87, 88, 89, 91, 96, 101, 105, 110, 115, 
          1027, 1066, 1084, 1134, 1173, 1037, 1038, 1039, 
          1040, 1041, 1042, 1043, 1173, 1178, 1209, 1374,
          1377, 1378]

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

    def listBadRuns(self):
        print(BAD_RUNS)

    def load_modules(self):
        import importlib

        modules_to_load = ['numpy', 'pandas', 'matplotlib.pyplot']
        module_names = modules_to_load
        for module_name in module_names:
            print(module_name)
#            globals()[module_name] = __import__(module_name)                
            module = importlib.import_module(module_name)
            globals()[module_name] = module

    def plotFits(self, ar, xvar, yvar, febid, minrun):

        df = pd.DataFrame(columns=['slope', 'offset', 'chan', 'feb'])
        ar_ = ar[ar['runNumber']>minrun] # Select only data after electronics rack was installed

        for idx, feb in enumerate(febid):
            fig, axes = plt.subplots(nrows=1, ncols=16, figsize=(24, 2), sharey='row')
            plt.subplots_adjust(wspace=0)
            axes[0].set_ylabel('SPE | FEB%d'%feb)
            for chan in range(NCHAN_FEB): # Loop thgough hdmi
                sipm = chan % 4
                ax = axes[chan//4]    
                x = ar_[xvar][:, idx, chan].to_numpy()
                y = ar_[yvar][:, idx, chan].to_numpy()
                x=x[y > 0] # Drop bad SPE points 
                y=y[y > 0] # Drop bad SPE points
                y=y[x > 0] # Drop bad Temp points
                x=x[x > 0] # Drop bad Temp points 
                if len(x) == 0: # Drop dead channels
                    continue

                linmodel = np.poly1d(np.polyfit(x, y, 1))
                xline = np.linspace(17, 25, 100)
                ax.plot(xline, linmodel(xline), 'r--', linewidth=0.5)
                ax.plot(x,y, '.', linewidth=0.5, markersize=3, label='Ch%d: %.2f'%(chan, linmodel.coeffs[0]))
                ax.set_xlabel('Temp [C]', fontsize=10)
                ax.set_xlim(16, 27)
                ax.legend(prop={'size': 8}, loc='upper right')
                new_row = {'slope': linmodel.coeffs[0], 'offset': linmodel.coeffs[1], 'chan':chan, 'feb':feb}
                df.loc[len(df)] = new_row            
    return df
