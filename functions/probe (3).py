# -*- coding: utf-8 -*-
"""probe.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1yHhuSFNMqNtJG2MGp0N_1Cp-WedMwRja
"""

from typing import List
import numpy as np
from minicons import cwe
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForMaskedLM
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score

def load_model(model_name):
    return cwe.CWE(model_name)

def extract_verb_embeddings(model : cwe.CWE, sentences : List, verbs : List, probe_layer : int):
    model_input = [pair for pair in zip(sentences, verbs)]
    verb_embeddings = model.extract_representation(model_input, layer = probe_layer)
    return verb_embeddings

def extract_sentence_embeddings(model, tokenizer, sentences: List[str], probe_layer: int):
    # Check if the tokenizer has a padding token
    if tokenizer.pad_token is None:
        # If not, set the padding token
        if 'gpt' in tokenizer.name_or_path:
            tokenizer.pad_token = tokenizer.eos_token
        else:
            tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    # Modify sentences based on model type
    if 'gpt' in tokenizer.name_or_path:
        # Add [EOS] token to the beginning and end of each sentence for GPT models
        sentences = [f"{tokenizer.eos_token} {sentence} {tokenizer.eos_token}" for sentence in sentences]
    elif 'bert' in model.config.model_type:
        # No modification needed for BERT models, [CLS] token is automatically added by the tokenizer
        pass
    # Tokenize the sentences
    inputs = tokenizer(sentences, return_tensors='pt', padding=True, truncation=True)
    # Get the model outputs
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
    hidden_states = outputs.hidden_states[probe_layer]  # Select the specific layer's hidden states
    if 'bert' in model.config.model_type:
        # Use the [CLS] token for BERT-like models
        sentence_embeddings = hidden_states[:, 0, :]
    else:
        # For GPT-like models, use the last [EOS] token
        eos_token_id = tokenizer.eos_token_id
        eos_token_embeddings = []
        for i, input_id in enumerate(inputs['input_ids']):
            eos_token_indices = (input_id == eos_token_id).nonzero(as_tuple=True)[0]
            eos_token_index = eos_token_indices[-1].item()  # Use the last occurrence of the EOS token
            eos_token_embeddings.append(hidden_states[i, eos_token_index, :])
        sentence_embeddings = torch.stack(eos_token_embeddings)
    return sentence_embeddings

def run_probing(embeddings : List, labels : List):
    # return list of 10-fold cv accuracies
    x = embeddings
    y = np.array(labels)
    kf = KFold(n_splits = 10, shuffle = True)
    accuracies = []
    for train_index, test_index in kf.split(x):
        model = LogisticRegression(max_iter = 500, solver = "liblinear")
        X_train, X_test = x[train_index], x[test_index]
        y_train, y_test = y[train_index], y[test_index]
        model.fit(X_train, y_train)
        test_pred = model.predict(X_test)
        accuracies.append(accuracy_score(y_test, test_pred))
    return accuracies