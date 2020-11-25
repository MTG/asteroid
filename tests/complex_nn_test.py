import torch
from torch.testing import assert_allclose
import pytest
import math

from asteroid import complex_nn as cnn
from asteroid.utils.test_utils import torch_version_tuple
from asteroid_filterbanks import transforms


def test_is_torch_complex():
    cnn.is_torch_complex(torch.randn(10, 10, dtype=torch.complex64))


def test_torch_complex_from_magphase():
    shape = (1, 257, 100)
    mag = torch.randn(shape).abs()
    phase = torch.remainder(torch.randn(shape), math.pi)
    out = cnn.torch_complex_from_magphase(mag, phase)
    assert_allclose(torch.abs(out), mag)
    assert_allclose(out.angle(), phase)


def test_torch_complex_from_reim():
    comp = torch.randn(10, 12, dtype=torch.complex64)
    assert_allclose(cnn.torch_complex_from_reim(comp.real, comp.imag), comp)


def test_as_torch_complex():
    shape = (1, 257, 100)
    re = torch.randn(shape)
    im = torch.randn(shape)
    # From mag and phase
    out = cnn.as_torch_complex((re, im))
    # From torch.complex
    out2 = cnn.as_torch_complex(out)
    assert_allclose(out, out2)
    # From torchaudio, ambiguous
    with pytest.warns(RuntimeWarning):
        out3 = cnn.as_torch_complex(torch.view_as_real(out))
    assert_allclose(out3, out)

    # From torchaudio, unambiguous
    _ = cnn.as_torch_complex(torch.randn(1, 5, 2))
    # From asteroid
    out4 = cnn.as_torch_complex(transforms.from_torchaudio(torch.view_as_real(out), dim=-2))
    assert_allclose(out4, out)


def test_as_torch_complex_raises():
    with pytest.raises(RuntimeError):
        cnn.as_torch_complex(torch.randn(1, 5, 3))


def test_onreim():
    inp = torch.randn(10, 10, dtype=torch.complex64)
    # Identity
    fn = cnn.on_reim(lambda x: x)
    assert_allclose(fn(inp), inp)
    # Top right quadrant
    fn = cnn.on_reim(lambda x: x.abs())
    assert_allclose(fn(inp), cnn.torch_complex_from_reim(inp.real.abs(), inp.imag.abs()))


def test_on_reim_class():
    inp = torch.randn(10, 10, dtype=torch.complex64)

    class Identity(torch.nn.Module):
        def __init__(self, a=0, *args, **kwargs):
            super().__init__()
            self.a = a

        def forward(self, x):
            return x + self.a

    fn = cnn.OnReIm(Identity, 0)
    assert_allclose(fn(inp), inp)
    fn = cnn.OnReIm(Identity, 1)
    assert_allclose(fn(inp), cnn.torch_complex_from_reim(inp.real + 1, inp.imag + 1))


def test_complex_mul_wrapper():
    a = torch.randn(10, 10, dtype=torch.complex64)

    fn = cnn.ComplexMultiplicationWrapper(torch.nn.ReLU)
    assert_allclose(
        fn(a),
        cnn.torch_complex_from_reim(
            torch.relu(a.real) - torch.relu(a.imag), torch.relu(a.real) + torch.relu(a.imag)
        ),
    )


@pytest.mark.parametrize("bound_type", ("BDSS", "sigmoid", "BDT", "tanh", "UBD", None))
def test_bound_complex_mask(bound_type):
    cnn.bound_complex_mask(torch.randn(4, 2, 257, dtype=torch.complex64), bound_type=bound_type)


def test_bound_complex_mask_raises():
    with pytest.raises(ValueError):
        cnn.bound_complex_mask(torch.randn(4, 2, 257, dtype=torch.complex64), bound_type="foo")
