#!/bin/bash

DATA=("KO_clean.csv" "LE_clean.csv" "WY_clean.csv" "WY_rev_sub_clean.csv")
MODELS=("gpt2" "gpt2-medium" "gpt2-large" "bert-base-uncased" "bert-large-uncased" "roberta-base" "roberta-large")

mkdir ..data/surprisal_results

for EXPT in "${DATA[@]}"
do
    # the script modifies the df inplace
    touch "data/surprisal_results/${EXPT}"
    cp ..data/${EXPT} ..data/surprisal_results/${EXPT}
    RESULT_PATH=data/${EXPT} data/surprisal_results/${EXPT}
    echo "Processing experiment: ${RESULT_PATH}"
    for MODEL in "${MODELS[@]}"
    do
        echo "Generating Surprisals for model: ${MODEL}"
        python surprisal_for_model.py --model "${MODEL}" --data "${RESULT_PATH}"
        if [ $? -eq 0 ]; then
            echo "Successfully processed ${MODEL}. Output saved to ${RESULT_PATH}"
        else
            echo "Failed to process ${MODEL}."
        fi
    done
done