import tkinter as tk
from tkinter import filedialog
import threading
from count_display import run_display_program
from process_data import data_run_program
from train_model import run
from classify import run_classify
import json
import sys
import os
import numpy as np
import warnings

warnings.filterwarnings('ignore')
model_path = os.path.abspath('./public/yolo11x-pose.pt')
file_path = os.path.abspath('./public/data.csv')

def numpy_to_list(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, list):
        return [numpy_to_list(item) for item in obj]
    return obj

def run_program(video_path, hand_choice, load_saved_models=True):
    # 确保视频路径是绝对路径
    video_path = os.path.abspath(video_path)
    print(f"处理视频: {video_path}")
    print(f"选择手臂: {hand_choice}")
    print(f"模型路径: {model_path}")
    print(f"数据文件路径: {file_path}")

    point1 = []
    if hand_choice == "left":
        point1 = [5, 7, 9]
        point2 = [7, 5, 11]
        first_peak_frame, last_peak_frame, aligned_df, std_csv, output_p = data_run_program(video_path, file_path, model_path, point1, point2)
    else:
        point1 = [6, 8, 10]
        point2 = [8, 6, 12]
        first_peak_frame, last_peak_frame, aligned_df, std_csv, output_p = data_run_program(video_path, file_path, model_path, point1, point2)
    
    print(f"数据处理完成: first_peak_frame={first_peak_frame}, last_peak_frame={last_peak_frame}")
    
    model1, device = run(file_path, load_saved_model=load_saved_models)
    model2, label_encoder = run_classify(file_path, load_saved_model=load_saved_models)
    
    print("开始运行显示程序")
    case_arr, score_arr, output_arr = run_display_program(model1, model2, device, first_peak_frame, last_peak_frame, model_path, video_path, point1, aligned_df, std_csv, output_p, label_encoder)
    
    # 转换 NumPy 数组为 Python 列表
    case_arr = numpy_to_list(case_arr)
    score_arr = numpy_to_list(score_arr)
    output_arr = numpy_to_list(output_arr)
    
    return case_arr, score_arr, output_arr

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Usage: python process_video.py <video_path> <hand_choice>"}))
        sys.exit(1)
    
    video_path = sys.argv[1]
    hand_choice = sys.argv[2]
    
    try:
        case_arr, score_arr, output_arr = run_program(video_path, hand_choice)
        result = {
            "case_arr": case_arr,
            "score_arr": score_arr,
            "output_arr": output_arr
        }
        print(json.dumps(result))
    except Exception as e:
        import traceback
        error_msg = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_msg), file=sys.stderr)
        sys.exit(1)
    