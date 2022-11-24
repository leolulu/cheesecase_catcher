import os
import shutil
import subprocess


def concat_video(folder_path, if_print=True):
    folder_path = os.path.abspath(folder_path)
    print(f"开始合并视频：{folder_path}")
    _cwd = os.getcwd()
    os.chdir(folder_path)
    if if_print:
        print(f"工作目录：{os.getcwd()}")

    if os.path.exists('filelist.txt'):
        os.remove('filelist.txt')
    with open('filelist.txt', 'a', encoding='utf-8') as f:
        for i in os.listdir('.'):
            if os.path.splitext(i)[-1] in ['.txt', '.log']:
                continue
            f.write(f"file '{i}'\n")
    file_name = f"{os.path.basename(folder_path)}_concat.mp4"
    log_path = os.path.abspath(os.path.join(folder_path, "concat_video.log"))
    command = f'ffmpeg -f concat -safe 0 -i filelist.txt -c copy -y "{file_name}" 2>>"{log_path}"'
    if if_print:
        print(f"指令：{command}")
    subprocess.call(command, shell=True)
    shutil.move(file_name, os.path.dirname(folder_path))
    os.chdir(_cwd)
    return os.path.join(os.path.dirname(folder_path), file_name)
