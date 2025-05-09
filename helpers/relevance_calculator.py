def calculate_relevance_score(distance: float) -> float:
    """
    Convert distance to a relevance score between 0 and 1.
    Lower distances become higher relevance scores.
    
    Args:
        distance (float): The distance from ChromaDB
        
    Returns:
        float: Relevance score between 0 and 1
    """
    # Based on typical ChromaDB distance ranges
    max_relevant_distance = 2.0
    
    # Convert distance to relevance score (0 to 1)
    relevance = max(0, 1 - (distance / max_relevant_distance))
    return round(relevance, 4) 