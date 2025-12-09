#!/usr/bin/env python

import os
try:
    __IPYTHON__
    import sys
    del sys.argv[1:]
except:
    pass

import srwpy.srwl_bl
import srwpy.srwlib
import srwpy.srwlpy
import math
import srwpy.srwl_uti_smp

def set_optics(v, names=None, want_final_propagation=True):
    el = []
    pp = []
    if not names:
        names = ['S1', 'S1_HCM', 'HCM', 'HCM_Before_DCM', 'DCM_C1', 'DCM_C2', 'After_DCM_HFM', 'HFM', 'HFM_VFM', 'VFM', 'VFM_VPM', 'VPM', 'After_VPM_Before_SSA', 'SSA', 'After_SSA_Before_VKB', 'VKB', 'After_VKB_Before_HKB', 'HKB', 'After_HKB_Focus']
    for el_name in names:
        if el_name == 'S1':
            # S1: aperture 26.62m
            el.append(srwpy.srwlib.SRWLOptA(
                _shape=v.op_S1_shape,
                _ap_or_ob='a',
                _Dx=v.op_S1_Dx,
                _Dy=v.op_S1_Dy,
                _x=v.op_S1_x,
                _y=v.op_S1_y,
            ))
            pp.append(v.op_S1_pp)
        elif el_name == 'S1_HCM':
            # S1_HCM: drift 26.62m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_S1_HCM_L,
            ))
            pp.append(v.op_S1_HCM_pp)
        elif el_name == 'HCM':
            # HCM: sphericalMirror 28.35m
            el.append(srwpy.srwlib.SRWLOptMirSph(
                _r=v.op_HCM_r,
                _size_tang=v.op_HCM_size_tang,
                _size_sag=v.op_HCM_size_sag,
                _nvx=v.op_HCM_nvx,
                _nvy=v.op_HCM_nvy,
                _nvz=v.op_HCM_nvz,
                _tvx=v.op_HCM_tvx,
                _tvy=v.op_HCM_tvy,
                _x=v.op_HCM_x,
                _y=v.op_HCM_y,
            ))
            pp.append(v.op_HCM_pp)

        elif el_name == 'HCM_Before_DCM':
            # HCM_Before_DCM: drift 28.35m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_HCM_Before_DCM_L,
            ))
            pp.append(v.op_HCM_Before_DCM_pp)
        elif el_name == 'DCM_C1':
            # DCM_C1: crystal 30.42m
            crystal = srwpy.srwlib.SRWLOptCryst(
                _d_sp=v.op_DCM_C1_d_sp,
                _psi0r=v.op_DCM_C1_psi0r,
                _psi0i=v.op_DCM_C1_psi0i,
                _psi_hr=v.op_DCM_C1_psiHr,
                _psi_hi=v.op_DCM_C1_psiHi,
                _psi_hbr=v.op_DCM_C1_psiHBr,
                _psi_hbi=v.op_DCM_C1_psiHBi,
                _tc=v.op_DCM_C1_tc,
                _ang_as=v.op_DCM_C1_ang_as,
                _nvx=v.op_DCM_C1_nvx,
                _nvy=v.op_DCM_C1_nvy,
                _nvz=v.op_DCM_C1_nvz,
                _tvx=v.op_DCM_C1_tvx,
                _tvy=v.op_DCM_C1_tvy,
                _uc=v.op_DCM_C1_uc,
                _e_avg=v.op_DCM_C1_energy,
                _ang_roll=v.op_DCM_C1_diffractionAngle
            )
            el.append(crystal)
            pp.append(v.op_DCM_C1_pp)

        elif el_name == 'DCM_C2':
            # DCM_C2: crystal 30.42m
            crystal = srwpy.srwlib.SRWLOptCryst(
                _d_sp=v.op_DCM_C2_d_sp,
                _psi0r=v.op_DCM_C2_psi0r,
                _psi0i=v.op_DCM_C2_psi0i,
                _psi_hr=v.op_DCM_C2_psiHr,
                _psi_hi=v.op_DCM_C2_psiHi,
                _psi_hbr=v.op_DCM_C2_psiHBr,
                _psi_hbi=v.op_DCM_C2_psiHBi,
                _tc=v.op_DCM_C2_tc,
                _ang_as=v.op_DCM_C2_ang_as,
                _nvx=v.op_DCM_C2_nvx,
                _nvy=v.op_DCM_C2_nvy,
                _nvz=v.op_DCM_C2_nvz,
                _tvx=v.op_DCM_C2_tvx,
                _tvy=v.op_DCM_C2_tvy,
                _uc=v.op_DCM_C2_uc,
                _e_avg=v.op_DCM_C2_energy,
                _ang_roll=v.op_DCM_C2_diffractionAngle
            )
            el.append(crystal)
            pp.append(v.op_DCM_C2_pp)

        elif el_name == 'After_DCM_HFM':
            # After_DCM_HFM: drift 30.42m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_After_DCM_HFM_L,
            ))
            pp.append(v.op_After_DCM_HFM_pp)
        elif el_name == 'HFM':
            # HFM: sphericalMirror 32.64m
            el.append(srwpy.srwlib.SRWLOptMirSph(
                _r=v.op_HFM_r,
                _size_tang=v.op_HFM_size_tang,
                _size_sag=v.op_HFM_size_sag,
                _nvx=v.op_HFM_nvx,
                _nvy=v.op_HFM_nvy,
                _nvz=v.op_HFM_nvz,
                _tvx=v.op_HFM_tvx,
                _tvy=v.op_HFM_tvy,
                _x=v.op_HFM_x,
                _y=v.op_HFM_y,
            ))
            pp.append(v.op_HFM_pp)

        elif el_name == 'HFM_VFM':
            # HFM_VFM: drift 32.64m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_HFM_VFM_L,
            ))
            pp.append(v.op_HFM_VFM_pp)
        elif el_name == 'VFM':
            # VFM: ellipsoidMirror 38.5m
            el.append(srwpy.srwlib.SRWLOptMirEl(
                _p=v.op_VFM_p,
                _q=v.op_VFM_q,
                _ang_graz=v.op_VFM_ang,
                _size_tang=v.op_VFM_size_tang,
                _size_sag=v.op_VFM_size_sag,
                _nvx=v.op_VFM_nvx,
                _nvy=v.op_VFM_nvy,
                _nvz=v.op_VFM_nvz,
                _tvx=v.op_VFM_tvx,
                _tvy=v.op_VFM_tvy,
                _x=v.op_VFM_x,
                _y=v.op_VFM_y,
            ))
            pp.append(v.op_VFM_pp)
            mirror_file = v.op_VFM_hfn
            assert os.path.isfile(mirror_file), \
                'Missing input file {}, required by VFM beamline element'.format(mirror_file)
            el.append(srwpy.srwlib.srwl_opt_setup_surf_height_1d(
                srwpy.srwlib.srwl_uti_read_data_cols(mirror_file, "\t", 0, 1),
                _dim=v.op_VFM_dim,
                _ang=abs(v.op_VFM_ang),
                _amp_coef=v.op_VFM_amp_coef,
            ))
            pp.append([0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])
        elif el_name == 'VFM_VPM':
            # VFM_VPM: drift 38.5m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_VFM_VPM_L,
            ))
            pp.append(v.op_VFM_VPM_pp)
        elif el_name == 'VPM':
            # VPM: mirror 39.5m
            mirror_file = v.op_VPM_hfn
            assert os.path.isfile(mirror_file), \
                'Missing input file {}, required by VPM beamline element'.format(mirror_file)
            el.append(srwpy.srwlib.srwl_opt_setup_surf_height_1d(
                srwpy.srwlib.srwl_uti_read_data_cols(mirror_file, "\t", 0, 1),
                _dim=v.op_VPM_dim,
                _ang=abs(v.op_VPM_ang),
                _amp_coef=v.op_VPM_amp_coef,
                _size_x=v.op_VPM_size_x,
                _size_y=v.op_VPM_size_y,
            ))
            pp.append(v.op_VPM_pp)
        elif el_name == 'After_VPM_Before_SSA':
            # After_VPM_Before_SSA: drift 39.5m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_After_VPM_Before_SSA_L,
            ))
            pp.append(v.op_After_VPM_Before_SSA_pp)
        elif el_name == 'SSA':
            # SSA: aperture 94.5m
            el.append(srwpy.srwlib.SRWLOptA(
                _shape=v.op_SSA_shape,
                _ap_or_ob='a',
                _Dx=v.op_SSA_Dx,
                _Dy=v.op_SSA_Dy,
                _x=v.op_SSA_x,
                _y=v.op_SSA_y,
            ))
            pp.append(v.op_SSA_pp)
        elif el_name == 'After_SSA_Before_VKB':
            # After_SSA_Before_VKB: drift 94.5m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_After_SSA_Before_VKB_L,
            ))
            pp.append(v.op_After_SSA_Before_VKB_pp)
        elif el_name == 'VKB':
            # VKB: ellipsoidMirror 108.9042143m
            el.append(srwpy.srwlib.SRWLOptMirEl(
                _p=v.op_VKB_p,
                _q=v.op_VKB_q,
                _ang_graz=v.op_VKB_ang,
                _size_tang=v.op_VKB_size_tang,
                _size_sag=v.op_VKB_size_sag,
                _nvx=v.op_VKB_nvx,
                _nvy=v.op_VKB_nvy,
                _nvz=v.op_VKB_nvz,
                _tvx=v.op_VKB_tvx,
                _tvy=v.op_VKB_tvy,
                _x=v.op_VKB_x,
                _y=v.op_VKB_y,
            ))
            pp.append(v.op_VKB_pp)

        elif el_name == 'After_VKB_Before_HKB':
            # After_VKB_Before_HKB: drift 108.9042143m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_After_VKB_Before_HKB_L,
            ))
            pp.append(v.op_After_VKB_Before_HKB_pp)
        elif el_name == 'HKB':
            # HKB: ellipsoidMirror 108.9660579m
            el.append(srwpy.srwlib.SRWLOptMirEl(
                _p=v.op_HKB_p,
                _q=v.op_HKB_q,
                _ang_graz=v.op_HKB_ang,
                _size_tang=v.op_HKB_size_tang,
                _size_sag=v.op_HKB_size_sag,
                _nvx=v.op_HKB_nvx,
                _nvy=v.op_HKB_nvy,
                _nvz=v.op_HKB_nvz,
                _tvx=v.op_HKB_tvx,
                _tvy=v.op_HKB_tvy,
                _x=v.op_HKB_x,
                _y=v.op_HKB_y,
            ))
            pp.append(v.op_HKB_pp)

        elif el_name == 'After_HKB_Focus':
            # After_HKB_Focus: drift 108.9660579m
            el.append(srwpy.srwlib.SRWLOptD(
                _L=v.op_After_HKB_Focus_L,
            ))
            pp.append(v.op_After_HKB_Focus_pp)
    if want_final_propagation:
        pp.append(v.op_fin_pp)

    return srwpy.srwlib.SRWLOptC(el, pp)



