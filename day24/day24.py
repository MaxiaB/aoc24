from collections import namedtuple
from typing import List, Tuple

Calc = namedtuple("Calc", ["wires", "op"])


def read_input():
    circuit = {}
    with open("input.txt", "r") as f:
        doing_wires = True
        for line in f.readlines():
            line = line.strip()
            if not line:
                doing_wires = False
                continue
            if doing_wires:
                wire, val = line.split(": ")
                val = int(val)
                circuit[wire] = val
                continue
            wire1, op, wire2, _, outwire = line.split(" ")
            circuit[outwire] = Calc([wire1, wire2], op)
    return circuit


def find_value(circuit, key):
    val = circuit[key]
    if isinstance(val, int):
        return val
    lval = find_value(circuit, val.wires[0])
    rval = find_value(circuit, val.wires[1])
    if val.op == "AND":
        return lval & rval
    elif val.op == "XOR":
        return lval ^ rval
    else:
        return lval | rval


def get_wire_nums(circuit, prefix: str) -> int:
    total = 0
    keys = list(sorted(filter(lambda key: key[0] == prefix, circuit.keys())))
    for i, k in enumerate(keys):
        total += find_value(circuit, k) * 2**i
    return total


HALF_ADD_PRE = "HA_"
HALF_ADD_CARRY_PRE = "HAC_"
FULL_ADD_CARRY_PRE = "FAC_"
ADD_WITH_CARRY_PRE = "z"
CARRY_PRE = "C_"


def find_exact_inputs(circuit, wires) -> List[Tuple[str, Calc]]:
    results = []
    for outwire, val in circuit.items():
        if not isinstance(val, Calc):
            continue
        if set(wires) == set(val.wires):
            results.append((outwire, val))
    return results


def traverse_gates(circuit):
    name_map = {}
    swaps = []

    def replace_wire_name(old_name: str, new_name: str):
        new_circuit = {}
        items = list(circuit.items())
        for outwire, val in items:
            if outwire == old_name:
                new_circuit[new_name] = val
                continue
            if not isinstance(val, Calc):
                new_circuit[outwire] = val
                continue
            wires = list(val.wires)
            if old_name not in wires:
                new_circuit[outwire] = val
                continue
            wires.remove(old_name)
            wires.append(new_name)
            new_circuit[outwire] = Calc(wires, val.op)
        name_map[new_name] = old_name
        assert len(new_circuit) == len(circuit)
        return new_circuit

    def swap_wires(wires: List[str]) -> None:
        for outwire, val in list(circuit.items()):
            if not isinstance(val, Calc):
                continue
            if wires[0] == val.wires[0]:
                circuit[outwire] = Calc([wires[1], val.wires[1]], val.op)
            elif wires[0] == val.wires[1]:
                circuit[outwire] = Calc([wires[1], val.wires[0]], val.op)
            elif wires[1] == val.wires[0]:
                circuit[outwire] = Calc([wires[0], val.wires[1]], val.op)
            elif wires[1] == val.wires[1]:
                circuit[outwire] = Calc([wires[0], val.wires[0]], val.op)
        swaps.extend(wires)

    def find_exact(wires, op) -> str:
        results = find_exact_inputs(circuit, wires)
        for outwire, calc in results:
            if calc.op == op:
                return outwire

        swap_possibles = []
        for _, val in circuit.items():
            if not isinstance(val, Calc):
                continue
            if (wires[0] in val.wires or wires[1] in val.wires) and val.op == op:
                swap_possibles.append(val)
        assert len(swap_possibles) == 1
        wires_to_swap = list(
            filter(lambda x: x not in wires, swap_possibles[0].wires)
        ) + list(filter(lambda x: x not in swap_possibles[0].wires, wires))
        swap_wires(wires_to_swap)
        return find_exact(wires, op)

    # start with x00, y00 and make the carry, no carry to take into account for least sig
    outwire = find_exact(["x00", "y00"], "AND")
    circuit = replace_wire_name(outwire, f"{CARRY_PRE}00")

    # then make half adds and half add carries for individual bits
    # if exact match isn't found, find whichever one is there and then swap the other with the wire shared with it
    ixbit = 1
    while f"x{str(ixbit).zfill(2)}" in circuit:
        prev_suffix = str(ixbit - 1).zfill(2)
        suffix = str(ixbit).zfill(2)

        outwire = find_exact([f"{c}{suffix}" for c in "xy"], "XOR")
        circuit = replace_wire_name(outwire, f"{HALF_ADD_PRE}{suffix}")

        outwire = find_exact([f"{c}{suffix}" for c in "xy"], "AND")
        circuit = replace_wire_name(outwire, f"{HALF_ADD_CARRY_PRE}{suffix}")

        outwire = find_exact(
            [f"{CARRY_PRE}{prev_suffix}", f"{HALF_ADD_PRE}{suffix}"], "AND"
        )
        circuit = replace_wire_name(outwire, f"{FULL_ADD_CARRY_PRE}{suffix}")

        outwire = find_exact(
            [f"{HALF_ADD_CARRY_PRE}{suffix}", f"{FULL_ADD_CARRY_PRE}{suffix}"], "OR"
        )
        circuit = replace_wire_name(outwire, f"{CARRY_PRE}{suffix}")

        ixbit += 1
    return ",".join(
        sorted([wire if len(wire) == 3 else name_map[wire] for wire in swaps])
    )


if __name__ == "__main__":
    circuit = read_input()
    print(get_wire_nums(circuit, "z"))

    swaps = traverse_gates(circuit)
    print(swaps)
