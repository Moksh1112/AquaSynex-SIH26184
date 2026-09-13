import pandas as pd

def rank_candidates(scores, top_k=None) -> list:
    """
    Rank candidate ATMs based on the 'probability' column.
    
    :param scores: A Pandas DataFrame or list of dicts containing candidate predictions.
    :param top_k: Optional integer to return only the top K candidates.
    :return: A list of dictionaries representing the ranked candidates.
    """
    if isinstance(scores, list):
        df = pd.DataFrame(scores)
    else:
        df = scores.copy()
        
    if df.empty:
        return []
        
    if 'probability' not in df.columns:
        raise ValueError("Missing 'probability' column. Ensure predict_candidates has been run.")
        
    # Sort by probability descending
    df_ranked = df.sort_values(by='probability', ascending=False)
    
    # Remove duplicate ATMs keeping the one with the highest probability
    if 'atm_id' in df_ranked.columns:
        df_ranked = df_ranked.drop_duplicates(subset=['atm_id'], keep='first')
        
    # Add rank column
    df_ranked = df_ranked.reset_index(drop=True)
    df_ranked['rank'] = df_ranked.index + 1
    
    if top_k is not None:
        df_ranked = df_ranked.head(top_k)
        
    return df_ranked.to_dict(orient='records')
