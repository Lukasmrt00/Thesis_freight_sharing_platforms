import time
import numpy as np
import math as mt
import csv


# Section 2: function definition
def scenario_determination(b, K, mu_d, stdev_d, scenario):
    input_par_list = [b[0], K[0], mu_d[0], stdev_d[0]]
    for i in range(len(scenario)):
        if input_par_list == scenario[i][0]:
            return scenario[i][1]


def capacity_utilization(order_size, truck_cap):
    capac_util = []
    numb_ftl = int(order_size // truck_cap)
    cap_util_ltl = (order_size / truck_cap) - numb_ftl
    if numb_ftl != 0:
        capac_util += [1] * numb_ftl
        capac_util.append(cap_util_ltl)
    else:
        capac_util.append(cap_util_ltl)
    return capac_util


def capacity_utilization_collab(order, truck_cap):
    cap_util = [[], []]
    numb_ftl_s1 = int(order[0] // truck_cap)
    cap_util_ltl_s1 = (order[0] / truck_cap) - numb_ftl_s1
    cap_util_collab = cap_util_ltl_s1 + (order[1] / truck_cap)
    if numb_ftl_s1 != 0:
        cap_util[0] += [1] * numb_ftl_s1
        for i in range(2):
            cap_util[i].append(cap_util_collab)
    else:
        for i in range(2):
            cap_util[i].append(cap_util_collab)
    return cap_util[0], cap_util[1]


def calculate_avg_capacity(cap_list):
    sum_cap_util = 0
    for i in range(0, len(cap_list)):
        sum_cap_util += cap_list[i]
    avg_cap_util = sum_cap_util/len(cap_list)
    return avg_cap_util


def excess_cap_calc(order, truck_cap):
    numb_ftl = int(order // truck_cap)
    cap_util_ltl = (order / truck_cap) - numb_ftl
    excess_cap = (1-cap_util_ltl) * truck_cap
    return excess_cap


def order_calc_shipper1(inv, s, S, numb_trucks, truck_cap):
    if inv <= s:
        order = S - inv
        numb_trucks += mt.ceil(order / truck_cap)
        excess_cap = excess_cap_calc(order, truck_cap)
    else:
        order = 0
        excess_cap = 0
    return order, numb_trucks, excess_cap


def order_calculation(inv, s, S, numb_trucks, truck_cap):
    if inv <= s:
        order = S - inv
        numb_trucks += mt.ceil(order / truck_cap)
    else:
        order = 0
    return order, numb_trucks


def cost_calculation(inv, temp_cost, order, h, b, K, numb_per_OoS, truck_cap):
    if inv > 0:
        temp_cost += (h * inv)
    else:
        temp_cost -= (b * inv)
        numb_per_OoS += 1

    if order > 0:
        temp_cost += K * mt.ceil(order/truck_cap)
    return temp_cost, numb_per_OoS


def cost_calc_collab_s1(inv, temp_cost, order, h, b, k, K, numb_per_OoS_s1, truck_cap):
    if inv > 0:
        temp_cost[0] += (h * inv)
    else:
        temp_cost[0] -= (b * inv)
        numb_per_OoS_s1 += 1

    if order > 0:
        temp_cost[0] += K * mt.ceil(order/truck_cap)
        temp_cost[1] += k
    return temp_cost, numb_per_OoS_s1


def sim_calculations(s1, S1, inv, h, b, k, K, mu_d, stdev_d, s, S, c, order, numb_trucks_s1, numb_trucks_s2_ind,
                     numb_trucks_s2_col, truck_cap, numb_per_OoS, cap_util, cost):
    for i in range(2):
        if i == 0:
            order[i], numb_trucks_s1, excess_cap = order_calc_shipper1(inv[i], s1, S1,
                                                                       numb_trucks_s1, truck_cap)
            if order[i] > 0:
                # Check acceptance requirements for collaborative shipping (according to (s,c,S) policy)
                if s < inv[1] <= c:
                    # Shipper 2 accepts the transport opportunity: collaborative shipping
                    order[1] = min(S - inv[1], excess_cap)
                    numb_trucks_s2_col += 1

                    # adjust inventory levels and report capacity utilization rates
                    for q in range(2):
                        inv[q] += order[q]
                        cap_util[q].extend(capacity_utilization_collab(order, truck_cap)[q])

                    # subtract demand of period t from inventory
                    inv[i] -= max(0, np.random.normal(mu_d[i], stdev_d[i]))
                    # cost calculation in the collaborative situation
                    cost, numb_per_OoS[0] = cost_calc_collab_s1(inv[0], cost, order[0], h[i], b[i],
                                                                k, K[i], numb_per_OoS[0], truck_cap)
                else:
                    # Shipper 2 does not accept the excess capacity
                    inv[0] += order[0]
                    cap_util[i].extend(capacity_utilization(order[i], truck_cap))

                    # subtract demand of period t from inventory
                    inv[i] -= max(0, np.random.normal(mu_d[i], stdev_d[i]))
                    # cost calculation for shipper 1 in non-collaborative situation
                    cost[i], numb_per_OoS[i] = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                                K[i], numb_per_OoS[i], truck_cap)

            else:
                # subtract demand of period t from inventory
                inv[i] -= max(0, np.random.normal(mu_d[i], stdev_d[i]))
                cost[i], numb_per_OoS[i] = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                            K[i], numb_per_OoS[i], truck_cap)
        # independent ordering for shipper 2
        else:
            order[i], numb_trucks_s2_ind = order_calculation(inv[i], s, S, numb_trucks_s2_ind, truck_cap)

            inv[i] += order[i]
            # subtract demand of period t from inventory
            inv[i] -= max(0, np.random.normal(mu_d[i], stdev_d[i]))
            if order[i] > 0:
                cap_util[i].extend(capacity_utilization(order[i], truck_cap))
            cost[i], numb_per_OoS[i] = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                        K[i], numb_per_OoS[i], truck_cap)

    return order, inv, numb_trucks_s1, numb_trucks_s2_ind, numb_trucks_s2_col, numb_per_OoS, cap_util, cost


