#!/usr/bin/env python3
import numpy as np
from huggingface_hub import hf_hub_download
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram
from sklearn.cluster import AgglomerativeClustering

# Gemma-scope based on https://colab.research.google.com/drive/17dQFYUYnuKnP6OwQPH9v_GSYUW5aj-Rp
# Neuronpedia API based on https://colab.research.google.com/github/jbloomAus/SAELens/blob/main/tutorials/tutorial_2_0.ipynb


# 3. Define dendrogram plotting function
def plot_dendrogram(model, **kwargs):
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)

    # Create abbreviated labels for better visualization
    # labels = [f"{i}: {desc[:30]}..." for i, desc in enumerate(feature_descriptions)]

    return dendrogram(
        linkage_matrix,  # labels=labels,
        leaf_rotation=45,
        leaf_font_size=8,
        **kwargs,
    )


def main():
    # 1. Download and load the weights
    path_to_params = hf_hub_download(
        repo_id="google/gemma-scope-2b-pt-res",
        filename="layer_20/width_16k/average_l0_71/params.npz",
        force_download=False,
    )

    params = np.load(path_to_params)
    decoder_vectors_EM = params["W_dec"][0:1000]
    print(f"{decoder_vectors_EM.shape=}")

    # 2. Get neuron descriptions
    # url = "TODO"  # Fill in correct Neuronpedia API endpoint
    # headers = {"Content-Type": "application/json"}

    # response = requests.get(url, headers=headers)
    # data = response.json()
    # explanations_df = pd.DataFrame(data)
    # explanations_df.rename(columns={"index": "feature"}, inplace=True)
    # explanations_df["description"] = explanations_df["description"].apply(
    #    lambda x: x.lower()
    # )

    # 4. Perform clustering and visualization
    model = AgglomerativeClustering(
        distance_threshold=0,
        n_clusters=None,
        linkage="single",
        metric="cosine",
        compute_distances=True,
    )

    model = model.fit(decoder_vectors_EM)

    # Visualize
    plt.figure(figsize=(25, 15))
    plt.title("Hierarchical Clustering of Gemma SAE Decoder Vectors")
    plot_dendrogram(
        model,
        # feature_descriptions=explanations_df["description"].tolist(),
        truncate_mode="level",
        p=5,
    )
    plt.xlabel("Feature Index and Description")
    plt.ylabel("Cosine Distance")
    plt.tight_layout()
    plt.show()

    # Print clustering statistics
    print(f"Number of features: {decoder_vectors_EM.shape[0]}")
    print(f"Feature vector dimension: {decoder_vectors_EM.shape[1]}")

    # Get main clusters at a specific distance threshold
    distance_threshold = None
    model_cut = AgglomerativeClustering(
        distance_threshold=distance_threshold,
        n_clusters=500,
        linkage="complete",
        metric="cosine",
    )
    cluster_labels = model_cut.fit_predict(decoder_vectors_EM)

    # Print cluster statistics and sample descriptions from each cluster
    n_clusters = len(np.unique(cluster_labels))
    print(
        f"\nNumber of clusters at distance threshold {distance_threshold}: {n_clusters}"
    )
    for i in range(n_clusters):
        cluster_size = np.sum(cluster_labels == i)
        print(f"\nCluster {i} size: {cluster_size}")
        cluster_indices = np.where(cluster_labels == i)[0][:3]
        print(cluster_indices)
        # Print first 3 descriptions from this cluster as examples
        # print("Sample features in this cluster:")
        # for idx in cluster_indices:
        #    print(f"  - {explanations_df['description'].iloc[idx]}")


if __name__ == "__main__":
    main()
