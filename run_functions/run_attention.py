# -*- coding: utf-8 -*-
"""run_attention_clean.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1HiMrY3XorMUmP0snyNm4D9V9DlkF4nYi

# Run attention analysis on GPT2-small
"""

import pandas as pd

df_all = pd.read_csv(f'/content/drive/MyDrive/LLM_role-reversal/RoleReversalLM-main/data/df_comb.csv')
df = df_all[(df_all.exp == "WY") & ((df_all['type'] == "substitution") | (df_all['type'] == "reversal"))]

import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained('gpt2')

# Function to get token indices for matching sequences of subtokens
def get_matching_subtoken_indices(sentence_tokens, word):
    word_tokens = tokenizer.tokenize(word)
    indices = []
    i = 0
    while i < len(sentence_tokens):
        if sentence_tokens[i:i+len(word_tokens)] == word_tokens:
            indices.extend(range(i, i+len(word_tokens)))
            i += len(word_tokens)
        else:
            i += 1
    return indices

# Function to process each group of sentences
def process_group(group, model):
    num_layers = model.config.n_layer
    num_heads = model.config.n_head

    # Initialize sums for averaging
    layer_attn_to_agent = np.zeros((num_layers, num_heads))
    layer_attn_to_patient = np.zeros((num_layers, num_heads))

    # First pass to calculate the average attention weights
    for _, row in group.iterrows():
        sentence = row['sentence']
        agent = " " + row['agent']
        patient = " " + row['patient']
        target = " " + row['target']

        inputs = tokenizer(sentence, return_tensors='pt')
        outputs = model(**inputs)

        # Tokenize sentence
        sentence_tokens = tokenizer.tokenize(sentence)

        # Get token indices
        agent_indices = get_matching_subtoken_indices(sentence_tokens, agent)
        patient_indices = get_matching_subtoken_indices(sentence_tokens, patient)
        target_indices = get_matching_subtoken_indices(sentence_tokens, target)

        # Get attention weights
        attentions = outputs.attentions

        for layer in range(num_layers):
            attn_tensor = attentions[layer].squeeze(0)  # Shape: (num_heads, seq_len, seq_len)

            for head in range(num_heads):
                attn_weights = attn_tensor[head]  # Shape: (seq_len, seq_len)
                attn_to_agent = attn_weights[target_indices][:, agent_indices].sum().item() if agent_indices else 0.0
                attn_to_patient = attn_weights[target_indices][:, patient_indices].sum().item() if patient_indices else 0.0

                layer_attn_to_agent[layer, head] += attn_to_agent
                layer_attn_to_patient[layer, head] += attn_to_patient

    # Average the attention values across sentences in the group
    layer_attn_to_agent /= len(group)
    layer_attn_to_patient /= len(group)

    # Find the layer and head with maximum average attention
    max_agent_layer, max_agent_head = np.unravel_index(layer_attn_to_agent.argmax(), layer_attn_to_agent.shape)
    max_patient_layer, max_patient_head = np.unravel_index(layer_attn_to_patient.argmax(), layer_attn_to_patient.shape)

    # Second pass to get the attention values from the max layer and head for each sentence
    max_attn_to_agent = []
    max_attn_to_patient = []
    agent_layer_patient_attn = []
    patient_layer_agent_attn = []

    for _, row in group.iterrows():
        sentence = row['sentence']
        agent = " " + row['agent']
        patient = " " + row['patient']
        target = " " + row['target']

        inputs = tokenizer(sentence, return_tensors='pt')
        outputs = model(**inputs)

        # Tokenize sentence
        sentence_tokens = tokenizer.tokenize(sentence)

        # Get token indices
        agent_indices = get_matching_subtoken_indices(sentence_tokens, agent)
        patient_indices = get_matching_subtoken_indices(sentence_tokens, patient)
        target_indices = get_matching_subtoken_indices(sentence_tokens, target)

        # Get attention weights
        attentions = outputs.attentions

        attn_tensor = attentions[max_agent_layer].squeeze(0)
        attn_weights = attn_tensor[max_agent_head]  # Shape: (seq_len, seq_len)
        attn_to_agent = attn_weights[target_indices][:, agent_indices].sum().item() if agent_indices else 0.0
        attn_to_patient_from_agent_layer = attn_weights[target_indices][:, patient_indices].sum().item() if patient_indices else 0.0

        attn_tensor = attentions[max_patient_layer].squeeze(0)
        attn_weights = attn_tensor[max_patient_head]  # Shape: (seq_len, seq_len)
        attn_to_patient = attn_weights[target_indices][:, patient_indices].sum().item() if patient_indices else 0.0
        attn_to_agent_from_patient_layer = attn_weights[target_indices][:, agent_indices].sum().item() if agent_indices else 0.0

        max_attn_to_agent.append(attn_to_agent)
        max_attn_to_patient.append(attn_to_patient)
        agent_layer_patient_attn.append(attn_to_patient_from_agent_layer)
        patient_layer_agent_attn.append(attn_to_agent_from_patient_layer)

    group['max_attn_to_agent'] = max_attn_to_agent
    group['max_attn_to_patient'] = max_attn_to_patient
    group['agent_layer_head'] = [(max_agent_layer, max_agent_head)] * len(group)
    group['patient_layer_head'] = [(max_patient_layer, max_patient_head)] * len(group)
    group['agent_layer_patient_attn'] = agent_layer_patient_attn
    group['patient_layer_agent_attn'] = patient_layer_agent_attn

    return group

