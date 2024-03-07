import numpy as np
import math as mt


# Section 2: function definition
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


def calculate_avg_capacity(cap_list):
    sum_cap_util = 0
    for i in range(0, len(cap_list)):
        sum_cap_util += cap_list[i]
    avg_cap_util = sum_cap_util/len(cap_list)
    return avg_cap_util


def order_calculation(inv, s, S, numb_trucks, truck_cap):
    if inv <= s:
        order = S - inv
        # print(s,",",S,": Order ",order, " units")
        numb_trucks += mt.ceil(order / truck_cap)
    else:
        order = 0
    return order, numb_trucks


def cost_calculation(inv, cost, order, h, b, K, numb_per_OoS):
    if inv > 0:
        cost += (h * inv)
    else:
        cost -= (b * inv)
        numb_per_OoS += 1

    if order > 0:
        cost += K
    return cost, numb_per_OoS


# Section 3: simulation execution
def simulation(mu_d, stdev_d, h, K, b, truck_cap):
    horizon = 1_000
    s_range = [i for i in range(-20, 50)]
    S_max = 50
    best_s = [0, 0, 0]
    best_S = [0, 0, 0]
    best_cost = [0, 999999999, 999999999]
    ass_numb_trucks = [0, 0, 0]  # associated number of trucks
    ass_avg_cap_util = [0, 0, 0]  # associated average capacity utilization
    ass_serv_lev = [0, 0, 0]  # associated service level

    for s in s_range:
        for S in range(s, S_max + 1):
            cost = [0, 0, 0]
            order = [0, 0, 0]
            numb_trucks = [0, 0, 0]
            numb_per_OoS = [0, 0, 0]    # number of periods out of stock
            cap_util = [0, [], []]
            inv = [0, mu_d[1], mu_d[2]]

            for t in range(horizon):
                # calculate order and the number of corresponding trucks
                for i in range(1, 3):
                    order[i], numb_trucks[i] = order_calculation(inv[i], s, S, numb_trucks[i], truck_cap)

                    # Add capacity utilization rate(s) to list
                    if order[i] > 0:
                        cap_util[i].extend(capacity_utilization(order[i],truck_cap))

                    # Add order and subtract demand
                    inv[i] += order[i]
                    inv[i] -= max(0, np.random.normal(mu_d[i], stdev_d[i]))

                    # calculate costs
                    cost[i], numb_per_OoS[i] = cost_calculation(inv[i], cost[i], order[i], h[i], b[i], K[i], numb_per_OoS[i])

                    # stop simulation of this (s,S) configuration if no improvement w.r.t. current best
                    if cost[1] > best_cost[1] and cost[2] > best_cost[2]:
                        break

            for i in range(1, 3):
                if cost[i] < best_cost[i]:
                    best_s[i] = s
                    best_S[i] = S
                    best_cost[i] = cost[i]
                    ass_numb_trucks[i] = numb_trucks[i]
                    ass_avg_cap_util[i] = calculate_avg_capacity(cap_util[i])
                    ass_serv_lev[i] = 1-(numb_per_OoS[i]/horizon)

    for i in range(1,3):
        print("----- Shipper", i, "-----")
        print("Best value for s:", best_s[i])
        print("Best value for S:", best_S[i])
        print("Corresponding cost", best_cost[i])
        print("Associated number of trucks needed:", ass_numb_trucks[i])
        print("Associated average utilization rate:", ass_avg_cap_util[i])
        print("Associated service level", ass_serv_lev[i])

    print("----- Total -----")
    print("Total number of trucks needed:", ass_numb_trucks[1]+ass_numb_trucks[2])
    print("Total average utilization rate", 0.5*(ass_avg_cap_util[1]+ass_avg_cap_util[2]))


def main():
    h = [0, 1, 1]  # holding cost per unit in inventory, per unit of time
    b = [0, 19, 19]  # backlog cost per unit backlog (negative inventory), per unit of time
    K = [0, 50, 50]  # fixed order cost per truck
    mu_d = [0, 10, 10]  # mean demand (normal distribution)
    stdev_d = [0, 2, 2]  # standard deviation demand (normal distribution)
    truck_cap = 33  # standard closed box trailers can fit 33 europallets

    simulation(mu_d, stdev_d, h, K, b, truck_cap)


main()



