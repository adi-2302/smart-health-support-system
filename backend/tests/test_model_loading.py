"""Model file loading: native XGBoost format by default, clear errors when the file is bad."""
import os
import tempfile

import pytest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app import config, ml_service  # noqa: E402


def test_default_model_is_native_format():
    assert config.MODEL_PATH.suffix == ".json"
    model = ml_service._read_model(config.MODEL_PATH)
    assert len(model.feature_names_in_) == 20
    assert model.n_classes_ == 3


def test_missing_model_gives_actionable_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="train_final_model.py"):
        ml_service._read_model(tmp_path / "nope.json")


def test_corrupt_model_gives_actionable_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("this is not a model")
    with pytest.raises(RuntimeError, match="train_final_model.py"):
        ml_service._read_model(bad)
