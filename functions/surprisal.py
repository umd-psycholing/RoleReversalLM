import numpy as np
import pandas as pd
from typing import List, Tuple

def surprisal_at_word(model, sentences : List, target_tokens : List):
    tokenwise_surprisals = model.token_score(sentences, surprisal = True, base_two = True)
    critical_surprisal = []
    for scores, sentence, target_tokens in zip(tokenwise_surprisals, sentences, target_tokens):
        try:
            word_surprisals = align_surprisal(scores, sentence)
            target_surprisal = 0
            target_list = target_tokens.split(" ")
            for word, surprisal in word_surprisals:
                if word in target_list:
                    target_surprisal += surprisal
        except IndexError:
            target_surprisal = -1
            import pdb; pdb.set_trace()
            print(f"Failed to compute surprisal for sentence {sentence} with scores {scores}")
        critical_surprisal.append(target_surprisal)
    return critical_surprisal

def word_final_surprisal(model, sentence, bi = True):
    surprisals = model.token_score(sentence, surprisal = True, base_two = True)[0]
    token_surprisals = align_surprisal(surprisals, sentence)
    if not bi:
        return np.sum([result[1] for result in token_surprisals[-2:]])
    return token_surprisals[-2][1] # getting probability of the word alone

def align_surprisal(token_surprisals: List[Tuple[str, float]], sentence: str):
    words = sentence.split(" ")
    token_index = 0
    word_index = 0
    word_level_surprisal = []  # list of word, surprisal tuples
    while token_index < len(token_surprisals):
        current_word = words[word_index]
        current_token, current_surprisal = token_surprisals[token_index]
        # token does not match, alignment must be adjusted
        mismatch = (current_token != current_word)

        while mismatch:
            token_index += 1
            current_token += token_surprisals[token_index][0].strip("##")
            current_surprisal += token_surprisals[token_index][1]
            mismatch = current_token != current_word
        word_level_surprisal.append((current_word, current_surprisal))
        token_index += 1
        word_index += 1
    return word_level_surprisal

def surprisal_effects(data : pd.DataFrame, surprisal_cols : List[str], comparison_cols: List[str], condition_name : str):
    # get the reversal and comparison columns from the stimulus config
    item_ids = data[data['condition'].isin(comparison_cols)]['item'].unique()
    diffs = []
    for item in item_ids:
        item_sentences = data[data['item'] == item]
        implausible_comparison = get_sentence_data(item_sentences, comparison_cols[0])
        plausible_comparison = get_sentence_data(item_sentences, comparison_cols[1])
        row = {
            "item": int(item)
        }
        for column_name in surprisal_cols: # should be in format {model}_surprisal
            row[f"{column_name}_surprisal_effect"] = implausible_comparison[column_name].values[0] - plausible_comparison[column_name].values[0]
        diffs.append(row)
    expt_effects = pd.DataFrame(diffs)
    expt_effects['condition'] = condition_name # experiments had both reversal and comparison conditions.
    return expt_effects

def get_sentence_data(item_data : pd.DataFrame, sentence_type : str):
    return item_data[item_data['condition'] == sentence_type]

def reversal_surprisal_effect(data: pd.DataFrame, surprisal_cols: List[str]):
    # for Ettinger reversal items
    item_ids = data['item'].str.split("-").apply(lambda lst: lst[0]).unique()
    diffs = []
    for item in item_ids:
        item_sentences = data[data['item'].str.contains(item)]
        canonical = item_sentences[item_sentences['item'] == item + "-a"]
        reverse = item_sentences[item_sentences['item'] == item + "-b"]
        row = {
            "item": int(item),
            "verb":canonical['target'].values[0],
            "canonical_context" : canonical['context'].values[0],
            "reversed_context": reverse['context'].values[0],
            "canonical_cloze": canonical['tgt_cloze'].values[0],
            "reversed_cloze": reverse['tgt_cloze'].values[0],
        }
        for column_name in surprisal_cols: # should be in format {model}_surprisal
            row[f"canonical_{column_name}"] = canonical[column_name].values[0],
            row[f"reversed_{column_name}"] = reverse[column_name].values[0],
            row[f"{column_name}_effect"] = reverse[column_name].values[0] - canonical[column_name].values[0]
        diffs.append(row)
    reversal_effects = pd.DataFrame(diffs)
    return reversal_effects

def cloze_surprisal(row, model, cloze_col, is_bi):
    sentence = row['context'].replace("[MASK]", row[cloze_col])
    return word_final_surprisal(model, sentence, bi = is_bi)
