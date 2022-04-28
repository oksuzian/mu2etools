#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import pandas

  
LIVETIME_LO=1.36E8+5.09E7
LIVETIME_HI=5.49E6 
LIVETIME_MU2E=3.46E6
LYIELD_SCALE=0.001726


CRV_SECTOR_NAMES_V8 = {
                       "R1":  "//0   CRV-R modules first three modules at TS",
                       "R2":  "//1   CRV-R modules upstream of cryo hole (except first three modules at TS)",
                       "R3":  "//2   CRV-R module above cryo hole",
                       "R4":  "//3   CRV-R module below cryo hole",
                       "R5":  "//4   CRV-R modules downstream of cryo hole (except endcap)",
                       "R6":  "//5   CRV-R modules at endcap",
                       "L1":  "//6   CRV-L modules (except endcap)",
                       "L2":  "//7   CRV-L modules at endcap",
                       "T1":  "//8   CRV-TS modules (three upstream modules)",
                       "T2":  "//9   CRV-TS modules (two downstream modules)",
                       "T3":  "//10   CRV-T modules (four upstream modules)",
                       "T4":  "//11  CRV-T modules (remaining 16 downstream modules)",
                       "E1":  "//12  CRV-TS-Extension upstream module",
                       "E2":  "//13  CRV-TS-Extension downstream module",
                       "U":   "//14  CRV-U modules",
                       "D1":  "//15  CRV-D modules above beam pipe",
                       "D2":  "//16  CRV-D module at -x of beam pipe",
                       "D3":  "//17  CRV-D module at +x of beam beam pipe",
                       "D4":  "//18  CRV-D module below beam pipe",
                       "C1":  "//19  CRV-Cryo-Inner module upstream of cryo hole",
                       "C2":  "//20  CRV-Cryo-Inner module downstream of cryo hole",
                       "C3":  "//21  CRV-Cryo-Outer module above of cryo hole",
                       "C4":   "//22  CRV-Cryo-Outer module downstream of cryo hole"
                      }


CRV_SECTOR_NAMES_V7 = {
                       "R1":  "0   CRV-R modules upstream of cryo hole", 
                       "R2":  "1   CRV-R module above cryo hole", 
                       "R3":  "2   CRV-R module below cryo hole", 
                       "R4":  "3   CRV-R modules downstream of cryo hole (except endcap)", 
                       "R5":  "4   CRV-R modules at endcap", 
                       "L1":  "5   CRV-L modules (except endcap)", 
                       "L2":  "6   CRV-L modules at endcap", 
                       "T1":  "7   CRV-TS modules (three upstream modules)", 
                       "T2":  "8   CRV-TS modules (two downstream modules)", 
                       "T3":  "9   CRV-T modules (four upstream modules)", 
                       "T4":  "10  CRV-T modules (remaining 16 downstream modules)", 
                       "E1":  "11  CRV-TS-Extension upstream module", 
                       "E2":  "12  CRV-TS-Extension downstream module", 
                       "U":   "13  CRV-U modules", 
                       "D1":  "14  CRV-D modules above beam pipe", 
                       "D2":  "15  CRV-D module at -x of beam pipe", 
                       "D3":  "16  CRV-D module at +x of beam beam pipe", 
                       "D4":  "17  CRV-D module below beam pipe", 
                       "C1":  "18  CRV-Cryo-Inner module upstream of cryo hole", 
                       "C2":  "19  CRV-Cryo-Inner module downstream of cryo hole", 
                       "C3":  "20  CRV-Cryo-Outer module above of cryo hole", 
                       "C4":  "21  CRV-Cryo-Outer module downstream of cryo hole"
                      }

