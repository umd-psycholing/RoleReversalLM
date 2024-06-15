import os
import json
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()
sns.set_palette('colorblind')

from functions import surprisal

surprisal_path = "../data/surprisal_results"
results = [file for file in os.listdir(surprisal_path) if "clean.csv" in file and "con" not in file]
# adding WY control items later
with open("../data/stimulus_config.json", "r") as file:
    stimulus_config = json.load(file)

def get_surprisal_cols(df):
    return [column for column in df.columns if "surprisal" in column]
all_surprisal_effects = []
for filename in results:
    df = pd.read_csv(os.path.join(surprisal_path, filename))
    config = stimulus_config[filename]
    surprisal_cols = get_surprisal_cols(df)
    expt = filename.split("_clean.csv")[0]
    reversal_data = surprisal.surprisal_effects(df, surprisal_cols, config['reversal'], f"Reversal")
    reversal_data['expt'] = expt
    comparison_data = surprisal.surprisal_effects(df, surprisal_cols, config['comparison'], f"{config['comparison_condition']}")
    comparison_data['expt'] = expt
    all_surprisal_effects.append(reversal_data)
    all_surprisal_effects.append(comparison_data)

# adding the control items from chow et al separately
wy_control = pd.read_csv(os.path.join(surprisal_path, "WY_con_clean.csv"))
surprisal_cols = get_surprisal_cols(wy_control)
control_data = surprisal.surprisal_effects(df, surprisal_cols, config['comparison'], f"{config['comparison_condition']}")
control_data['expt'] = 'WY'
all_surprisal_effects.append(control_data)
surprisal_effects = pd.concat(all_surprisal_effects)

surprisal_effects.to_csv(os.path.join(surprisal_path, "surprisal_effects.csv"), index = False)

all_effects = pd.read_csv(os.path.join(surprisal_path, "surprisal_effects.csv"))
all_effects.drop("item", axis = 1, inplace = True)

# relabeling the experiments based on paper
def relabel_experiment(row):
    expt, condition = row['expt'], row['condition']
    if expt == "WY":
        if condition == "Reversal":
            return "swap-arguments"
        elif condition == "Substitution":
            return "replace-argument"
        else:
            return "Chow et al Control"
    elif expt == "KO":
        if condition == "Reversal":
            return "change-verb"
        else:
            return "Kim & Osterhout Control"
    else:
        return "EXCLUDE"

melted = pd.melt(all_effects, id_vars = ["expt", "condition"])
melted.columns = ["expt", "condition", "Model", "Surprisal Effect"]
melted['condition'] = melted.apply(relabel_experiment, axis = 1)

# Plotting for the main experimental effects
os.mkdir("figures")
plt.rc('font', size=48)           # controls default text sizes
plt.rc('axes', titlesize=48)      # fontsize of the axes title
plt.rc('axes', labelsize=48)      # fontsize of the x and y labels
plt.rc('xtick', labelsize=48)     # fontsize of the tick labels
plt.rc('ytick', labelsize=48)     # fontsize of the tick labels
plt.rc('figure', titlesize=48)    # fontsize of the figure title

expt_conditions = ['swap-arguments', 'change-verb', 'replace-argument']
final_effect_table = melted[melted['condition'].isin(expt_conditions)]
g = sns.FacetGrid(final_effect_table, col = "condition", hue = "Model", height = 15, sharex=False, sharey=True, col_wrap=3)
g.map(sns.barplot, "Model", "Surprisal Effect", order = model_names)
g.set_titles(template="{col_name}", size = 64)
g.set_axis_labels("", "Surprisal Effect")
for ax in g.axes.flatten():
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
g.fig.subplots_adjust(wspace=0.2, hspace=0.35)
plt.subplots_adjust(left=0.2, right=0.8) 
plt.figure.savefig("figures/surprisal_effects.png")

# Plotting the control/cloze conditions
cloze_conditions = ['Kim & Osterhout Control', 'Chow et al Control']
cloze_effect_table = melted[melted['condition'].isin(cloze_conditions)]
g = sns.FacetGrid(cloze_effect_table, col = "condition", col_order=expt_conditions, hue = "Model", height = 15, sharex=False, sharey=True, col_wrap=3)
g.map(sns.barplot, "Model", "Surprisal Effect", order = model_names)
g.set_titles(template="{col_name}", size = 64)
g.set_axis_labels("", "Surprisal Effect")
for ax in g.axes.flatten():
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
g.fig.subplots_adjust(wspace=0.2, hspace=0.35)  # Adjust wspace for horizontal space and hspace for vertical space

# Center the plots by adjusting the left and right margins
plt.subplots_adjust(left=0.2, right=0.8)  # Adjust these values to center the plots horizontally
plt.figure.savefig("figures/control_surprisal_effects.png")

