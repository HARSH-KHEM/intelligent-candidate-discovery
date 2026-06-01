"""
faiss_index.py — FAISS vector index for fast top-K candidate search.

Builds an IndexFlatIP (inner-product / cosine similarity on normalized vectors)
for sub-millisecond retrieval of the most relevant candidates given a JD embedding.

Usage:
    from ml.faiss_index import CandidateIndex
    index = CandidateIndex(dim=384)
    index.add(candidate_embeddings, candidate_ids)
    results = index.search(jd_embedding, top_k=50)
"""

import logging
import os
import pickle
from dataclasses import dataclass

import faiss
import numpy as np

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────
DEFAULT_DIM = 384
DEFAULT_TOP_K = 50


@dataclass
class SearchResult:
    """A single search result from the FAISS index."""
    candidate_id: str
    score: float  # cosine similarity (0 to 1 for normalized vectors)
    rank: int


class CandidateIndex:
    """FAISS-based vector index for candidate similarity search."""

    def __init__(self, dim: int = DEFAULT_DIM):
        """
        Initialize an empty FAISS index.

        Args:
            dim: Embedding dimension (384 for all-MiniLM-L6-v2).
        """
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # Inner product = cosine on normalized vectors
        self.candidate_ids: list[str] = []
        logger.info(f"Initialized FAISS IndexFlatIP (dim={dim})")

    @property
    def size(self) -> int:
        """Number of vectors currently in the index."""
        return self.index.ntotal

    def add(
        self,
        embeddings: np.ndarray,
        candidate_ids: list[str],
    ) -> None:
        """
        Add candidate embeddings to the index.

        Args:
            embeddings: np.ndarray of shape (n, dim) — must be L2-normalized.
            candidate_ids: List of candidate IDs matching the embeddings.

        Raises:
            ValueError: If shapes don't match or dimensions are wrong.
        """
        if embeddings.ndim != 2 or embeddings.shape[1] != self.dim:
            raise ValueError(
                f"Expected embeddings of shape (n, {self.dim}), "
                f"got {embeddings.shape}"
            )

        if len(candidate_ids) != embeddings.shape[0]:
            raise ValueError(
                f"Number of IDs ({len(candidate_ids)}) doesn't match "
                f"number of embeddings ({embeddings.shape[0]})"
            )

        embeddings = embeddings.astype(np.float32)
        self.index.add(embeddings)
        self.candidate_ids.extend(candidate_ids)
        logger.info(f"Added {len(candidate_ids)} candidates. Total: {self.size}")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[SearchResult]:
        """
        Search for the top-K most similar candidates to a query.

        Args:
            query_embedding: np.ndarray of shape (1, dim) or (dim,).
            top_k: Number of results to return.

        Returns:
            List of SearchResult sorted by descending similarity score.
        """
        if self.size == 0:
            logger.warning("Index is empty — no results to return.")
            return []

        # Ensure correct shape
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        query_embedding = query_embedding.astype(np.float32)

        # Clamp top_k to index size
        k = min(top_k, self.size)

        scores, indices = self.index.search(query_embedding, k)
        scores = scores[0]  # Flatten from (1, k) to (k,)
        indices = indices[0]

        results = []
        for rank, (idx, score) in enumerate(zip(indices, scores), start=1):
            if idx < 0:  # FAISS returns -1 for missing results
                continue
            results.append(SearchResult(
                candidate_id=self.candidate_ids[idx],
                score=float(score),
                rank=rank,
            ))

        logger.info(f"Search returned {len(results)} results (top_k={top_k})")
        return results

    def save(self, directory: str) -> None:
        """
        Save the index and metadata to disk.

        Args:
            directory: Path to save the index files.
        """
        os.makedirs(directory, exist_ok=True)
        index_path = os.path.join(directory, "faiss.index")
        meta_path = os.path.join(directory, "metadata.pkl")

        faiss.write_index(self.index, index_path)
        with open(meta_path, "wb") as f:
            pickle.dump({"candidate_ids": self.candidate_ids, "dim": self.dim}, f)

        logger.info(f"Index saved to {directory} ({self.size} vectors)")

    def load(self, directory: str) -> None:
        """
        Load a previously saved index from disk.

        Args:
            directory: Path containing the saved index files.

        Raises:
            FileNotFoundError: If index files don't exist.
        """
        index_path = os.path.join(directory, "faiss.index")
        meta_path = os.path.join(directory, "metadata.pkl")

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"No FAISS index found at {index_path}")

        self.index = faiss.read_index(index_path)

        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
            self.candidate_ids = meta["candidate_ids"]
            self.dim = meta["dim"]

        logger.info(f"Index loaded from {directory} ({self.size} vectors)")

    def reset(self) -> None:
        """Clear the index completely."""
        self.index = faiss.IndexFlatIP(self.dim)
        self.candidate_ids = []
        logger.info("Index reset.")


def main():
    """Test FAISS index with synthetic data."""
    import tempfile

    dim = DEFAULT_DIM
    n_candidates = 100

    # Generate random normalized embeddings
    np.random.seed(42)
    embeddings = np.random.randn(n_candidates, dim).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    ids = [f"CID-{i:04d}" for i in range(n_candidates)]

    # Build index
    index = CandidateIndex(dim=dim)
    index.add(embeddings, ids)
    print(f"Index size: {index.size}")

    # Search with first embedding as query
    query = embeddings[0:1]
    results = index.search(query, top_k=5)
    print("\nTop 5 results for CID-0000:")
    for r in results:
        print(f"  #{r.rank} {r.candidate_id} score={r.score:.4f}")

    # Test save/load
    with tempfile.TemporaryDirectory() as tmpdir:
        index.save(tmpdir)
        print(f"\nSaved to {tmpdir}")

        new_index = CandidateIndex(dim=dim)
        new_index.load(tmpdir)
        print(f"Loaded index size: {new_index.size}")

        results2 = new_index.search(query, top_k=5)
        assert results[0].candidate_id == results2[0].candidate_id
        print("Save/load verification: ✅")

    print("\n✅ FAISS index test passed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
