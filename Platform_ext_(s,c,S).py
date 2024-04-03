import time
import numpy as np
import math as mt
import csv


# Section 2: function definition
def scenario_determination(K, mu_d, stdev_d, scenario):
    input_par_list = [K[0], mu_d[0], stdev_d[0]]
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


def sim_calculations(s1, S1, inv, h, b, k, K, mu_d, stdev_d, s, S, c, order, numb_trucks, truck_cap, numb_per_OoS, cap_util, cost, cost_after):
    for i in range(2):
        if i == 0:
            order[i], numb_trucks[i], excess_cap = order_calc_shipper1(inv[i], s1, S1,
                                                                       numb_trucks[i], truck_cap)
            if order[i] > 0:
                # Shipper 2 accepts the transport opportunity: collaborative shipping
                if s < inv[1] <= c:
                    order[1] = min(S - inv[1], excess_cap)
                    # cost calculation in the collaborative situation
                    cost, numb_per_OoS[0] = cost_calc_collab_s1(inv[0], cost, order[0], h[i], b[i],
                                                                k, K[i], numb_per_OoS[0], truck_cap)
                    # adjust inventory levels and report capacity utilization rates
                    for q in range(2):
                        inv[q] += order[q]
                        cap_util[q].extend(capacity_utilization_collab(order, truck_cap)[q])

                    cost_after, _ = cost_calc_collab_s1(inv[0], cost, order[0], h[i], b[i],
                                                                k, K[i], numb_per_OoS[0], truck_cap)
                # Shipper 2 does not accept the excess capacity
                else:
                    cost[i], numb_per_OoS[i] = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                                K[i], numb_per_OoS[i], truck_cap)
                    inv[0] += order[0]
                    cap_util[i].extend(capacity_utilization(order[i], truck_cap))

                    cost_after[i], _ = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                                K[i], numb_per_OoS[i], truck_cap)
            else:
                cost[i], numb_per_OoS[i] = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                            K[i], numb_per_OoS[i], truck_cap)

        else:
            order[i], numb_trucks[i] = order_calculation(inv[i], s, S, numb_trucks[i], truck_cap)
            cost[i], numb_per_OoS[i] = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                        K[i], numb_per_OoS[i], truck_cap)
            inv[i] += order[i]
            if order[i] > 0:
                cap_util[i].extend(capacity_utilization(order[i], truck_cap))

            cost_after[i], _ = cost_calculation(inv[i], cost[i], order[i], h[i], b[i],
                                                                K[i], numb_per_OoS[i], truck_cap)

        inv[i] -= max(0, np.random.normal(mu_d[i], stdev_d[i]))

    return order, inv, numb_trucks, numb_per_OoS, cap_util, cost, cost_after


