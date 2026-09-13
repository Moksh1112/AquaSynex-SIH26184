import pandas as pd

def explain_prediction(prediction_data):
    """
    Generate explanations based on the candidate predictions.
    
    :param prediction_data: A Pandas DataFrame or list of ranked candidate dictionaries.
    :return: A list of explanation strings.
    """
    if not prediction_data:
        return ["No prediction data available for explanation."]
        
    if isinstance(prediction_data, list):
        df = pd.DataFrame(prediction_data)
    else:
        df = prediction_data.copy()
        
    if df.empty:
        return ["No candidates available to generate explanation."]
        
    explanations = []
    
    # Analyze the top candidate
    top_cand = df.iloc[0]
    atm_id = top_cand.get('atm_id', 'Unknown ATM')
    prob = top_cand.get('probability', 0.0)
    
    explanations.append(f"Top candidate ({atm_id}) has a high risk probability of {prob*100:.1f}%.")
    
    if 'distance_to_case_center' in top_cand and top_cand['distance_to_case_center'] > 0:
        dist = top_cand['distance_to_case_center']
        explanations.append(f"Location is within {dist:.1f} km of the suspicious activity center.")
        
    if 'transaction_velocity' in top_cand and top_cand['transaction_velocity'] > 0:
        explanations.append("High recent transaction velocity detected for the connected account.")
        
    if 'recent_activity_score' in top_cand and top_cand['recent_activity_score'] > 0:
        explanations.append("Suspicious recent historical cash-out behavior identified.")
        
    if 'atm_proximity_score' in top_cand and top_cand['atm_proximity_score'] > 0:
        explanations.append("ATM location aligns with historical withdrawal patterns.")
        
    if len(explanations) == 1:
        explanations.append("Candidate identified based on spatial and temporal correlations.")
        
    return explanations
