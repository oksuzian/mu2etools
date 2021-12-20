#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import pandas

class Utils:
  
  def __init__(self):
    self.LIVETIME_LO=1.36E8+5.09E7
    self.LIVETIME_HI=5.49E6 
    self.LIVETIME_MU2E=3.46E6  

  def getNormBackground(self, df, cuts, scale):

  # scale - to account for a larger momentum window 

    raw_count_hi = len(df.query('is_high==1 & %s' % cuts))
    raw_count_lo = len(df.query('is_high==0 & %s' % cuts))

    ave_hi = raw_count_hi/self.LIVETIME_HI*self.LIVETIME_MU2E/scale
    ave_lo = raw_count_lo/self.LIVETIME_LO*self.LIVETIME_MU2E/scale
    ave = ave_hi + ave_lo
  
    err_hi = math.sqrt(raw_count_hi)/self.LIVETIME_HI*self.LIVETIME_MU2E/scale
    err_lo = math.sqrt(raw_count_lo)/self.LIVETIME_LO*self.LIVETIME_MU2E/scale
    err = math.sqrt(err_hi**2 + err_lo**2)

    return (ave, err, ave_hi, ave_lo, err_hi, err_lo)
  
  def pritnLiveTimes(self):
    print("LIVETIME_MU2E: %e" % self.LIVETIME_MU2E)
    print("LIVETIME_HI: %e" % self.LIVETIME_HI)
    print("LIVETIME_LO: %e" % self.LIVETIME_LO)
    
  def getVarList(self, list_name):
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

    if list_name=="outDF":
      list = {'evtinfo__eventid',
              'evtinfo__runid',
              'evtinfo__subrunid',
              'de_status',
              'de_pdg',
              'de_nhits',
              'de_t0',
              'deent_mom',
              'deent_d0',
              'deent_p0',
              'deent_om',
              'deent_z0',
              'deent_td',
              'dequal_TrkPID',
              'dequal_TrkQual',
              'trigbits',
              'ue_status',
              'ue_nhits',
              'crvinfo__crvSectorType',
              'crvinfo__x',
              'crvinfo__y',
              'crvinfo__z',
              'crvinfo__PEs',
              'crvinfo__timeWindowStart',
              'crvinfo__nCoincidenceHits',
              'crvinfomc__x',
              'crvinfomc__y',
              'crvinfomc__z',
              'bestcrv',
              'is_high',
              'crvinfo__dT',
              'deent_d0_om',
              'is_triggered'}

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
