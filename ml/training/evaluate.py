import pandas as pd

def evaluate_ranking(df: pd.DataFrame) -> dict:
    """
    Evaluates Top-K ranking metrics by grouping predictions by case_id.
    """
    if 'case_id' not in df.columns or 'label' not in df.columns or 'probability' not in df.columns:
        return {}

    cases = df['case_id'].unique()
    recall_1 = 0
    recall_3 = 0
    recall_5 = 0
    cases_with_positive = 0
    
    for case_id in cases:
        case_df = df[df['case_id'] == case_id]
        if case_df['label'].sum() == 0:
            continue
            
        cases_with_positive += 1
        
        # Sort descending by probability
        ranked = case_df.sort_values(by='probability', ascending=False).reset_index(drop=True)
        
        # Find rank of true positives (0-indexed, so we check if any are in the top K)
        # In this dataset, there's typically only 1 true positive per case.
        top_1 = ranked.head(1)['label'].sum() > 0
        top_3 = ranked.head(3)['label'].sum() > 0
        top_5 = ranked.head(5)['label'].sum() > 0
        
        if top_1: recall_1 += 1
        if top_3: recall_3 += 1
        if top_5: recall_5 += 1
        
    if cases_with_positive == 0:
        return {"recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0}
        
    return {
        "recall@1": float(recall_1 / cases_with_positive),
        "recall@3": float(recall_3 / cases_with_positive),
        "recall@5": float(recall_5 / cases_with_positive)
    }
