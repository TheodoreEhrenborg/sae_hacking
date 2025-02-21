#!/usr/bin/env python3
import asyncio
from argparse import ArgumentParser, Namespace

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
from beartype import beartype
from huggingface_hub import hf_hub_download
from scipy.cluster import hierarchy
from sklearn.cluster import AgglomerativeClustering

# Gemma-scope based on https://colab.research.google.com/drive/17dQFYUYnuKnP6OwQPH9v_GSYUW5aj-Rp
# Neuronpedia API based on https://colab.research.google.com/github/jbloomAus/SAELens/blob/main/tutorials/tutorial_2_0.ipynb


@beartype
def make_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--abridge", type=int)
    return parser


@beartype
async def get_description_async(idx: int, session: aiohttp.ClientSession) -> str:
    url = f"https://www.neuronpedia.org/api/feature/gemma-2-2b/20-gemmascope-res-16k/{idx}"
    async with session.get(url) as response:
        data = await response.json()
        try:
            return data["explanations"][0]["description"]
        except:
            print(data)
            raise


@beartype
async def get_all_descriptions(indices: list[int]) -> list[str]:
    async with aiohttp.ClientSession() as session:
        tasks = [get_description_async(idx, session) for idx in indices]
        return await asyncio.gather(*tasks)


@beartype
def main(args: Namespace) -> None:
    path_to_params = hf_hub_download(
        repo_id="google/gemma-scope-2b-pt-res",
        filename="layer_20/width_16k/average_l0_71/params.npz",
        force_download=False,
    )

    params = np.load(path_to_params)
    decoder_vectors_EM = params["W_dec"]
    if args.abridge:
        decoder_vectors_EM = decoder_vectors_EM[0 : args.abridge]
    E = decoder_vectors_EM.shape[0]
    print(f"{decoder_vectors_EM.shape=}")
    Z = hierarchy.linkage(decoder_vectors_EM, "complete")
    plt.figure()
    dn = hierarchy.dendrogram(
        Z,
        p=4,
        truncate_mode="level",
        labels=[f"label {i}" for i in range(E)],
        no_plot=True
    )
    if True:
        for i in dn['icoord']:
            for j in range(len(i)-1):
                plt.plot([i[j], i[j+1]], [dn['dcoord'][dn['icoord'].index(i)][j],
                        dn['dcoord'][dn['icoord'].index(i)][j+1]], 'k-', linewidth=0.5)
        plt.xticks(dn['leaves'],
          [f"label {i}" for i in dn['leaves']],
          fontsize=6)

    # plt.tick_params(axis='x', labelsize=1)
    plt.savefig(
        "/results/tmp.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()
    exit()

    cluster_model = AgglomerativeClustering(
        distance_threshold=None,
        n_clusters=500,
        linkage="complete",
        metric="cosine",
    )
    cluster_labels = cluster_model.fit_predict(decoder_vectors_EM)

    n_clusters = len(np.unique(cluster_labels))
    print(f"\nNumber of clusters: {n_clusters}")
    print("Getting descriptions from Neuronpedia...")
    exit()
    descriptions = asyncio.run(get_all_descriptions(list(range(E))))
    for i in range(n_clusters):
        cluster_size = np.sum(cluster_labels == i)
        if cluster_size > 1:
            print(f"\nCluster {i} size: {cluster_size}")
            cluster_indices = np.where(cluster_labels == i)[0]
            for idx in cluster_indices:
                print(f"{idx}: {descriptions[idx]}")


if __name__ == "__main__":
    main(make_parser().parse_args())
