"""Run RMVPE with the model code from the RVC project (MIT) kept outside this repository.

RVC's ``infer/rmvpe.py`` imports two project-specific modules; they are replaced here by tiny
stand-ins so the network is called directly (no CUDA graphs). ``torch.load`` inside that file
keeps its default ``weights_only=True``, so the weights file cannot run code. The product
pipeline will get its own implementation later (see docs/PHASE0_REPORT.md).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import numpy as np

RMVPE_SAMPLE_RATE = 16000


def load_rvc_module(code_path: Path):
    """Import RVC's rmvpe.py from ``code_path`` with its two project modules stubbed."""
    import torch

    cuda_graph = types.ModuleType("tools.cuda_graph")
    cuda_graph.run_cuda_graph = lambda _model, _key, fn, x: fn(x)
    config = types.ModuleType("configs.config")
    config.get_device_dtype_sm = lambda i: (torch.device(f"cuda:{i}"), torch.float16, None, None)
    sys.modules.update(
        {
            "tools": types.ModuleType("tools"),
            "tools.cuda_graph": cuda_graph,
            "configs": types.ModuleType("configs"),
            "configs.config": config,
        }
    )
    spec = importlib.util.spec_from_file_location("rvc_rmvpe", code_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_f0(
    vocals_wav: Path, code_path: Path, weights_path: Path, threshold: float
) -> np.ndarray:
    """Return F0 in Hz at a 10 ms hop (0 = unvoiced) for a vocals file, on the GPU in fp16."""
    import librosa
    import torch

    module = load_rvc_module(code_path)
    audio, _ = librosa.load(str(vocals_wav), sr=RMVPE_SAMPLE_RATE, mono=True)
    model = module.RMVPE(str(weights_path), is_half=True, device="cuda:0")
    f0 = model.infer_from_audio(audio, thred=threshold)
    del model
    torch.cuda.empty_cache()
    return f0