# Section 3: simulation execution
def simulation(s1, S1, mu_d, stdev_d, h, k, p, K, b, truck_cap, rep):
    horizon = 1_000
    s_range = [i for i in range(0, 50)]
    S_max = 50
    best_s2 = 0
    best_S2 = 0
    best_c = 0
    best_cost = [999999999, 999999999]
    ass_numb_trucks_s1 = 0              # associated number of trucks for shipper 1
    ass_numb_trucks_s2_ind = 0          # associated number of trucks for shipper 2 (independently)
    ass_numb_trucks_s2_col = 0          # associated number of trucks for shipper 1 (collaborative shipping)
    ass_avg_cap_util = [0, 0]           # associated average capacity utilization
    ass_serv_lev = [0, 0]               # associated service level

    for s in s_range:
        for S in range(s, S_max + 1):
            for c in range(s+1, S):
                cost = [0, 0]
                order = [0, 0]
                numb_trucks_s1 = 0
                numb_trucks_s2_ind = 0
                numb_trucks_s2_col = 0
                numb_per_OoS = [0, 0]  # number of periods out of stock
                cap_util = [[], []]
                inv = [mu_d[0], mu_d[1]]
                for t in range(51):
                    order, inv, numb_trucks_s1, numb_trucks_s2_ind, numb_trucks_s2_col, numb_per_OoS, cap_util, cost = (
                        sim_calculations(s1, S1, inv, h, b, k, K, mu_d, stdev_d, s, S, c, order,
                                         numb_trucks_s1, numb_trucks_s2_ind, numb_trucks_s2_col, truck_cap,
                                         numb_per_OoS, cap_util, cost))
                    cost = [0, 0]

                for t in range(51, horizon):
                    order, inv, numb_trucks_s1, numb_trucks_s2_ind, numb_trucks_s2_col, numb_per_OoS, cap_util, cost = (
                        sim_calculations(s1, S1, inv, h, b, k, K, mu_d, stdev_d, s, S, c, order,
                                         numb_trucks_s1, numb_trucks_s2_ind, numb_trucks_s2_col, truck_cap,
                                         numb_per_OoS, cap_util, cost))

                    # stop simulation of this (s,S) configuration if no improvement w.r.t. current best
                    if cost[0] > best_cost[0] and cost[1] > best_cost[1]:
                        break

                for i in range(2):
                    if cost[i] < best_cost[i]:
                        # only change c for shipper 2 (cannot be changed for a better cost for S1)
                        if i == 0:
                            ass_numb_trucks_s1 = numb_trucks_s1
                        if i == 1:
                            best_s2 = s
                            best_S2 = S
                            best_c = c
                            ass_numb_trucks_s2_ind = numb_trucks_s2_ind
                            ass_numb_trucks_s2_col = numb_trucks_s2_col
                        best_cost[i] = round(cost[i], 2)
                        ass_avg_cap_util[i] = round(calculate_avg_capacity(cap_util[i]), 5)
                        ass_serv_lev[i] = round((1-(numb_per_OoS[i]/horizon)),4)

    for i in range(2):
        print("----- Shipper", i+1, "-----")
        if i == 0:
            print("Best value for s:", s1)
            print("Best value for S:", S1)
        else:
            print("Best value for s:", best_s2)
            print("Best value for S:", best_S2)
            print("Best value for c:", best_c)

        print("Corresponding cost", best_cost[i])
        if i == 0:
            print("Associated number of trucks needed:", ass_numb_trucks_s1)
        else:
            print("Associated number of trucks needed (independent shipping):", ass_numb_trucks_s2_ind)
            print("Associated number of trucks needed (collaborative shipping):", ass_numb_trucks_s2_col)
        print("Associated average utilization rate:", ass_avg_cap_util[i])
        print("Associated service level", ass_serv_lev[i])

    total_ass_numb_trucks = ass_numb_trucks_s1 + ass_numb_trucks_s2_ind
    total_avg_cap_util = round(0.5*(ass_avg_cap_util[0] + ass_avg_cap_util[1]), 5)

    print("----- Total -----")
    print("Total number of trucks needed:", total_ass_numb_trucks)
    print("Total average utilization rate", total_avg_cap_util)

    return [h, b[0], b[1], K[0], K[1], mu_d[0], mu_d[1], stdev_d[0], stdev_d[1], k, p, s1, S1, best_s2, best_S2, best_c,
            best_cost[0], best_cost[1], ass_numb_trucks_s1, ass_numb_trucks_s2_ind, ass_numb_trucks_s2_col,
            ass_avg_cap_util[0], ass_avg_cap_util[1], ass_serv_lev[0], ass_serv_lev[1], total_ass_numb_trucks,
            total_avg_cap_util, rep]