def getNormBackground(df, cuts, scale):
    # scale - to account for a larger momentum window
    raw_count_hi = len(df.query('is_high==1 & %s' % cuts))
    raw_count_lo = len(df.query('is_high==0 & %s' % cuts))

    ave_hi = raw_count_hi/LIVETIME_HI*LIVETIME_MU2E/scale
    ave_lo = raw_count_lo/LIVETIME_LO*LIVETIME_MU2E/scale
    ave = ave_hi + ave_lo
  
    err_hi = math.sqrt(raw_count_hi)/LIVETIME_HI*LIVETIME_MU2E/scale
    err_lo = math.sqrt(raw_count_lo)/LIVETIME_LO*LIVETIME_MU2E/scale
    err = math.sqrt(err_hi**2 + err_lo**2)

    return (ave, err, ave_hi, ave_lo, err_hi, err_lo)
  
def pritnLiveTimes():
    print("LIVETIME_MU2E: %e" % LIVETIME_MU2E)
    print("LIVETIME_HI: %e" % LIVETIME_HI)
    print("LIVETIME_LO: %e" % LIVETIME_LO)
    
def getVarList(list_name):
    list = 'N/A'
    if list_name=="all":
            list = {'crvinfo__x': [-8000, 1000], 
            'crvinfo__y': [0, 3500],
            'crvinfo__z': [-5000, 20000],
            'de_nhits': [-2, 100],
            'ue_nhits': [-2, 100],
            'dequal_TrkPID': [-1.1, 1.1],
            'dequal_TrkQual': [-0.1, 1.1],
            'deent_td': [0, 10],
            'deent_z0': [-500,500],
            'deent_d0': [-500,500],
            'deent_om': [-0.01, 0.05],
            'crvinfo__PEs': [-1, 1000],
            'crvinfo__dT': [-500, 500],
            'deent_mom': [50, 200],
            'deent_d0_om' : [300, 1200]}
        
    if list_name=="allCRY5":
            list = {'crvinfo_x': [-8000, 1000], 
            'crvinfo_y': [0, 3500],
            'crvinfo_z': [-5000, 20000],
            'de_nhits': [-2, 100],
            'ue_nhits': [-2, 100],
            'dequal_TrkPID': [-1.1, 1.1],
            'dequal_TrkQual': [-0.1, 1.1],
            'deent_td': [0, 10],
            'deent_d0': [-500,500],
            'deent_om': [-0.01, 0.05],
            'crvinfo__PEs': [-1, 1000],
            'crvinfo__dT': [-500, 500],
            'deent_mom': [50, 200],
            'deent_d0_om' : [300, 1200]}

    if list_name=="withCRV":
            list = {'crvinfo__z': [-5000, 20000],
            'crvinfo__PEs': [-1, 1000],
            'crvinfo__dT': [-500, 500],
            'de_nhits': [-2, 100],
            'ue_nhits': [-2, 100],
            'dequal_TrkPID': [-1.1, 1.1],
            'dequal_TrkQual': [-0.1, 1.1],
            'deent_td': [0, 10],
            'deent_z0': [-500,500]}

    if list_name=="noCRV":
            list = {'de_nhits': [-2, 100],
            'ue_nhits': [-2, 100],
            'dequal_TrkPID': [-1.1, 1.1],
            'dequal_TrkQual': [-0.1, 1.1],
            'deent_td': [0, 10],
            'deent_z0': [-500,500]}

    if list_name=="translate":
      list = {'crvinfo__x': "x position", 
              'crvinfo__y': "y position",
              'crvinfo__z': "z position",
              'de_nhits': "Downstream tracker hits",
              'ue_nhits': "Upstream tracker hits",
              'dequal_TrkPID': "Particle ID", 
              'dequal_TrkQual': "Track Quality",
              'deent_td': "Pitch Angle",
              'deent_z0': "z0 of track",
              'deent_d0': "distance from z axis",
              'deent_om': 'Min transverse radius',
              'crvinfo__PEs': "PE yield",
              'crvinfo__dT': "Delta-T = T_crv - T_tracker",
              'deent_mom': "Momentum",
              'deent_d0_om' : 'Max transverse radius',
              'is_cosmic':'cosmic status'}

    return list
