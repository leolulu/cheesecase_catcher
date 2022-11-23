import os
import re
import shutil
import subprocess
import sys
import time
from math import ceil

import cv2
from tqdm import tqdm


def extract_frame_opencv_ffmpeg(video_path, fps=1.0):
    from utils.bookmark_gen import get_duration, string_to_seconds
    video_path = os.path.abspath(video_path)
    base_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_pic_dir = os.path.join(base_dir, video_name)
    if os.path.exists(output_pic_dir):
        shutil.rmtree(output_pic_dir)
        time.sleep(2)
    os.mkdir(output_pic_dir)

    video_duration = get_duration(video_path)
    yield (output_pic_dir, video_duration)

    command = f'ffmpeg -i "{video_path}" -r {fps} -q:v 2 -f image2 "{output_pic_dir}/%08d.jpg"'
    print(f"开始使用ffmpeg进行视频抽帧: {command}")
    pbar = tqdm(total=video_duration, desc="ffnoeg抽帧")
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
    for line in iter(proc.stdout.readline, ''):  # type: ignore
        line = line.strip()
        time_info_findinfo = re.findall(r"time=([0-9:.]+)", line)
        if len(time_info_findinfo) > 0:
            time_info = time_info_findinfo[0]
            pbar.n = string_to_seconds(time_info)
            pbar.refresh()
    pbar.close()
    print("抽帧处理完毕...")


def extract_frame_opencv(video_path, interval=1):
    """
    Args:
        video_path (str): abs path of video file
        interval (int): interval in second
    """
    video_path = os.path.abspath(video_path)
    base_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_pic_dir = os.path.join(base_dir, video_name)
    if os.path.exists(output_pic_dir):
        shutil.rmtree(output_pic_dir)
        time.sleep(2)
    os.mkdir(output_pic_dir)
    path_ = os.getcwd()
    os.chdir(output_pic_dir)
    vidcap = cv2.VideoCapture(video_path)
    isOpened = vidcap.isOpened()
    if not isOpened:
        raise UserWarning("视频没有正常打开！")
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    frame_count = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    task_count = ceil(frame_count/fps/interval)
    print(f"视频帧数为：{fps}，总帧数为：{frame_count}")

    second = 0
    for _ in tqdm(range(task_count), desc="opencv抽帧"):
        vidcap.set(cv2.CAP_PROP_POS_MSEC, second*1000)
        (frameState, frame) = vidcap.read()
        output_pic_name = f"{time_format(second)}.jpg"
        if not frameState:
            break
        cv2.imwrite(output_pic_name, frame)
        yield (os.path.join(output_pic_dir), os.path.abspath(output_pic_name), task_count)
        second += interval

    print("抽帧处理完毕...")
    vidcap.release()

    os.chdir(path_)


def time_format(total_second):
    hour = int(total_second/3600)
    total_second -= 3600 * hour
    minute = int(total_second/60)
    total_second -= 60 * minute
    hour = str(hour).zfill(2)
    minute = str(minute).zfill(2)
    second = str(total_second).zfill(2)
    return f"{hour}_{minute}_{second}"


def invoke_extract_frame_opencv(video_path, interval=1):
    for _ in extract_frame_opencv(video_path, interval):
        pass


if __name__ == '__main__':
    video_path = sys.argv[1]
    invoke_extract_frame_opencv(video_path, interval=1)
