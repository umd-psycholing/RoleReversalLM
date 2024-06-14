# Argument Roles in Language Models

This repository contains all the data and scripts used for the paper, "A Psycholinguistic Evaluation of Language Models' Sensitivity to Argument Roles".

The "data" folder contains all the stimuli sets used to run the analyses in the paper.
The scripts in "run_functions" will output the results and plots reported in the paper.
They require importing functions that are stored in the "functions" folder.

Add the required dependencies with `pip install -r requirements.txt`.
To replicate Experiment 1, run the following:

```
chmod +x run_functions/compute_all_surprisals.sh
./compute_all_surprisals.sh
python run_functions/run_surprisal.py
```

To replicate Experiments 2 and 3, run `run_functions/run_probe.py` and `run_functions/run_attention.py`, respectively.