def main():
    h = [1, 1]  # holding cost per unit in inventory, per unit of time
    b = [19, 19]  # backlog cost per unit backlog (negative inventory), per unit of time
    K_values = [[25, 25], [50, 50], [100, 100]]  # fixed order cost per truck
    k_percent = [0.25, 0.50, 0.75]
    mu_d_values = [[10, 10], [20, 20], [30, 30]]  # mean demand (normal distribution)
    stdev_d_values = [[2, 2], [5, 5], [15, 15]]  # standard deviation demand (normal distribution)
    truck_cap = 33  # standard closed box trailers can fit 33 Euro-pallets
    counter = 0

    output = [["h", "b (S1)", "b (S2)", "K (S1)", "K (S2)",  "mu_d (S1)", "mu_d (S2)", "stdev_d (S1)", "stdev_d (S2)",
               "k (abs.)", "k (rel.)", "s1 (small)", "S1 (big)", "s2 (small)", "S2 (big)", "c", "Cost S1", "Cost S2",
               "# trucks S1", "# trucks S2 (ind)", "# trucks S2 (coll.)", "Avg. load factor S1",
               "Avg. load factor S2", "Service level S1", "Service level S2", "Total # trucks",
               "Total avg load factor", "Repetition"]]

    input_scenario_s1 = [[[5, 25, 10, 2], [6, 22]],
                         [[5, 25, 10, 5], [7, 25]],
                         [[5, 25, 10, 15], [13, 27]],
                         [[5, 25, 20, 2], [15, 22]],
                         [[5, 25, 20, 5], [17, 25]],
                         [[5, 25, 20, 15], [21, 36]],
                         [[5, 25, 30, 2], [21, 32]],
                         [[5, 25, 30, 5], [26, 34]],
                         [[5, 25, 30, 15], [30, 45]],
                         [[5, 50, 10, 2], [6, 28]],
                         [[5, 50, 10, 5], [6, 26]],
                         [[5, 50, 10, 15], [11, 30]],
                         [[5, 50, 20, 2], [16, 22]],
                         [[5, 50, 20, 5], [14, 26]],
                         [[5, 50, 20, 15], [18, 37]],
                         [[5, 50, 30, 2], [19, 32]],
                         [[5, 50, 30, 5], [26, 35]],
                         [[5, 50, 30, 15], [29, 46]],
                         [[5, 100, 10, 2], [6, 28]],
                         [[5, 100, 10, 5], [6, 26]],
                         [[5, 100, 10, 15], [9, 31]],
                         [[5, 100, 20, 2], [4, 50]],
                         [[5, 100, 20, 5], [6, 50]],
                         [[5, 100, 20, 15], [10, 46]],
                         [[5, 100, 30, 2], [23, 32]],
                         [[5, 100, 30, 5], [26, 35]],
                         [[5, 100, 30, 15], [24, 47]],
                         [[10, 25, 10, 2], [8, 23]],
                         [[10, 25, 10, 5], [10, 27]],
                         [[10, 25, 10, 15], [18, 33]],
                         [[10, 25, 20, 2], [16, 23]],
                         [[10, 25, 20, 5], [21, 26]],
                         [[10, 25, 20, 15], [27, 41]],
                         [[10, 25, 30, 2], [23, 33]],
                         [[10, 25, 30, 5], [28, 36]],
                         [[10, 25, 30, 15], [39, 48]],
                         [[10, 50, 10, 2], [8, 30]],
                         [[10, 50, 10, 5], [8, 29]],
                         [[10, 50, 10, 15], [16, 33]],
                         [[10, 50, 20, 2], [14, 23]],
                         [[10, 50, 20, 5], [17, 27]],
                         [[10, 50, 20, 15], [26, 42]],
                         [[10, 50, 30, 2], [21, 32]],
                         [[10, 50, 30, 5], [28, 36]],
                         [[10, 50, 30, 15], [33, 49]],
                         [[10, 100, 10, 2], [8, 30]],
                         [[10, 100, 10, 5], [10, 30]],
                         [[10, 100, 10, 15], [17, 37]],
                         [[10, 100, 20, 2], [16, 23]],
                         [[10, 100, 20, 5], [18, 33]],
                         [[10, 100, 20, 15], [24, 45]],
                         [[10, 100, 30, 2], [25, 33]],
                         [[10, 100, 30, 5], [29, 36]],
                         [[10, 100, 30, 15], [33, 49]],
                         [[19, 25, 10, 2], [9, 23]],
                         [[19, 25, 10, 5], [11, 29]],
                         [[19, 25, 10, 15], [23, 38]],
                         [[19, 25, 20, 2], [15, 23]],
                         [[19, 25, 20, 5], [22, 28]],
                         [[19, 25, 20, 15], [31, 44]],
                         [[19, 25, 30, 2], [21, 33]],
                         [[19, 25, 30, 5], [30, 38]],
                         [[19, 25, 30, 15], [42, 50]],
                         [[19, 50, 10, 2], [10, 31]],
                         [[19, 50, 10, 5], [11, 31]],
                         [[19, 50, 10, 15], [23, 39]],
                         [[19, 50, 20, 2], [16, 23]],
                         [[19, 50, 20, 5], [20, 29]],
                         [[19, 50, 20, 15], [30, 47]],
                         [[19, 50, 30, 2], [18, 33]],
                         [[19, 50, 30, 5], [27, 37]],
                         [[19, 50, 30, 15], [38, 49]],
                         [[19, 100, 10, 2], [9, 31]],
                         [[19, 100, 10, 5], [11, 32]],
                         [[19, 100, 10, 15], [22, 43]],
                         [[19, 100, 20, 2], [15, 23]],
                         [[19, 100, 20, 5], [19, 34]],
                         [[19, 100, 20, 15], [29, 48]],
                         [[19, 100, 30, 2], [24, 33]],
                         [[19, 100, 30, 5], [27, 38]],
                         [[19, 100, 30, 15], [36, 50]],
                         [[19, 25, 10, 2], [9, 24]],
                         [[19, 25, 10, 10], [17, 31]],
                         [[19, 25, 30, 2], [20, 33]],
                         [[19, 25, 30, 10], [37, 46]],
                         [[19, 75, 10, 2], [9, 31]],
                         [[19, 75, 10, 10], [16, 35]],
                         [[19, 75, 30, 2], [24, 33]],
                         [[19, 75, 30, 10], [32, 47]]]

    for rep in range(10, 11):
        print("\n------- New repetition -------")
        for K in K_values:
            for p in k_percent:
                k = p * K[0]
                for mu_d in mu_d_values:
                    for stdev_d in stdev_d_values:
                        print("\n------- New input values -------")
                        print("Repetition number: ", rep)
                        print("b: ", b, " - K: ", K, " - k: ", k, " - mu_d: ", mu_d, "stdev_d: ", stdev_d)
                        start_time = time.time()
                        s1, S1 = scenario_determination(b, K, mu_d, stdev_d, input_scenario_s1)
                        output.append(simulation(s1, S1, mu_d, stdev_d, h, k, p, K, b, truck_cap, rep))
                        end_time = time.time()
                        print("\nTime taken: ", end_time - start_time)
                        counter += 1
                        print("Counter: ", counter)

    # File path to write CSV data
    file_path = r'C:\Lukas_outputs\(s,c,S)_rep_10_SAME_PARAM_new_scen_b19.csv'

    # Writing data to CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(output)

    print("Data has been written to", file_path)


main()



