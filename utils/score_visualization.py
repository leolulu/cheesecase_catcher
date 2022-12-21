import math
import matplotlib.pyplot as plt
from matplotlib.pyplot import MultipleLocator   # type: ignore


def prepare_score_for_visualization(porn_score_result_path):
    with open(porn_score_result_path, 'r', encoding='utf-8') as f:
        data = f.read().strip().split('\n')
        data = [i.split('\t') for i in data]
        data = [[i[0].replace('_', ':'), float(i[1])] for i in data]
    return data


def save_bar_visualization(data, save_name):
    x = [i[0] for i in data]
    y = [i[1] for i in data]
    color = ['crimson' if i >= 80 else '#1f77b4' for i in y]

    x_inch = len(data)/3
    print(f"当前data数量为{len(data)}，x_inch为{x_inch}")
    y_inch = 6
    dpi = 200
    if x_inch * dpi > 65535:
        ratio = x_inch * dpi / 65535
        dpi = dpi / ratio
        print(f"图太大了，dpi调整为：{dpi}")

    fig, ax = plt.subplots(figsize=(x_inch, y_inch), dpi=dpi)
    ax.bar(x, y, width=1, edgecolor="white", linewidth=0.4, color=color)
    ax.set(ylim=(0, 100))
    plt.xlabel("time")
    plt.ylabel('score')
    plt.xticks(rotation=45, fontsize=40)
    plt.axhline(80, linestyle='--', c='gray')
    plt.margins(x=0)
    locator = MultipleLocator(3)
    locator.MAXTICKS = int(max(math.ceil(len(x)/3)+3, locator.MAXTICKS))
    ax.xaxis.set_major_locator(locator)

    plt.savefig(save_name+'.pdf', bbox_inches='tight')
    plt.savefig(save_name+'.png', bbox_inches='tight')


if __name__ == "__main__":
    import os
    result_txt_path = r"C:\Users\pro3\Downloads\porn_score_result.txt"
    data = prepare_score_for_visualization(result_txt_path)
    save_bar_visualization(
        data,
        os.path.splitext(result_txt_path)[0]
    )
