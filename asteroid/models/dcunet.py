import torch

from .. import complex_nn
from asteroid_filterbanks import make_enc_dec
from asteroid_filterbanks.transforms import from_torchaudio
from ..masknn.convolutional import DCUMaskNet
from .base_models import BaseEncoderMaskerDecoder


class BaseDCUNet(BaseEncoderMaskerDecoder):  # CHECK-JIT
    """Base class for ``DCUNet`` and ``DCCRNet`` classes.

    Args:
        stft_kernel_size (int): STFT frame length to use
        stft_stride (int, optional): STFT hop length to use.
        sample_rate (float): Sampling rate of the model.

    """

    masknet_class = DCUMaskNet

    def __init__(
        self,
        architecture,
        stft_kernel_size=512,
        stft_stride=None,
        sample_rate=16000.0,
        masknet_kwargs=None,
    ):
        self.architecture = architecture
        self.stft_kernel_size = stft_kernel_size
        self.stft_stride = stft_stride
        self.masknet_kwargs = masknet_kwargs

        encoder, decoder = make_enc_dec(
            "stft",
            kernel_size=stft_kernel_size,
            n_filters=stft_kernel_size,
            stride=stft_stride,
            sample_rate=sample_rate,
        )
        masker = self.masknet_class.default_architecture(architecture, **(masknet_kwargs or {}))
        super().__init__(encoder, masker, decoder)

    def forward_encoder(self, wav):
        tf_rep = self.encoder(wav)
        return complex_nn.as_torch_complex(tf_rep)

    def apply_masks(self, tf_rep, est_masks):
        masked_tf_rep = est_masks * tf_rep.unsqueeze(1)
        return from_torchaudio(torch.view_as_real(masked_tf_rep))

    def get_model_args(self):
        """Arguments needed to re-instantiate the model."""
        model_args = {
            "architecture": self.architecture,
            "stft_kernel_size": self.stft_kernel_size,
            "stft_stride": self.stft_stride,
            "sample_rate": self.sample_rate,
            "masknet_kwargs": self.masknet_kwargs,
        }
        return model_args


class DCUNet(BaseDCUNet):
    """DCUNet as proposed in [1].

    Args:
        architecture (str): The architecture to use, any of
            "DCUNet-10", "DCUNet-16", "DCUNet-20", "Large-DCUNet-20".
        stft_kernel_size (int): STFT frame length to use
        stft_stride (int, optional): STFT hop length to use.

    References
        - [1] : "Phase-aware Speech Enhancement with Deep Complex U-Net",
        Hyeong-Seok Choi et al. https://arxiv.org/abs/1903.03107
    """

    masknet_class = DCUMaskNet