# Section 3: simulation execution
def simulation(mu_d, stdev_d, h, k, K, b, truck_cap, rep):
    input_scenario_S1 = [[[25, 10, 2], [9, 23]],
                         [[25, 10, 5], [12, 29]],
                         [[25, 10, 15], [25, 36]],
                         [[25, 20, 2], [14,23]],
                         [[25, 20, 5], [23, 28]],
                         [[25, 20, 15], [32, 46]],
                         [[25, 30, 2], [18, 33]],
                         [[25, 30, 5], [29, 38]],
                         [[25, 30, 15], [39, 50]],
                         [[50, 10, 2], [9, 31]],
                         [[50, 10, 5], [12, 31]],
                         [[50, 10, 15], [21, 40]],
                         [[50, 20, 2], [15, 23]],
                         [[50, 20, 5], [22, 29]],
                         [[50, 20, 15], [32, 47]],
                         [[50, 30, 2], [20, 33]],
                         [[50, 30, 5], [28, 38]],
                         [[50, 30, 15], [42, 50]],
                         [[100, 10, 2], [10, 32]],
                         [[100, 10, 5], [11, 32]],
                         [[100, 10, 15], [22, 40]],
                         [[100, 20, 2], [15, 23]],
                         [[100, 20, 5], [19, 34]],
                         [[100, 20, 15], [29, 49]],
                         [[100, 30, 2], [25, 33]],
                         [[100, 30, 5], [29, 39]],
                         [[100, 30, 15], [34, 49]]]
    s1, S1 = scenario_determination(K, mu_d, stdev_d, input_scenario_S1)
    horizon = 1_000
    s_range = [i for i in range(-5, 50)]
    S_max = 50
    best_s2 = 0
    best_S2 = 0
    best_c = 0
    best_cost = [999999999, 999999999]
    best_cost_after = [999999999, 999999999]
    ass_numb_trucks = [0, 0]  # associated number of trucks
    ass_avg_cap_util = [0, 0]  # associated average capacity utilization
    ass_serv_lev = [0, 0]  # associated service level

    for s in s_range:
        for S in range(s, S_max + 1):
            for c in range(s+1, S):
                cost = [0, 0]
                cost_after = [0, 0]
                order = [0, 0]
                numb_trucks = [0, 0]
                numb_per_OoS = [0, 0]  # number of periods out of stock
                cap_util = [[], []]
                inv = [mu_d[0], mu_d[1]]
                for t in range(51):
                    order, inv, numb_trucks, numb_per_OoS, cap_util, cost, cost_after = (
                        sim_calculations(s1, S1, inv, h, b, k, K, mu_d, stdev_d, s, S, c, order,
                                         numb_trucks, truck_cap, numb_per_OoS, cap_util, cost, cost_after))

                    cost = [0, 0]
                    cost_after = [0, 0]

                for t in range(51, horizon):
                    order, inv, numb_trucks, numb_per_OoS, cap_util, cost, cost_after = (
                        sim_calculations(s1, S1, inv, h, b, k, K, mu_d, stdev_d, s, S, c, order,
                                         numb_trucks, truck_cap, numb_per_OoS, cap_util, cost, cost_after))

                    # stop simulation of this (s,S) configuration if no improvement w.r.t. current best
                    if cost[0] > best_cost[0] and cost[1] > best_cost[1]:
                        break

                for i in range(2):
                    if cost[i] < best_cost[i]:
                        # only change c for shipper 2 (cannot be changed for a better cost for S1)
                        if i == 1:
                            best_s2 = s
                            best_S2 = S
                            best_c = c
                        best_cost[i] = round(cost[i], 5)
                        best_cost_after[i] = round(cost_after[i], 5)
                        ass_numb_trucks[i] = numb_trucks[i]
                        ass_avg_cap_util[i] = round(calculate_avg_capacity(cap_util[i]), 5)
                        ass_serv_lev[i] = 1-(numb_per_OoS[i]/horizon)

    for i in range(2):
        print("----- Shipper", i+1, "-----")
        if i == 0:
            print("Best value for s:", s1)
            print("Best value for S:", S1)
        else:
            print("Best value for s:", best_s2)
            print("Best value for S:", best_S2)
            print("Best value for c:", best_c)

        print("Corresponding cost BEFORE order added to inv", best_cost[i])
        print("Corresponding cost AFTER order added to inv", best_cost_after)
        print("Associated number of trucks needed:", ass_numb_trucks[i])
        print("Associated average utilization rate:", ass_avg_cap_util[i])
        print("Associated service level", ass_serv_lev[i])

    total_ass_numb_trucks = ass_numb_trucks[0]+ass_numb_trucks[1]
    total_avg_cap_util = round(0.5*(ass_avg_cap_util[0]+ass_avg_cap_util[1]), 5)

    print("----- Total -----")
    print("Total number of trucks needed:", total_ass_numb_trucks)
    print("Total average utilization rate", total_avg_cap_util)

    return [h, b, K, k, mu_d, stdev_d, s1, S1, best_s2, best_S2, best_c, best_cost[0], best_cost[1],
            ass_numb_trucks[0], ass_numb_trucks[1], ass_avg_cap_util[0], ass_avg_cap_util[1], ass_serv_lev[0],
            ass_serv_lev[1], total_ass_numb_trucks, total_avg_cap_util, rep]


def main():
    h = [1, 1]  # holding cost per unit in inventory, per unit of time
    b_values = [19, 19]  # backlog cost per unit backlog (negative inventory), per unit of time
    K_values = [[25, 25], [50, 50], [100, 100]]  # fixed order cost per truck
    k_percent = [0.25, 0.50, 0.75]
    mu_d_values = [[10, 10], [20, 20], [30, 30]]  # mean demand (normal distribution)
    stdev_d_values = [[2, 2], [5, 5], [15, 15]]  # standard deviation demand (normal distribution)
    truck_cap = 33  # standard closed box trailers can fit 33 europallets
    counter = 0

    output = [["h", "b", "K", "k", "mu_d", "stdev_d", "s-value S1", "S-value S1", "s-value S2", "S-value S2",
               "Corresponding c value", "Corresponding cost S1", "Corresponding cost S2", "# trucks needed S1",
               "# trucks needed S2", "Avg. capacity utilization S1", "Avg. capacity utilization S2", "Service level S1",
               "Service level S2", "Total ass # trucks", "Total avg cap util", "Repetition"]]

    for rep in range(1, 2):
        print("\n------- New repetition -------")
        for K in K_values:
            for p in k_percent:
                k = p * K[0]
                for mu_d in mu_d_values:
                    for stdev_d in stdev_d_values:
                        print("\n------- New input values -------")
                        print("Repetition number: ", rep)
                        print("K: ", K, " - k: ", k, " - mu_d: ", mu_d, "stdev_d: ", stdev_d)
                        start_time = time.time()
                        output.append(simulation(mu_d, stdev_d, h, k, K, b_values, truck_cap, rep))
                        end_time = time.time()
                        print("\nTime taken: ", end_time - start_time)
                        counter += 1
                        print("Counter: ", counter)

    # File path to write CSV data
    file_path = r'C:\Users\lukas\PycharmProjects\Thesis_freight_sharing_platforms\Output files\extension_(s,c,S)_1_reps_adj.csv'

    # Writing data to CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(output)

    print("Data has been written to", file_path)


main()



