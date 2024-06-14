import argparse
import os

import pandas as pd
from minicons import scorer

from src.surprisal import surprisal_at_word

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, help='model name, should be in minicons')
    parser.add_argument('--data', required=True, help='Path to file with stimuli')

    # Parsing arguments
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    model_surprisal(df, args.model)
    df.to_csv(args.data, index = False) # editing the CSV one model at a time

def load_model(model_name):
    if 'gpt' in model_name:
        model = scorer.IncrementalLMScorer(model_name)
    else:
        model = scorer.MaskedLMScorer(model_name)
    return model

def model_surprisal(data : pd.DataFrame, model_name : str):
    model = load_model(model_name)
    if 'uncased' in model_name:
        data['sentence'] = data['sentence'].str.lower()
    surprisals = surprisal_at_word(model, data['sentence'].tolist(), data['target'].tolist())
    data[f'{model_name}_surprisal'] = surprisals

if __name__ == "__main__":
    main()
