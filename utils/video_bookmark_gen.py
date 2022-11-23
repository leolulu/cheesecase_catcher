import os
import re
import subprocess
import sys

from tqdm import tqdm


def scene_change_detection(video_path, threshold=0.4):
    video_path = os.path.abspath(video_path)
    command = rf"""ffmpeg -i "{video_path}" -filter:v "select='gt(scene,{threshold})',showinfo" -f null - """
    print(f"开始检测场景转换: {command}")
    pbar = tqdm(total=get_duration(video_path), desc="转场识别")
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
    result_strs = []
    for line in iter(proc.stdout.readline, ''):  # type: ignore
        line = line.strip()
        result_strs.append(line)
        time_info_findinfo = re.findall(r"time=([0-9:.]+)", line)
        if len(time_info_findinfo) > 0:
            time_info = time_info_findinfo[0]
            # pbar.update(_string_to_seconds(time_info)-pbar.n)
            pbar.n = _string_to_seconds(time_info)
            pbar.refresh()

    pbar.close()
    return re.findall(r"pts_time:([0-9.]+)", '\n'.join(result_strs))


def get_duration(video_path):
    command = rf"""ffprobe "{video_path}" """
    print(f"开始检测视频时长: {command}")
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outs, errs = proc.communicate()
    duration_info = re.findall(r"Duration: ([0-9.:]+)", errs.decode())
    if len(duration_info) == 0:
        raise UserWarning("没有检测到视频时间！")
    duration_info = duration_info[0]
    seconds = _string_to_seconds(duration_info)
    print(f"视频时长为：{duration_info}，秒数为：{seconds}")
    return seconds


def _string_to_seconds(time_str):
    duration_info_without_milli = time_str.split('.')[0]
    (hour, minute, second) = duration_info_without_milli.split(':')
    seconds = int(hour)*3600 + int(minute)*60 + int(second)
    return seconds


def gen_bookmark(video_path, threshold=0.4):
    video_path = os.path.abspath(video_path)
    scene_change_timestamp = scene_change_detection(video_path, threshold)
    if len(scene_change_timestamp) == 0:
        print(f"没有转场被检测出，当前阈值为：{threshold}")
        return
    bookmark_str = "[Bookmark]\n"
    idx = 0

    for t in scene_change_timestamp:
        row = "{}={}*书签*\n".format(
            idx,
            int(float(t)*1000)
        )
        bookmark_str += row
        idx += 1
    bookmark_path = os.path.splitext(video_path)[0]+'.pbf'
    with open(bookmark_path, 'w', encoding='utf-8') as f:
        f.write(bookmark_str)
    print("处理完毕...")


if __name__ == '__main__':
    gen_bookmark(sys.argv[1])
