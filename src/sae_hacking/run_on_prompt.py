#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace

import torch
from beartype import beartype
from sae_lens import SAE, HookedSAETransformer
from transformers import AutoTokenizer

from sae_hacking.timeprint import timeprint

# TODO Save in output dir
# TODO Run in loop


@beartype
def highlight_tokens_with_intensity(
    split_text: list[str], activations: torch.Tensor
) -> str:
    html_parts = []

    for token, activation in zip(split_text, activations, strict=True):
        # TODO Normalize activation

        red = int(max(235 - (activation * 20), 100))
        green = 255
        blue = int(max(235 - (activation * 20), 100))

        color = f"#{red:02x}{green:02x}{blue:02x}"

        highlighted = f'<span style="background-color: {color};">{token}</span>'
        html_parts.append(highlighted)

    return "".join(html_parts)


@beartype
def create_html(
    split_text: list[str], activations: torch.Tensor, args: Namespace
) -> str:
    html_output = highlight_tokens_with_intensity(split_text, activations)

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Highlighted Text Example</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 16px;
                line-height: 1.5;
                margin: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>Green Intensity Highlighting Example</h1>
        <p>{html_output}</p>
        <hr>
        <p>Arguments: {args}</p>
    </body>
    </html>
    """

    return full_html


@beartype
def get_feature_activation_per_token(
    model: HookedSAETransformer,
    sae: SAE,
    feature_idx: int,
    prompt: str,
) -> torch.Tensor:
    """
    Returns an array showing how much a specific SAE feature activated on each token of the prompt.

    Args:
        model: The transformer model with SAE hooks
        sae: The SAE to analyze
        feature_idx: Index of the specific feature to track
        prompt: The input text prompt

    Returns:
        Tensor of shape [num_tokens] containing activation values for the specified feature
        across all tokens in the prompt
    """
    # Ensure the SAE uses its error term for accurate activation measurement
    sae.use_error_term = True

    # Reset the model and SAEs to ensure clean state
    model.reset_hooks()
    model.reset_saes()

    # Run the model with the SAE to get activations
    _, cache = model.run_with_cache_with_saes(prompt, saes=[sae])

    # Get the SAE activations from the cache
    # Shape: [batch_size, sequence_length, n_features]
    sae_acts = cache[f"{sae.cfg.hook_name}.hook_sae_acts_post"]

    # Extract activations for the specified feature across all tokens
    # Assuming batch_size is 1, we take the first batch with sae_acts[0]
    feature_acts = sae_acts[0, :, feature_idx]

    return feature_acts


@beartype
def make_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--model", default="google/gemma-2-2b")
    parser.add_argument("--sae-release", required=True)
    parser.add_argument("--sae-id", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--feature-idx", required=True, type=int)
    parser.add_argument("--prompt", required=True)
    return parser


@torch.inference_mode()
@beartype
def main(args: Namespace) -> None:
    timeprint("Starting")
    model = HookedSAETransformer.from_pretrained(args.model, device=args.device)
    timeprint("Loaded model")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    timeprint("Loaded tokenizer")

    sae, _, _ = SAE.from_pretrained(
        release=args.sae_release, sae_id=args.sae_id, device=args.device
    )
    timeprint("Loaded SAE")
    activations_S = get_feature_activation_per_token(
        model, sae, args.feature_idx, args.prompt
    )
    timeprint("Got activations")

    split_text = tokenizer.tokenize(args.prompt, add_special_tokens=True)
    print(len(split_text))
    print(activations_S.shape)

    html_output = create_html(split_text, activations_S, args)
    print(html_output)


if __name__ == "__main__":
    main(make_parser().parse_args())
