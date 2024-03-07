import numpy as np
import math as mt


# Section 1: function definition
def capacity_utilization(order,truck_cap):
    capac_util = []
    numb_ftl = int(order // truck_cap)
    cap_util_ltl = (order / truck_cap) - numb_ftl
    if numb_ftl != 0:
        capac_util += [1] * numb_ftl
        capac_util.append(cap_util_ltl)
    else:
        capac_util.append(cap_util_ltl)
    return capac_util


def order_calculation(inv, s, S, numb_trucks, truck_cap):
    if inv <= s:
        order = S - inv
        # print(s,",",S,": Order ",order, " units")
        numb_trucks += mt.ceil(order / truck_cap)
    else:
        order = 0
    return order, numb_trucks


def cost_calculation(inv, cost, order, h, b, K, numb_per_OoS, truck_cap):
    if inv > 0:
        cost += (h * inv)
    else:
        cost -= (b * inv)
        numb_per_OoS += 1

    if order > 0:
        cost += K * mt.ceil(order / truck_cap)
    return cost, numb_per_OoS


def simulation(mu_d, stdev_d, h, K, b, truck_cap):
    ass_numb_trucks = 0     # associated number of trucks
    ass_avg_cap_util = 0    # associated average capacity utilization
    ass_serv_lev = 0        # associated service level
    horizon = 1_000
    s_range = [i for i in range(-20, 50)]
    S_max = 50
    best_s = 0
    best_S = 0
    best_cost = 999999999

    for s in s_range:
        for S in range(s, S_max + 1):
            cost = 0
            numb_trucks = 0
            numb_per_OoS = 0    # number of periods out of stock
            cap_util = []
            inv = mu_d

            for t in range(horizon):
                # calculate order and the number of corresponding trucks
                order, numb_trucks = order_calculation(inv, s, S, numb_trucks, truck_cap)

                # Add capacity utilization rate(s) to list
                if order > 0:
                    cap_util.extend(capacity_utilization(order, truck_cap))

                # Add order and subtract demand
                inv += order
                inv -= max(0, np.random.normal(mu_d, stdev_d))


                # calculate costs
                cost, numb_per_OoS = cost_calculation(inv, cost, order, h, b, K, numb_per_OoS, truck_cap)

                if cost > best_cost:
                    break

            if cost < best_cost:
                best_s = s
                best_S = S
                best_cost = cost
                ass_numb_trucks = numb_trucks
                ass_avg_cap_util = np.mean(cap_util)
                ass_serv_lev = 1-(numb_per_OoS/horizon)

    print("Best value for s:", best_s)
    print("Best value for S:", best_S)
    print("Corresponding cost", best_cost)
    print("Associated number of trucks needed:", ass_numb_trucks)
    print("Associated average utilization rate:", ass_avg_cap_util)
    print("Associated service level", ass_serv_lev)


# Section 2: Execution
def main():
    h = 1           # holding cost per unit in inventory, per unit of time
    b = 19          # backlog cost per unit backlog (negative inventory), per unit of time
    K = 50          # fixed order cost per truck
    mu_d = 10       # mean demand (normal distribution)
    stdev_d = 2     # standard deviation demand (normal distribution)
    truck_cap = 33  # standard closed box trailers can fit 33 europallets

    simulation(mu_d, stdev_d, h, K, b, truck_cap)


main()

