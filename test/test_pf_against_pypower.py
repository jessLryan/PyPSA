

import pypsa

from pypower.api import ppoption, runpf, case118 as case


import pandas as pd

import numpy as np




def test_pypower_case():

    #ppopt is a dictionary with the details of the optimization routine to run
    ppopt = ppoption(PF_ALG=2)

    #choose DC or AC
    ppopt["PF_DC"] = False

    #ppc is a dictionary with details about the network, including baseMVA, branches and generators
    ppc = case()

    results,success = runpf(ppc, ppopt)

    #store results in a DataFrame for easy access
    results_df = {}

    #branches
    columns = 'bus0, bus1, r, x, b, rateA, rateB, rateC, ratio, angle, status, angmin, angmax, p0, q0, p1, q1'.split(", ")
    results_df['branch'] = pd.DataFrame(data=results["branch"],columns=columns)

    #buses
    columns = ["bus","type","Pd","Qd","Gs","Bs","area","v_mag","v_ang","v_nom","zone","Vmax","Vmin"]
    results_df['bus'] = pd.DataFrame(data=results["bus"],columns=columns,index=results["bus"][:,0])

    #generators
    columns = "bus, p, q, q_max, q_min, Vg, mBase, status, p_max, p_min, Pc1, Pc2, Qc1min, Qc1max, Qc2min, Qc2max, ramp_agc, ramp_10, ramp_30, ramp_q, apf".split(", ")
    results_df['gen'] = pd.DataFrame(data=results["gen"],columns=columns)



    #now compute in PyPSA

    network = pypsa.Network()
    network.import_from_pypower_ppc(ppc)
    network.pf()



    #compare generator dispatch

    p_pypsa = network.generators.p.loc[network.now]
    p_pypower = results_df['gen']["p"]

    np.testing.assert_array_almost_equal(p_pypsa,p_pypower)


    #compare branch flows
    for item in ["lines","transformers"]:
        df = getattr(network,item)
        index = [int(i) for i in df.index]
        p0_pypsa = df.p0.loc[network.now].values
        p0_pypower = results_df['branch']["p0"][index].values

        np.testing.assert_array_almost_equal(p0_pypsa,p0_pypower)

    #compare voltages
    v_mag_pypsa = network.buses.v_mag.loc[network.now]
    v_mag_pypower = results_df["bus"]["v_mag"]

    np.testing.assert_array_almost_equal(v_mag_pypsa,v_mag_pypower)

    v_ang_pypsa = network.buses["v_ang"] = network.buses.v_ang.loc[network.now]
    pypower_slack_angle = results_df["bus"]["v_ang"][results_df["bus"]["type"] == 3].values[0]
    v_ang_pypower = (results_df["bus"]["v_ang"] - pypower_slack_angle)*np.pi/180.

    np.testing.assert_array_almost_equal(v_ang_pypsa,v_ang_pypower)