import os
import shutil
import sys
import time
from math import ceil

import cv2
from tqdm import tqdm


def extract_frame(video_path, interval=1):
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
    print(f"视频帧数为：{fps}，总帧数为：{frame_count}")

    second = 0
    for _ in tqdm(range(ceil(frame_count/fps/interval)), desc="抽帧"):
        vidcap.set(cv2.CAP_PROP_POS_MSEC, second*1000)
        (frameState, frame) = vidcap.read()
        output_pic_name = f"{str(second).zfill(5)}.jpg"
        if not frameState:
            break
        cv2.imwrite(output_pic_name, frame)
        yield (os.path.join(output_pic_dir), os.path.abspath(output_pic_name))
        second += interval

    print("抽帧处理完毕...")
    vidcap.release()

    os.chdir(path_)


def invoke_extract_frame(video_path, interval=1):
    for _ in extract_frame(video_path, interval):
        pass


if __name__ == '__main__':
    video_path = sys.argv[1]
    invoke_extract_frame(video_path, interval=1)
