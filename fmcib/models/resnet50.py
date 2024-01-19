import os
from pathlib import Path

import torch
import tqdm
import wget
from loguru import logger
from monai.networks.nets import resnet50 as resnet50_monai

from fmcib.utils.download_utils import bar_progress


def resnet50(
    pretrained=True,
    device="cuda",
    weights_path=None,
    download_url="https://zenodo.org/records/10528450/files/model_weights.torch?download=1",
    n_input_channels=1,
    widen_factor=2,
    conv1_t_stride=2,
    bias_downsample=True,
    feed_forward=False,
):
    """
    Constructs a ResNet-50 model for image classification.

    Args:
        pretrained (bool, optional): If True, loads the pretrained weights. Default is True.
        device (str, optional): The device to load the model on. Default is "cuda".
        weights_path (str or Path, optional): The path to the pretrained weights file. If None, the weights will be downloaded. Default is None.
        download_url (str, optional): The URL to download the pretrained weights. Default is "https://www.dropbox.com/s/bd7azdsvx1jhalp/fmcib.torch?dl=1".

    Returns:
        torch.nn.Module: The ResNet-50 model.
    """
    logger.info(f"Loading pretrained foundation model (Resnet50) on {device}...")

    model = resnet50_monai(
        pretrained=False,
        n_input_channels=n_input_channels,
        widen_factor=widen_factor,
        conv1_t_stride=conv1_t_stride,
        feed_forward=feed_forward,
        bias_downsample=bias_downsample,
    )
    model = model.to(device)
    if pretrained:
        if weights_path is None:
            current_path = Path(os.getcwd())
            if not (current_path / "model_weights.torch").exists():
                wget.download(download_url, bar=bar_progress)
            weights_path = current_path / "model_weights.torch"

        logger.info(f"Loading weights from {weights_path}...")
        checkpoint = torch.load(weights_path, map_location=device)

        if "trunk_state_dict" in checkpoint:
            model_state_dict = checkpoint["trunk_state_dict"]
        elif "state_dict" in checkpoint:
            model_state_dict = checkpoint["state_dict"]
            model_state_dict = {key.replace("model.backbone.", ""): value for key, value in model_state_dict.items()}
            model_state_dict = {key.replace("module.", ""): value for key, value in model_state_dict.items()}

        msg = model.load_state_dict(model_state_dict, strict=False)
        logger.warning(f"Missing keys: {msg[0]} and unexpected keys: {msg[1]}")

    return model
