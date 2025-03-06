#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from beartype import beartype

from sae_hacking.safetensor_utils import load_dict_with_tensors


@beartype
def find_pattern(tensor_dict: dict) -> list[tuple[int, int, int, int]]:
    # Get bipartite partition

    results = []

    # Precompute positive and negative neighbors for each node
    pos_neighbors = {ablator_node: set() for ablator_node in tensor_dict}
    neg_neighbors = {ablator_node: set() for ablator_node in tensor_dict}

    for ablator_node in tensor_dict:
        for reader_node, weight in enumerate(tensor_dict[ablator_node]):
            if weight > 0:
                pos_neighbors[ablator_node].add(reader_node)
            elif weight < 0:
                neg_neighbors[ablator_node].add(reader_node)

    # For each A in X and each C in X
    for A in tensor_dict:
        # Find all B where AB is positive
        pos_B_from_A = pos_neighbors[A]

        for C in tensor_dict:
            if A == C:
                continue

            # Find all B where BC is positive
            pos_B_from_C = pos_neighbors[C]

            # Find common B nodes: these can be the 'B' in our 4-tuple
            common_B = pos_B_from_A.intersection(pos_B_from_C)

            # Find all D where AD is positive and CD is negative
            potential_D = pos_neighbors[A].intersection(neg_neighbors[C])

            # Generate all valid 4-tuples
            for B in common_B:
                for D in potential_D:
                    if B != D:  # Ensure distinct nodes
                        results.append((A, B, C, D))

    return results


@beartype
def make_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--input-path", required=True)
    return parser


@beartype
def main(args: Namespace) -> None:
    tensor_dict = load_dict_with_tensors(args.input_path)
    find_pattern(tensor_dict)


if __name__ == "__main__":
    main(make_parser().parse_args())
