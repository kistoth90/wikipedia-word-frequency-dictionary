"""Filtering utilities for word frequency dictionaries."""
import logging


def filter_by_ignore_list(
    frequency_dict: dict[str, dict[str, float | int]],
    ignore_list: list[str]
) -> dict[str, dict[str, float | int]]:
    """Remove words from frequency dictionary that are in ignore list.

    Args:
        frequency_dict: Word frequency dictionary with structure:
            {"word": {"count": int, "percentage": float}}
        ignore_list: List of words to exclude (case-insensitive)

    Returns:
        Filtered frequency dictionary without ignored words

    Example:
        >>> freq = {"hello": {"count": 5, "percentage": 2.5}, "world": {"count": 3, "percentage": 1.5}}
        >>> filter_by_ignore_list(freq, ["hello"])
        {"world": {"count": 3, "percentage": 1.5}}
    """
    if not ignore_list:
        return frequency_dict

    # Convert ignore list to lowercase for case-insensitive matching
    ignore_set = {word.lower() for word in ignore_list}

    filtered = {
        word: stats
        for word, stats in frequency_dict.items()
        if word.lower() not in ignore_set
    }

    removed_count = len(frequency_dict) - len(filtered)
    if removed_count > 0:
        logging.debug(f"Filtered {removed_count} words using ignore list")

    return filtered


def filter_by_percentile(
    frequency_dict: dict[str, dict[str, float | int]],
    percentile: int
) -> dict[str, dict[str, float | int]]:
    """Keep only words with frequency >= percentile threshold.

    Args:
        frequency_dict: Word frequency dictionary with structure:
            {"word": {"count": int, "percentage": float}}
        percentile: Percentile threshold (0-100)
            - 0: Keep all words
            - 50: Keep words with frequency >= median
            - 90: Keep words in top 10% by frequency
            - 100: Keep only words with maximum frequency

    Returns:
        Filtered frequency dictionary with words above threshold

    Example:
        If percentile=90, keep only words in top 10% by frequency.
        If we have 100 words sorted by frequency, this keeps the 10 most frequent words.

    Note:
        The percentile is calculated based on the position in the sorted frequency list,
        not on the actual percentage values.
    """
    if not frequency_dict:
        return {}

    # Extract and sort all percentage values
    percentages = sorted([stats["percentage"] for stats in frequency_dict.values()])

    # Calculate percentile index
    n = len(percentages)

    if percentile == 0:
        return frequency_dict.copy()

    if percentile == 100:
        # Keep only words at maximum percentage
        max_percentage = max(percentages)
        threshold = max_percentage
    else:
        # Calculate threshold at the given percentile
        index = int((percentile / 100) * n)
        if index >= n:
            return {}
        threshold = percentages[index]

    # Filter words above threshold
    filtered = {
        word: stats
        for word, stats in frequency_dict.items()
        if stats["percentage"] >= threshold
    }

    logging.debug(
        f"Filtered to {len(filtered)} words at {percentile}th percentile "
        f"(threshold: {threshold:.4f}%)"
    )

    return filtered
