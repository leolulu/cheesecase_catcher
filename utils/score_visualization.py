
import matplotlib.pyplot as plt
from matplotlib.pyplot import MultipleLocator   # type: ignore


def prepare_score_for_visualization(porn_score_result_path):
    with open(porn_score_result_path, 'r', encoding='utf-8') as f:
        data = f.read().strip().split('\n')
        data = [i.split('\t') for i in data]
        data = [[i[0].replace('_', ':'), float(i[1])] for i in data]
    return data


def save_bar_visualization(data, save_path):
    x = [i[0] for i in data]
    y = [i[1] for i in data]
    color = ['crimson' if i >= 80 else '#1f77b4' for i in y]

    fig, ax = plt.subplots()
    ax.bar(x, y, width=1, edgecolor="white", linewidth=0.4, color=color)
    ax.set(ylim=(0, 100))
    fig.set_figwidth(len(data)/3)
    fig.set_figheight(6)
    plt.xlabel("time")
    plt.ylabel('score')
    plt.xticks(rotation=45, fontsize=40)
    plt.axhline(80, linestyle='--', c='gray')
    plt.margins(x=0)
    ax.xaxis.set_major_locator(MultipleLocator(3))

    plt.savefig(save_path, dpi=200, bbox_inches='tight')
