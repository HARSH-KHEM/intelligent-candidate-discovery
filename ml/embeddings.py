"""
embeddings.py — Load SBERT model and generate 384-dim embeddings.

Uses the all-MiniLM-L6-v2 model from sentence-transformers for fast,
high-quality semantic embeddings of job descriptions and candidate profiles.

Usage:
    from ml.embeddings import EmbeddingEngine
    engine = EmbeddingEngine()
    vectors = engine.encode(["text1", "text2"])  # shape: (2, 384)
"""

import logging
from typing import Union

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────
DEFAULT_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
DEFAULT_BATCH_SIZE = 64


class EmbeddingEngine:
    """Wrapper around sentence-transformers for generating embeddings."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Load the SBERT model.

        Args:
            model_name: HuggingFace model identifier. Defaults to all-MiniLM-L6-v2.
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dim = EMBEDDING_DIM
        logger.info(f"Model loaded. Embedding dimension: {self.dim}")

    def encode(
        self,
        texts: Union[list[str], str],
        batch_size: int = DEFAULT_BATCH_SIZE,
        normalize: bool = True,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Generate embeddings for one or more texts.

        Args:
            texts: Single string or list of strings to embed.
            batch_size: Number of texts to process at once (for large datasets).
            normalize: If True, L2-normalize vectors for cosine similarity via dot product.
            show_progress: Show a progress bar during encoding.

        Returns:
            np.ndarray of shape (n_texts, 384) with float32 embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)

        logger.info(f"Encoding {len(texts)} texts (batch_size={batch_size})")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        embeddings = embeddings.astype(np.float32)
        logger.info(f"Generated embeddings: shape={embeddings.shape}")
        return embeddings

    def encode_jd(self, jd_text: str) -> np.ndarray:
        """Encode a single job description. Returns shape (1, 384)."""
        return self.encode([jd_text], normalize=True)

    def encode_candidates(
        self,
        profiles: list[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> np.ndarray:
        """
        Encode candidate profiles in batches.

        Args:
            profiles: List of candidate profile/resume texts.
            batch_size: Batch size for processing large datasets.

        Returns:
            np.ndarray of shape (n_candidates, 384).
        """
        return self.encode(profiles, batch_size=batch_size, show_progress=True)


def main():
    """Test embedding generation with sample data."""
    engine = EmbeddingEngine()

    # Test single JD embedding
    jd = (
        "Senior Backend Engineer with 5+ years Python experience. "
        "Must know FastAPI, PostgreSQL, Docker, Kubernetes, AWS."
    )
    jd_emb = engine.encode_jd(jd)
    print(f"JD embedding shape: {jd_emb.shape}")
    print(f"JD embedding norm:  {np.linalg.norm(jd_emb[0]):.4f}")

    # Test batch candidate embeddings
    candidates = [
        "Python developer with 6 years building REST APIs using FastAPI and Django.",
        "Frontend React developer specializing in UI/UX design.",
        "DevOps engineer with extensive Kubernetes and AWS experience.",
        "Data scientist focused on NLP and transformer models.",
        "Java backend developer building microservices with Spring Boot.",
    ]
    cand_embs = engine.encode_candidates(candidates)
    print(f"\nCandidate embeddings shape: {cand_embs.shape}")

    # Compute cosine similarities (since vectors are normalized, dot product = cosine)
    similarities = np.dot(cand_embs, jd_emb.T).flatten()
    print("\nSimilarities to JD:")
    for text, sim in sorted(zip(candidates, similarities), key=lambda x: -x[1]):
        print(f"  {sim:.4f}  {text[:70]}...")

    print("\n✅ Embedding engine test passed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