def process_and_visualize_attention(model_name, df):
    print(f"\nProcessing model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(model_name, output_attentions=True)
    type_plausibility_groups = df.groupby(['type', 'plausibility'])

    processed_dfs = []

    for (group_name, plausibility), group in type_plausibility_groups:
        print(f"\nProcessing group: {group_name}, Plausibility: {plausibility}")
        processed_group = process_group(group, model)
        processed_dfs.append(processed_group)

    return pd.concat(processed_dfs)

df = process_and_visualize_attention('gpt2', df)

print(df.head())
df.to_csv(f'~/results/attn_gpt2.csv')

"""# Run attention analysis on RoBERTa-large"""

import pandas as pd

df_all = pd.read_csv(f'/content/drive/MyDrive/LLM_role-reversal/RoleReversalLM-main/data/df_comb.csv')
df = df_all[(df_all.exp == "WY") & ((df_all['type'] == "substitution") | (df_all['type'] == "reversal"))]

import numpy as np
from transformers import AutoTokenizer, AutoModel

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained('roberta-large')

# Function to get token indices for matching sequences of subtokens
def get_matching_subtoken_indices(sentence_tokens, word):
    word_tokens = tokenizer.tokenize(word)
    indices = []
    i = 0
    while i < len(sentence_tokens):
        if sentence_tokens[i:i+len(word_tokens)] == word_tokens:
            indices.extend(range(i, i+len(word_tokens)))
            i += len(word_tokens)
        else:
            i += 1
    return indices

# Function to process each group of sentences
def process_group(group, model):
    num_layers = model.config.num_hidden_layers
    num_heads = model.config.num_attention_heads

    # Initialize sums for averaging
    layer_attn_to_agent = np.zeros((num_layers, num_heads))
    layer_attn_to_patient = np.zeros((num_layers, num_heads))

    # First pass to calculate the average attention weights
    for _, row in group.iterrows():
        sentence = row['sentence']
        agent = " " + row['agent']
        patient = " " + row['patient']
        target = " " + row['target']

        inputs = tokenizer(sentence, return_tensors='pt')
        outputs = model(**inputs)

        # Tokenize sentence
        sentence_tokens = tokenizer.tokenize(sentence)

        # Get token indices
        agent_indices = get_matching_subtoken_indices(sentence_tokens, agent)
        patient_indices = get_matching_subtoken_indices(sentence_tokens, patient)
        target_indices = get_matching_subtoken_indices(sentence_tokens, target)

        # Get attention weights
        attentions = outputs.attentions

        for layer in range(num_layers):
            attn_tensor = attentions[layer].squeeze(0)  # Shape: (num_heads, seq_len, seq_len)

            for head in range(num_heads):
                attn_weights = attn_tensor[head]  # Shape: (seq_len, seq_len)
                attn_to_agent = attn_weights[target_indices][:, agent_indices].sum().item() if agent_indices else 0.0
                attn_to_patient = attn_weights[target_indices][:, patient_indices].sum().item() if patient_indices else 0.0

                layer_attn_to_agent[layer, head] += attn_to_agent
                layer_attn_to_patient[layer, head] += attn_to_patient

    # Average the attention values across sentences in the group
    layer_attn_to_agent /= len(group)
    layer_attn_to_patient /= len(group)

    # Find the layer and head with maximum average attention
    max_agent_layer, max_agent_head = np.unravel_index(layer_attn_to_agent.argmax(), layer_attn_to_agent.shape)
    max_patient_layer, max_patient_head = np.unravel_index(layer_attn_to_patient.argmax(), layer_attn_to_patient.shape)

    # Second pass to get the attention values from the max layer and head for each sentence
    max_attn_to_agent = []
    max_attn_to_patient = []
    agent_layer_patient_attn = []
    patient_layer_agent_attn = []

    for _, row in group.iterrows():
        sentence = row['sentence']
        agent = " " + row['agent']
        patient = " " + row['patient']
        target = " " + row['target']

        inputs = tokenizer(sentence, return_tensors='pt')
        outputs = model(**inputs)

        # Tokenize sentence
        sentence_tokens = tokenizer.tokenize(sentence)

        # Get token indices
        agent_indices = get_matching_subtoken_indices(sentence_tokens, agent)
        patient_indices = get_matching_subtoken_indices(sentence_tokens, patient)
        target_indices = get_matching_subtoken_indices(sentence_tokens, target)

        # Get attention weights
        attentions = outputs.attentions

        attn_tensor = attentions[max_agent_layer].squeeze(0)
        attn_weights = attn_tensor[max_agent_head]  # Shape: (seq_len, seq_len)
        attn_to_agent = attn_weights[target_indices][:, agent_indices].sum().item() if agent_indices else 0.0
        attn_to_patient_from_agent_layer = attn_weights[target_indices][:, patient_indices].sum().item() if patient_indices else 0.0

        attn_tensor = attentions[max_patient_layer].squeeze(0)
        attn_weights = attn_tensor[max_patient_head]  # Shape: (seq_len, seq_len)
        attn_to_patient = attn_weights[target_indices][:, patient_indices].sum().item() if patient_indices else 0.0
        attn_to_agent_from_patient_layer = attn_weights[target_indices][:, agent_indices].sum().item() if agent_indices else 0.0

        max_attn_to_agent.append(attn_to_agent)
        max_attn_to_patient.append(attn_to_patient)
        agent_layer_patient_attn.append(attn_to_patient_from_agent_layer)
        patient_layer_agent_attn.append(attn_to_agent_from_patient_layer)

    group['max_attn_to_agent'] = max_attn_to_agent
    group['max_attn_to_patient'] = max_attn_to_patient
    group['agent_layer_head'] = [(max_agent_layer, max_agent_head)] * len(group)
    group['patient_layer_head'] = [(max_patient_layer, max_patient_head)] * len(group)
    group['agent_layer_patient_attn'] = agent_layer_patient_attn
    group['patient_layer_agent_attn'] = patient_layer_agent_attn

    return group

# Process each type and plausibility group
def process_and_visualize_attention(model_name, df):
    print(f"\nProcessing model: {model_name}")
    model = AutoModel.from_pretrained(model_name, output_attentions=True)
    type_plausibility_groups = df.groupby(['type', 'plausibility'])

    processed_dfs = []

    for (group_name, plausibility), group in type_plausibility_groups:
        print(f"\nProcessing group: {group_name}, Plausibility: {plausibility}")
        processed_group = process_group(group, model)
        processed_dfs.append(processed_group)

    return pd.concat(processed_dfs)

# Run for RoBERTa large model
df = process_and_visualize_attention('roberta-large', df)

# Show the updated dataframe with new columns
print(df.head())
df.to_csv(f'~/results/attn_roberta-large.csv')