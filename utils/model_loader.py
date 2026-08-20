from pathlib import Path

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "all-MiniLM-L6-v2"


def _is_valid_model(path: Path) -> bool:
    """Check whether the local directory contains a usable model."""
    if not path.is_dir():
        return False

    required_files = [
        "config.json",
        "modules.json",
        "tokenizer.json",
    ]

    return all((path / filename).exists() for filename in required_files)


def load_embedding_model(expected_model: str | None = None) -> SentenceTransformer:
    """
    Load the local embedding model.

    If the model does not exist or fails validation, download it
    from Hugging Face and save it locally.
    """
    if expected_model is not None and expected_model != MODEL_NAME:
        raise ValueError(
            f"Expected embedding model {expected_model!r} does not match loader model {MODEL_NAME!r}"
        )

    if _is_valid_model(MODEL_PATH):
        try:
            return SentenceTransformer(str(MODEL_PATH), device="cpu")
        except Exception:
            print("Local embedding model failed validation. Re-downloading.")

    print(f"Downloading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME, device="cpu")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_PATH))

    return model