varParam = [
    ['name', 's', 'HXN Large Coupl. 12keV KB - SSA12x8', 'simulation name'],

#---Data Folder
    ['fdir', 's', 'HXN_Large_Coupl._12keV_KB_-_SSA12x8/', 'folder (directory) name for reading-in input and saving output data files'],

#---Electron Beam
    ['ebm_nm', 's', '', 'standard electron beam name'],
    ['ebm_nms', 's', '', 'standard electron beam name suffix: e.g. can be Day1, Final'],
    ['ebm_i', 'f', 0.5, 'electron beam current [A]'],
    ['ebm_e', 'f', 3.0, 'electron beam avarage energy [GeV]'],
    ['ebm_de', 'f', 0.0, 'electron beam average energy deviation [GeV]'],
    ['ebm_x', 'f', 0.0, 'electron beam initial average horizontal position [m]'],
    ['ebm_y', 'f', 0.0, 'electron beam initial average vertical position [m]'],
    ['ebm_xp', 'f', 0.0, 'electron beam initial average horizontal angle [rad]'],
    ['ebm_yp', 'f', 0.0, 'electron beam initial average vertical angle [rad]'],
    ['ebm_z', 'f', 0., 'electron beam initial average longitudinal position [m]'],
    ['ebm_dr', 'f', -1.8, 'electron beam longitudinal drift [m] to be performed before a required calculation'],
    ['ebm_ens', 'f', 0.00089, 'electron beam relative energy spread'],
    ['ebm_emx', 'f', 7.6e-10, 'electron beam horizontal emittance [m]'],
    ['ebm_emy', 'f', 3e-11, 'electron beam vertical emittance [m]'],
    # Definition of the beam through Twiss:
    ['ebm_betax', 'f', 1.84, 'horizontal beta-function [m]'],
    ['ebm_betay', 'f', 1.17, 'vertical beta-function [m]'],
    ['ebm_alphax', 'f', 0.0, 'horizontal alpha-function [rad]'],
    ['ebm_alphay', 'f', 0.0, 'vertical alpha-function [rad]'],
    ['ebm_etax', 'f', 0.0, 'horizontal dispersion function [m]'],
    ['ebm_etay', 'f', 0.0, 'vertical dispersion function [m]'],
    ['ebm_etaxp', 'f', 0.0, 'horizontal dispersion function derivative [rad]'],
    ['ebm_etayp', 'f', 0.0, 'vertical dispersion function derivative [rad]'],

#---Undulator
#---idealized params
    ['und_bx', 'f', 0.0, 'undulator horizontal peak magnetic field [T]'],
    ['und_by', 'f', 0.92478649, 'undulator vertical peak magnetic field [T]'],
    ['und_phx', 'f', 0.0, 'initial phase of the horizontal magnetic field [rad]'],
    ['und_phy', 'f', 0.0, 'initial phase of the vertical magnetic field [rad]'],
    ['und_sx', 'i', 1, 'undulator horizontal magnetic field symmetry vs longitudinal position'],
    ['und_sy', 'i', -1, 'undulator vertical magnetic field symmetry vs longitudinal position'],
    ['und_b2e', '', '', 'estimate undulator fundamental photon energy (in [eV]) for the amplitude of sinusoidal magnetic field defined by und_b or und_bx, und_by', 'store_true'],
    ['und_e2b', '', '', 'estimate undulator field amplitude (in [T]) for the photon energy defined by w_e', 'store_true'],
#---tabulated params
#    ['und_g', 'f', 5.9127, 'undulator gap [mm] (assumes availability of magnetic measurement or simulation data)'],
#    ['und_ph', 'f', 0.0, 'shift of magnet arrays [mm] for which the field should be set up'],
#    ['und_mfz', 's', 'magn_meas_u20_hxn.zip', 'name of zip-file of directory with magnetic measurement files for different gaps + summary file (if it is defined, it overrides the values of und_mdir and und_mfs)'],
#---both  params
    ['und_zc', 'f', 0.0, 'undulator center longitudinal position [m]'],
    ['und_per', 'f', 0.02, 'undulator period [m]'],
    ['und_len', 'f', 3.0, 'undulator length [m]'],



#---Calculation Types
    # Electron Trajectory
    ['tr', '', '', 'calculate electron trajectory', 'store_true'],
    ['tr_cti', 'f', 0.0, 'initial time moment (c*t) for electron trajectory calculation [m]'],
    ['tr_ctf', 'f', 0.0, 'final time moment (c*t) for electron trajectory calculation [m]'],
    ['tr_np', 'f', 10000, 'number of points for trajectory calculation'],
    ['tr_mag', 'i', 1, 'magnetic field to be used for trajectory calculation: 1- approximate, 2- accurate'],
    ['tr_fn', 's', 'res_trj.dat', 'file name for saving calculated trajectory data'],
    ['tr_pl', 's', '', 'plot the resulting trajectiry in graph(s): ""- dont plot, otherwise the string should list the trajectory components to plot'],

    #Single-Electron Spectrum vs Photon Energy
    ['ss', '', '', 'calculate single-e spectrum vs photon energy', 'store_true'],
    ['ss_ei', 'f', 10000.0, 'initial photon energy [eV] for single-e spectrum vs photon energy calculation'],
    ['ss_ef', 'f', 14000.0, 'final photon energy [eV] for single-e spectrum vs photon energy calculation'],
    ['ss_ne', 'i', 5000, 'number of points vs photon energy for single-e spectrum vs photon energy calculation'],
    ['ss_x', 'f', 0.0, 'horizontal position [m] for single-e spectrum vs photon energy calculation'],
    ['ss_y', 'f', 0.0, 'vertical position [m] for single-e spectrum vs photon energy calculation'],
    ['ss_meth', 'i', 1, 'method to use for single-e spectrum vs photon energy calculation: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"'],
    ['ss_prec', 'f', 0.01, 'relative precision for single-e spectrum vs photon energy calculation (nominal value is 0.01)'],
    ['ss_pol', 'i', 6, 'polarization component to extract after spectrum vs photon energy calculation: 0- Linear Horizontal, 1- Linear Vertical, 2- Linear 45 degrees, 3- Linear 135 degrees, 4- Circular Right, 5- Circular Left, 6- Total'],
    ['ss_mag', 'i', 1, 'magnetic field to be used for single-e spectrum vs photon energy calculation: 1- approximate, 2- accurate'],
    ['ss_ft', 's', 'f', 'presentation/domain: "f"- frequency (photon energy), "t"- time'],
    ['ss_u', 'i', 1, 'electric field units: 0- arbitrary, 1- sqrt(Phot/s/0.1%bw/mm^2), 2- sqrt(J/eV/mm^2) or sqrt(W/mm^2), depending on representation (freq. or time)'],
    ['ss_fn', 's', 'res_spec_se.dat', 'file name for saving calculated single-e spectrum vs photon energy'],
    ['ss_pl', 's', '', 'plot the resulting single-e spectrum in a graph: ""- dont plot, "e"- show plot vs photon energy'],

    #Multi-Electron Spectrum vs Photon Energy (taking into account e-beam emittance, energy spread and collection aperture size)
    ['sm', '', '', 'calculate multi-e spectrum vs photon energy', 'store_true'],
    ['sm_ei', 'f', 100.0, 'initial photon energy [eV] for multi-e spectrum vs photon energy calculation'],
    ['sm_ef', 'f', 20000.0, 'final photon energy [eV] for multi-e spectrum vs photon energy calculation'],
    ['sm_ne', 'i', 10000, 'number of points vs photon energy for multi-e spectrum vs photon energy calculation'],
    ['sm_x', 'f', 0.0, 'horizontal center position [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_rx', 'f', 0.0001, 'range of horizontal position / horizontal aperture size [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_nx', 'i', 1, 'number of points vs horizontal position for multi-e spectrum vs photon energy calculation'],
    ['sm_y', 'f', 0.0, 'vertical center position [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_ry', 'f', 0.0001, 'range of vertical position / vertical aperture size [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_ny', 'i', 1, 'number of points vs vertical position for multi-e spectrum vs photon energy calculation'],
    ['sm_mag', 'i', 1, 'magnetic field to be used for calculation of multi-e spectrum spectrum or intensity distribution: 1- approximate, 2- accurate'],
    ['sm_hi', 'i', 1, 'initial UR spectral harmonic to be taken into account for multi-e spectrum vs photon energy calculation'],
    ['sm_hf', 'i', 15, 'final UR spectral harmonic to be taken into account for multi-e spectrum vs photon energy calculation'],
    ['sm_prl', 'f', 1.0, 'longitudinal integration precision parameter for multi-e spectrum vs photon energy calculation'],
    ['sm_pra', 'f', 1.0, 'azimuthal integration precision parameter for multi-e spectrum vs photon energy calculation'],
    ['sm_meth', 'i', -1, 'method to use for spectrum vs photon energy calculation in case of arbitrary input magnetic field: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler", -1- dont use this accurate integration method (rather use approximate if possible)'],
    ['sm_prec', 'f', 0.01, 'relative precision for spectrum vs photon energy calculation in case of arbitrary input magnetic field (nominal value is 0.01)'],
    ['sm_nm', 'i', 1, 'number of macro-electrons for calculation of spectrum in case of arbitrary input magnetic field'],
    ['sm_na', 'i', 5, 'number of macro-electrons to average on each node at parallel (MPI-based) calculation of spectrum in case of arbitrary input magnetic field'],
    ['sm_ns', 'i', 5, 'saving periodicity (in terms of macro-electrons) for intermediate intensity at calculation of multi-electron spectrum in case of arbitrary input magnetic field'],
    ['sm_type', 'i', 2, 'calculate flux (=1) or flux per unit surface (=2)'],
    ['sm_pol', 'i', 6, 'polarization component to extract after calculation of multi-e flux or intensity: 0- Linear Horizontal, 1- Linear Vertical, 2- Linear 45 degrees, 3- Linear 135 degrees, 4- Circular Right, 5- Circular Left, 6- Total'],
    ['sm_rm', 'i', 1, 'method for generation of pseudo-random numbers for e-beam phase-space integration: 1- standard pseudo-random number generator, 2- Halton sequences, 3- LPtau sequences (to be implemented)'],
    ['sm_fn', 's', 'res_spec_me.dat', 'file name for saving calculated milti-e spectrum vs photon energy'],
    ['sm_pl', 's', '', 'plot the resulting spectrum-e spectrum in a graph: ""- dont plot, "e"- show plot vs photon energy'],
    #to add options for the multi-e calculation from "accurate" magnetic field

    #Power Density Distribution vs horizontal and vertical position
    ['pw', '', '', 'calculate SR power density distribution', 'store_true'],
    ['pw_x', 'f', 0.0, 'central horizontal position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_rx', 'f', 0.025, 'range of horizontal position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_nx', 'i', 100, 'number of points vs horizontal position for calculation of power density distribution'],
    ['pw_y', 'f', 0.0, 'central vertical position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_ry', 'f', 0.015, 'range of vertical position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_ny', 'i', 100, 'number of points vs vertical position for calculation of power density distribution'],
    ['pw_pr', 'f', 1.0, 'precision factor for calculation of power density distribution'],
    ['pw_meth', 'i', 1, 'power density computation method (1- "near field", 2- "far field")'],
    ['pw_zst', 'f', 0., 'initial longitudinal position along electron trajectory of power density distribution (effective if pow_sst < pow_sfi)'],
    ['pw_zfi', 'f', 0., 'final longitudinal position along electron trajectory of power density distribution (effective if pow_sst < pow_sfi)'],
    ['pw_mag', 'i', 1, 'magnetic field to be used for power density calculation: 1- approximate, 2- accurate'],
    ['pw_fn', 's', 'res_pow.dat', 'file name for saving calculated power density distribution'],
    ['pw_pl', 's', '', 'plot the resulting power density distribution in a graph: ""- dont plot, "x"- vs horizontal position, "y"- vs vertical position, "xy"- vs horizontal and vertical position'],

    #Single-Electron Intensity distribution vs horizontal and vertical position
    ['si', '', '', 'calculate single-e intensity distribution (without wavefront propagation through a beamline) vs horizontal and vertical position', 'store_true'],
    #Single-Electron Wavefront Propagation
    ['ws', '', '', 'calculate single-electron (/ fully coherent) wavefront propagation', 'store_true'],
    #Multi-Electron (partially-coherent) Wavefront Propagation
    ['wm', '', '', 'calculate multi-electron (/ partially coherent) wavefront propagation', 'store_true'],

    ['w_e', 'f', 11997.5, 'photon energy [eV] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ef', 'f', 12002.5, 'final photon energy [eV] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ne', 'i', 1, 'number of points vs photon energy for calculation of intensity distribution'],
    ['w_x', 'f', 0.0, 'central horizontal position [m] for calculation of intensity distribution'],
    ['w_rx', 'f', 0.0032, 'range of horizontal position [m] for calculation of intensity distribution'],
    ['w_nx', 'i', 200, 'number of points vs horizontal position for calculation of intensity distribution'],
    ['w_y', 'f', 0.0, 'central vertical position [m] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ry', 'f', 0.0015, 'range of vertical position [m] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ny', 'i', 100, 'number of points vs vertical position for calculation of intensity distribution'],
    ['w_smpf', 'f', 0.05, 'sampling factor for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_meth', 'i', 1, 'method to use for calculation of intensity distribution vs horizontal and vertical position: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"'],
    ['w_prec', 'f', 0.01, 'relative precision for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_mag', 'i', 1, 'magnetic field to be used for calculation of intensity distribution vs horizontal and vertical position: 1- approximate, 2- accurate'],
    ['w_u', 'i', 1, 'electric field units: 0- arbitrary, 1- sqrt(Phot/s/0.1%bw/mm^2), 2- sqrt(J/eV/mm^2) or sqrt(W/mm^2), depending on representation (freq. or time)'],

    ['si_pol', 'i', 6, 'polarization component to extract after calculation of intensity distribution: 0- Linear Horizontal, 1- Linear Vertical, 2- Linear 45 degrees, 3- Linear 135 degrees, 4- Circular Right, 5- Circular Left, 6- Total'],
    ['si_type', 'i', 0, 'type of a characteristic to be extracted after calculation of intensity distribution: 0- Single-Electron Intensity, 1- Multi-Electron Intensity, 2- Single-Electron Flux, 3- Multi-Electron Flux, 4- Single-Electron Radiation Phase, 5- Re(E): Real part of Single-Electron Electric Field, 6- Im(E): Imaginary part of Single-Electron Electric Field, 7- Single-Electron Intensity, integrated over Time or Photon Energy'],
    ['si_fn', 's', 'res_int_se.dat', 'file name for saving calculated single-e intensity distribution (without wavefront propagation through a beamline) vs horizontal and vertical position'],
    ['si_pl', 's', '', 'plot the input intensity distributions in graph(s): ""- dont plot, "x"- vs horizontal position, "y"- vs vertical position, "xy"- vs horizontal and vertical position'],
    ['ws_fni', 's', 'res_int_pr_se.dat', 'file name for saving propagated single-e intensity distribution vs horizontal and vertical position'],
    ['ws_pl', 's', '', 'plot the resulting intensity distributions in graph(s): ""- dont plot, "x"- vs horizontal position, "y"- vs vertical position, "xy"- vs horizontal and vertical position'],

    ['wm_nm', 'i', 100000, 'number of macro-electrons (coherent wavefronts) for calculation of multi-electron wavefront propagation'],
    ['wm_na', 'i', 10, 'number of macro-electrons (coherent wavefronts) to average on each node for parallel (MPI-based) calculation of multi-electron wavefront propagation'],
    ['wm_ns', 'i', 5, 'saving periodicity (in terms of macro-electrons / coherent wavefronts) for intermediate intensity at multi-electron wavefront propagation calculation'],
    ['wm_ch', 'i', 41, 'type of a characteristic to be extracted after calculation of multi-electron wavefront propagation: #0- intensity (s0); 1- four Stokes components; 2- mutual intensity cut vs x; 3- mutual intensity cut vs y; 40- intensity(s0), mutual intensity cuts and degree of coherence vs X & Y'],
    ['wm_ap', 'i', 0, 'switch specifying representation of the resulting Stokes parameters: coordinate (0) or angular (1)'],
    ['wm_x0', 'f', 0.0, 'horizontal center position for mutual intensity cut calculation'],
    ['wm_y0', 'f', 0.0, 'vertical center position for mutual intensity cut calculation'],
    ['wm_ei', 'i', 1, 'integration over photon energy is required (1) or not (0); if the integration is required, the limits are taken from w_e, w_ef'],
    ['wm_rm', 'i', 1, 'method for generation of pseudo-random numbers for e-beam phase-space integration: 1- standard pseudo-random number generator, 2- Halton sequences, 3- LPtau sequences (to be implemented)'],
    ['wm_am', 'i', 0, 'multi-electron integration approximation method: 0- no approximation (use the standard 5D integration method), 1- integrate numerically only over e-beam energy spread and use convolution to treat transverse emittance'],
    ['wm_fni', 's', 'res_int_pr_me.dat', 'file name for saving propagated multi-e intensity distribution vs horizontal and vertical position'],
    ['wm_ff', 's', 'ascii', 'format of file name for saving propagated multi-e intensity distribution vs horizontal and vertical position (ascii and hdf5 supported)'],


    ['wm_nmm', 'i', 1, 'number of MPI masters to use'],
    ['wm_ncm', 'i', 100, 'number of Coherent Modes to calculate'],
    ['wm_acm', 's', 'SP', 'coherent mode decomposition algorithm to be used (supported algorithms are: "SP" for SciPy, "SPS" for SciPy Sparse, "PM" for Primme, based on names of software packages)'],
    ['wm_nop', '', '', 'switch forcing to do calculations ignoring any optics defined (by set_optics function)', 'store_true'],

    ['wm_fnmi', 's', '', 'file name of input cross-spectral density / mutual intensity; if this file name is supplied, the initial cross-spectral density (for such operations as coherent mode decomposition) will not be calculated, but rathre it will be taken from that file.'],
    ['wm_fncm', 's', '', 'file name of input coherent modes; if this file name is supplied, the eventual partially-coherent radiation propagation simulation will be done based on propagation of the coherent modes from that file.'],

    ['wm_fbk', '', '', 'create backup file(s) with propagated multi-e intensity distribution vs horizontal and vertical position and other radiation characteristics', 'store_true'],

    # Optics parameters
    ['op_r', 'f', 26.62, 'longitudinal position of the first optical element [m]'],
    # Former appParam:
    ['rs_type', 's', 'u', 'source type, (u) idealized undulator, (t), tabulated undulator, (m) multipole, (g) gaussian beam'],

#---Beamline optics:
    # S1: aperture
    ['op_S1_shape', 's', 'r', 'shape'],
    ['op_S1_Dx', 'f', 0.0032, 'horizontalSize'],
    ['op_S1_Dy', 'f', 0.0015, 'verticalSize'],
    ['op_S1_x', 'f', 0.0, 'horizontalOffset'],
    ['op_S1_y', 'f', 0.0, 'verticalOffset'],

    # S1_HCM: drift
    ['op_S1_HCM_L', 'f', 1.7300000000000004, 'length'],

    # HCM: sphericalMirror
    ['op_HCM_hfn', 's', '', 'heightProfileFile'],
    ['op_HCM_dim', 's', 'x', 'orientation'],
    ['op_HCM_r', 'f', 17718.8, 'radius'],
    ['op_HCM_size_tang', 'f', 1.0, 'tangentialSize'],
    ['op_HCM_size_sag', 'f', 0.006, 'sagittalSize'],
    ['op_HCM_ang', 'f', 0.0032, 'grazingAngle'],
    ['op_HCM_nvx', 'f', 0.9999948800043691, 'normalVectorX'],
    ['op_HCM_nvy', 'f', 0.0, 'normalVectorY'],
    ['op_HCM_nvz', 'f', -0.003199994538669463, 'normalVectorZ'],
    ['op_HCM_tvx', 'f', 0.003199994538669463, 'tangentialVectorX'],
    ['op_HCM_tvy', 'f', 0.0, 'tangentialVectorY'],
    ['op_HCM_amp_coef', 'f', 1.0, 'heightAmplification'],
    ['op_HCM_x', 'f', 0.0, 'horizontalOffset'],
    ['op_HCM_y', 'f', 0.0, 'verticalOffset'],

    # HCM_Before_DCM: drift
    ['op_HCM_Before_DCM_L', 'f', 2.0700000000000003, 'length'],

    # DCM_C1: crystal
    ['op_DCM_C1_hfn', 's', '', 'heightProfileFile'],
    ['op_DCM_C1_dim', 's', 'x', 'orientation'],
    ['op_DCM_C1_d_sp', 'f', 3.1355713563754857, 'dSpacing'],
    ['op_DCM_C1_psi0r', 'f', -6.759642582545276e-06, 'psi0r'],
    ['op_DCM_C1_psi0i', 'f', 7.245217017493692e-08, 'psi0i'],
    ['op_DCM_C1_psiHr', 'f', -3.56789300932007e-06, 'psiHr'],
    ['op_DCM_C1_psiHi', 'f', 5.058419598704464e-08, 'psiHi'],
    ['op_DCM_C1_psiHBr', 'f', -3.56789300932007e-06, 'psiHBr'],
    ['op_DCM_C1_psiHBi', 'f', 5.058419598704464e-08, 'psiHBi'],
    ['op_DCM_C1_tc', 'f', 0.01, 'crystalThickness'],
    ['op_DCM_C1_uc', 'f', 1, 'useCase'],
    ['op_DCM_C1_ang_as', 'f', 0.0, 'asymmetryAngle'],
    ['op_DCM_C1_nvx', 'f', -0.9863311088533899, 'nvx'],
    ['op_DCM_C1_nvy', 'f', 6.702018003143382e-09, 'nvy'],
    ['op_DCM_C1_nvz', 'f', -0.16477543417646437, 'nvz'],
    ['op_DCM_C1_tvx', 'f', -0.16477543417646437, 'tvx'],
    ['op_DCM_C1_tvy', 'f', 1.119632055010627e-09, 'tvy'],
    ['op_DCM_C1_ang', 'f', 0.1655303290490928, 'grazingAngle'],
    ['op_DCM_C1_amp_coef', 'f', 1.0, 'heightAmplification'],
    ['op_DCM_C1_energy', 'f', 12000.0, 'energy'],
    ['op_DCM_C1_diffractionAngle', 'f', 1.57079632, 'diffractionAngle'],

    # DCM_C2: crystal
    ['op_DCM_C2_hfn', 's', '', 'heightProfileFile'],
    ['op_DCM_C2_dim', 's', 'x', 'orientation'],
    ['op_DCM_C2_d_sp', 'f', 3.1355713563754857, 'dSpacing'],
    ['op_DCM_C2_psi0r', 'f', -6.759642582545276e-06, 'psi0r'],
    ['op_DCM_C2_psi0i', 'f', 7.245217017493692e-08, 'psi0i'],
    ['op_DCM_C2_psiHr', 'f', -3.56789300932007e-06, 'psiHr'],
    ['op_DCM_C2_psiHi', 'f', 5.058419598704464e-08, 'psiHi'],
    ['op_DCM_C2_psiHBr', 'f', -3.56789300932007e-06, 'psiHBr'],
    ['op_DCM_C2_psiHBi', 'f', 5.058419598704464e-08, 'psiHBi'],
    ['op_DCM_C2_tc', 'f', 0.01, 'crystalThickness'],
    ['op_DCM_C2_uc', 'f', 1, 'useCase'],
    ['op_DCM_C2_ang_as', 'f', 0.0, 'asymmetryAngle'],
    ['op_DCM_C2_nvx', 'f', 0.9863311088533899, 'nvx'],
    ['op_DCM_C2_nvy', 'f', 6.702018003143382e-09, 'nvy'],
    ['op_DCM_C2_nvz', 'f', -0.16477543417646437, 'nvz'],
    ['op_DCM_C2_tvx', 'f', 0.16477543417646437, 'tvx'],
    ['op_DCM_C2_tvy', 'f', 1.119632055010627e-09, 'tvy'],
    ['op_DCM_C2_ang', 'f', 0.1655303290490928, 'grazingAngle'],
    ['op_DCM_C2_amp_coef', 'f', 1.0, 'heightAmplification'],
    ['op_DCM_C2_energy', 'f', 12000.0, 'energy'],
    ['op_DCM_C2_diffractionAngle', 'f', -1.57079632, 'diffractionAngle'],

    # After_DCM_HFM: drift
    ['op_After_DCM_HFM_L', 'f', 2.219999999999999, 'length'],

    # HFM: sphericalMirror
    ['op_HFM_hfn', 's', '', 'heightProfileFile'],
    ['op_HFM_dim', 's', 'x', 'orientation'],
    ['op_HFM_r', 'f', 38660.0, 'radius'],
    ['op_HFM_size_tang', 'f', 1.0, 'tangentialSize'],
    ['op_HFM_size_sag', 'f', 0.06, 'sagittalSize'],
    ['op_HFM_ang', 'f', 0.0032, 'grazingAngle'],
    ['op_HFM_nvx', 'f', -0.9999948800043691, 'normalVectorX'],
    ['op_HFM_nvy', 'f', 0.0, 'normalVectorY'],
    ['op_HFM_nvz', 'f', -0.003199994538669463, 'normalVectorZ'],
    ['op_HFM_tvx', 'f', -0.003199994538669463, 'tangentialVectorX'],
    ['op_HFM_tvy', 'f', 0.0, 'tangentialVectorY'],
    ['op_HFM_amp_coef', 'f', 1.0, 'heightAmplification'],
    ['op_HFM_x', 'f', 0.0, 'horizontalOffset'],
    ['op_HFM_y', 'f', 0.0, 'verticalOffset'],

    # HFM_VFM: drift
    ['op_HFM_VFM_L', 'f', 5.859999999999999, 'length'],

    # VFM: ellipsoidMirror
    ['op_VFM_hfn', 's', 'HXN_Large_Coupl._12keV_KB_-_SSA12x8/hxn_vfm_figure_error_1207.dat', 'heightProfileFile'],
    ['op_VFM_dim', 's', 'y', 'orientation'],
    ['op_VFM_p', 'f', 38.5, 'firstFocusLength'],
    ['op_VFM_q', 'f', 56.0, 'focalLength'],
    ['op_VFM_ang', 'f', 0.003, 'grazingAngle'],
    ['op_VFM_amp_coef', 'f', 2.0, 'heightAmplification'],
    ['op_VFM_size_tang', 'f', 0.45, 'tangentialSize'],
    ['op_VFM_size_sag', 'f', 0.01, 'sagittalSize'],
    ['op_VFM_nvx', 'f', 0.0, 'normalVectorX'],
    ['op_VFM_nvy', 'f', 0.999995500003375, 'normalVectorY'],
    ['op_VFM_nvz', 'f', -0.002999995500002025, 'normalVectorZ'],
    ['op_VFM_tvx', 'f', 0.0, 'tangentialVectorX'],
    ['op_VFM_tvy', 'f', 0.002999995500002025, 'tangentialVectorY'],
    ['op_VFM_x', 'f', 0.0, 'horizontalOffset'],
    ['op_VFM_y', 'f', 0.0, 'verticalOffset'],

    # VFM_VPM: drift
    ['op_VFM_VPM_L', 'f', 1.0, 'length'],

    # VPM: mirror
    ['op_VPM_hfn', 's', 'HXN_Large_Coupl._12keV_KB_-_SSA12x8/mirror_1d.dat', 'heightProfileFile'],
    ['op_VPM_dim', 's', 'y', 'orientation'],
    ['op_VPM_ang', 'f', 0.003, 'grazingAngle'],
    ['op_VPM_amp_coef', 'f', 0.0, 'heightAmplification'],
    ['op_VPM_size_x', 'f', 0.001, 'horizontalTransverseSize'],
    ['op_VPM_size_y', 'f', 0.001, 'verticalTransverseSize'],

    # After_VPM_Before_SSA: drift
    ['op_After_VPM_Before_SSA_L', 'f', 55.0, 'length'],

    # SSA: aperture
    ['op_SSA_shape', 's', 'r', 'shape'],
    ['op_SSA_Dx', 'f', 1.2e-05, 'horizontalSize'],
    ['op_SSA_Dy', 'f', 8e-06, 'verticalSize'],
    ['op_SSA_x', 'f', 0.0, 'horizontalOffset'],
    ['op_SSA_y', 'f', 0.0, 'verticalOffset'],

    # After_SSA_Before_VKB: drift
    ['op_After_SSA_Before_VKB_L', 'f', 14.404214300000007, 'length'],

    # VKB: ellipsoidMirror
    ['op_VKB_hfn', 's', '', 'heightProfileFile'],
    ['op_VKB_dim', 's', 'y', 'orientation'],
    ['op_VKB_p', 'f', 14.4042143, 'firstFocusLength'],
    ['op_VKB_q', 'f', 0.0957882, 'focalLength'],
    ['op_VKB_ang', 'f', 0.0033, 'grazingAngle'],
    ['op_VKB_amp_coef', 'f', 1.0, 'heightAmplification'],
    ['op_VKB_size_tang', 'f', 0.0616, 'tangentialSize'],
    ['op_VKB_size_sag', 'f', 0.01, 'sagittalSize'],
    ['op_VKB_nvx', 'f', 0.0, 'normalVectorX'],
    ['op_VKB_nvy', 'f', 0.9999945550049414, 'normalVectorY'],
    ['op_VKB_nvz', 'f', -0.003299994010503261, 'normalVectorZ'],
    ['op_VKB_tvx', 'f', 0.0, 'tangentialVectorX'],
    ['op_VKB_tvy', 'f', 0.003299994010503261, 'tangentialVectorY'],
    ['op_VKB_x', 'f', 0.0, 'horizontalOffset'],
    ['op_VKB_y', 'f', 0.0, 'verticalOffset'],

    # After_VKB_Before_HKB: drift
    ['op_After_VKB_Before_HKB_L', 'f', 0.061843599999988896, 'length'],

    # HKB: ellipsoidMirror
    ['op_HKB_hfn', 's', '', 'heightProfileFile'],
    ['op_HKB_dim', 's', 'x', 'orientation'],
    ['op_HKB_p', 'f', 14.4660579, 'firstFocusLength'],
    ['op_HKB_q', 'f', 0.0339446, 'focalLength'],
    ['op_HKB_ang', 'f', 0.0024, 'grazingAngle'],
    ['op_HKB_amp_coef', 'f', 1.0, 'heightAmplification'],
    ['op_HKB_size_tang', 'f', 0.0439, 'tangentialSize'],
    ['op_HKB_size_sag', 'f', 0.01, 'sagittalSize'],
    ['op_HKB_nvx', 'f', 0.9999971200013824, 'normalVectorX'],
    ['op_HKB_nvy', 'f', 0.0, 'normalVectorY'],
    ['op_HKB_nvz', 'f', -0.0023999976960006634, 'normalVectorZ'],
    ['op_HKB_tvx', 'f', -0.0023999976960006634, 'tangentialVectorX'],
    ['op_HKB_tvy', 'f', 0.0, 'tangentialVectorY'],
    ['op_HKB_x', 'f', 0.0, 'horizontalOffset'],
    ['op_HKB_y', 'f', 0.0, 'verticalOffset'],

    # After_HKB_Focus: drift
    ['op_After_HKB_Focus_L', 'f', 0.033944599999998104, 'length'],

#---Propagation parameters
    ['op_S1_pp', 'f',                   [0, 0, 1.0, 0, 0, 1.2, 5.0, 1.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'S1'],
    ['op_S1_HCM_pp', 'f',               [0, 0, 1.0, 1, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'S1_HCM'],
    ['op_HCM_pp', 'f',                  [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'HCM'],
    ['op_HCM_Before_DCM_pp', 'f',       [0, 0, 1.0, 1, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'HCM_Before_DCM'],
    ['op_DCM_C1_pp', 'f',               [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, -0.32504627340614156, 2.208655852652862e-09, 0.9456981125839153, 0.9456981125839153, 3.689757159645261e-10], 'DCM_C1'],
    ['op_DCM_C2_pp', 'f',               [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.32504627340614156, 2.208655852652862e-09, 0.9456981125839153, 0.9456981125839153, -3.689757159645261e-10], 'DCM_C2'],
    ['op_After_DCM_HFM_pp', 'f',        [0, 0, 1.0, 1, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'After_DCM_HFM'],
    ['op_HFM_pp', 'f',                  [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'HFM'],
    ['op_HFM_VFM_pp', 'f',              [0, 0, 1.0, 1, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'HFM_VFM'],
    ['op_VFM_pp', 'f',                  [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'VFM'],
    ['op_VFM_VPM_pp', 'f',              [0, 0, 1.0, 1, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'VFM_VPM'],
    ['op_VPM_pp', 'f',                  [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'VPM'],
    ['op_After_VPM_Before_SSA_pp', 'f', [0, 0, 1.0, 4, 0, 4.0, 0.1, 4.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'After_VPM_Before_SSA'],
    ['op_SSA_pp', 'f',                  [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'SSA'],
    ['op_After_SSA_Before_VKB_pp', 'f', [0, 0, 1.0, 3, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'After_SSA_Before_VKB'],
    ['op_VKB_pp', 'f',                  [0, 0, 1.0, 0, 0, 0.33, 2.0, 0.62, 1.45, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'VKB'],
    ['op_After_VKB_Before_HKB_pp', 'f', [0, 0, 1.0, 1, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'After_VKB_Before_HKB'],
    ['op_HKB_pp', 'f',                  [0, 0, 1.0, 0, 0, 1.7, 1.176, 5.0, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'HKB'],
    ['op_After_HKB_Focus_pp', 'f',      [0, 0, 1.0, 4, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'After_HKB_Focus'],
    ['op_fin_pp', 'f',                  [0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'final post-propagation (resize) parameters'],

    #[ 0]: Auto-Resize (1) or not (0) Before propagation
    #[ 1]: Auto-Resize (1) or not (0) After propagation
    #[ 2]: Relative Precision for propagation with Auto-Resizing (1. is nominal)
    #[ 3]: Allow (1) or not (0) for semi-analytical treatment of the quadratic (leading) phase terms at the propagation
    #[ 4]: Do any Resizing on Fourier side, using FFT, (1) or not (0)
    #[ 5]: Horizontal Range modification factor at Resizing (1. means no modification)
    #[ 6]: Horizontal Resolution modification factor at Resizing
    #[ 7]: Vertical Range modification factor at Resizing
    #[ 8]: Vertical Resolution modification factor at Resizing
    #[ 9]: Type of wavefront Shift before Resizing (not yet implemented)
    #[10]: New Horizontal wavefront Center position after Shift (not yet implemented)
    #[11]: New Vertical wavefront Center position after Shift (not yet implemented)
    #[12]: Optional: Orientation of the Output Optical Axis vector in the Incident Beam Frame: Horizontal Coordinate
    #[13]: Optional: Orientation of the Output Optical Axis vector in the Incident Beam Frame: Vertical Coordinate
    #[14]: Optional: Orientation of the Output Optical Axis vector in the Incident Beam Frame: Longitudinal Coordinate
    #[15]: Optional: Orientation of the Horizontal Base vector of the Output Frame in the Incident Beam Frame: Horizontal Coordinate
    #[16]: Optional: Orientation of the Horizontal Base vector of the Output Frame in the Incident Beam Frame: Vertical Coordinate
]


def epilogue():
    pass


def main():
    v = srwpy.srwl_bl.srwl_uti_parse_options(srwpy.srwl_bl.srwl_uti_ext_options(varParam), use_sys_argv=True)
    names = ['S1','S1_HCM','HCM','HCM_Before_DCM','DCM_C1','DCM_C2','After_DCM_HFM','HFM','HFM_VFM','VFM','VFM_VPM','VPM','After_VPM_Before_SSA','SSA','After_SSA_Before_VKB','VKB','After_VKB_Before_HKB','HKB','After_HKB_Focus']
    op = set_optics(v, names, True)
    v.wm = True
    srwpy.srwl_bl.SRWLBeamline(_name=v.name).calc_all(v, op)

main()

epilogue()
