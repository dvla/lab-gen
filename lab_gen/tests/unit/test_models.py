import pytest

from lab_gen.datatypes.errors import ModelKeyError
from lab_gen.datatypes.models import Model, ModelFamily, ModelProvider, ModelVariant
from lab_gen.services.llm.lifetime import get_model, init_models


@pytest.fixture(scope="session", autouse=True)
def _before_all() -> None:
    init_models()


def test_default_model() -> None:
    """Tests getting the default model."""
    default_model = get_model()

    assert default_model.provider == ModelProvider.AZURE
    assert default_model.variant == ModelVariant.GENERAL
    assert default_model.family == ModelFamily.GPT


def test_specific_model() -> None:
    """Tests getting the model by key."""
    a_model = get_model(Model.compute_key(ModelProvider.BEDROCK, ModelVariant.ADVANCED, ModelFamily.CLAUDE))

    assert a_model.provider == ModelProvider.BEDROCK
    assert a_model.variant == ModelVariant.ADVANCED
    assert a_model.family == ModelFamily.CLAUDE


def test_invalid_model() -> None:
    """Tests getting the model by invalid key."""
    with pytest.raises(ModelKeyError):
        get_model("NonExistentModel")
