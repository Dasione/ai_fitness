import os
import cv2
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from ultralytics import solutions, YOLO
import datetime
from scipy.signal import find_peaks
import time
import threading
import queue
import base64
import asyncio
import websockets
import json
import warnings

warnings.filterwarnings('ignore')
model_path_data = './public/yolo11x-pose.pt'

def plot_angles_with_peaks(angles, peaks):
    """
    绘制角度曲线并标注极大值点。

    Args:
        angles (list): 角度数组。
        peaks (list): 极大值点的索引。
    """
    plt.figure(figsize=(10, 6))
    plt.plot(angles, label="Angle", color="blue")
    plt.scatter(peaks, [angles[p] for p in peaks], color="red", label="Peaks", zorder=5)
    plt.xlabel("Frame Index")
    plt.ylabel("Angle (degrees)")
    plt.title("Angle Variation with Peaks")
    plt.legend()
    plt.grid()
    # plt.show()

def select_roi_auto(frame, model_path):
    """自动选择最大人体检测框作为ROI区域"""
    model = YOLO(model_path)
    results = model.predict(frame, verbose=False)
    
    # 提取人体检测框（类别0为人）
    boxes = results[0].boxes.xyxy.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()
    person_boxes = boxes[classes == 0]

    if len(person_boxes) == 0:
        raise ValueError("⚠️ 未检测到人体")

    # 找到面积最大的检测框
    areas = (person_boxes[:, 2] - person_boxes[:, 0]) * (person_boxes[:, 3] - person_boxes[:, 1])
    max_idx = np.argmax(areas)
    x1, y1, x2, y2 = person_boxes[max_idx].astype(int)

    # 返回矩形坐标和边界框信息
    return {
        "points": np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.int32),
        "bbox": (x1, y1, x2, y2)
    }

def create_mask(frame, points):
    """
    根据选择的点创建掩码
    """
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    points_array = np.array(points, dtype=np.int32)
    cv2.fillPoly(mask, [points_array], 255)
    return mask

def process_video(video_path, point1, point2, output_csv, output_p, alingn_csv, std_csv, std, model_path_data):
    """
    处理单个视频，提取角度并根据极大值分割视频，同时记录角度数据。
    """
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), "Error reading video file"
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, 59)
    # 读取第60帧用于选择ROI
    ret, first_frame = cap.read()
    if not ret:
        print("无法读取视频第60帧")
        return
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    try:
        # 使用自动选择ROI替换手动选择
        roi_info = select_roi_auto(first_frame, model_path_data)
        roi_points = roi_info["points"].tolist()  # 转换为列表格式
        x1, y1, x2, y2 = roi_info["bbox"]
    except Exception as e:
        print(str(e))
        return
    
    # 创建掩码
    mask = create_mask(first_frame, roi_points)
    
    w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # 保存ROI信息到文件
    roi_info = {
        'points': roi_points,
        'width': w,
        'height': h
    }
    with open('roi_info.json', 'w') as f:
        json.dump(roi_info, f)
    
    gym1 = solutions.AIGym(
        model=model_path_data,
        show=False,
        line_width=1,
        up_angle=120.0,
        down_angle=80.0,
        kpts=point1,
        verbose=False
    )
    gym2 = solutions.AIGym(
        model=model_path_data,
        show=False,
        line_width=1,
        up_angle=120.0,
        down_angle=80.0,
        kpts=point2,
        verbose=False
    )
    
    angles_group1 = []
    angles_group2 = []
    frames = []
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        # 应用掩码
        masked_frame = frame.copy()
        masked_frame[mask == 0] = 0  # 将非ROI区域设为黑色
        
        gym1.monitor(masked_frame)
        gym2.monitor(masked_frame)
        angle1 = 0
        angle2 = 0
        if point1 == [6, 8, 10]:
            angle1 = gym1.angle[0] if isinstance(gym1.angle, (list, tuple)) else 0
            angle2 = gym2.angle[0] if isinstance(gym2.angle, (list, tuple)) else 0
        elif point1 == [5, 7, 9]:
            angle1 = gym1.angle[0] if isinstance(gym1.angle, (list, tuple)) else 0
            angle2 = gym2.angle[0] if isinstance(gym2.angle, (list, tuple)) else 0
        angles_group1.append(angle1)
        angles_group2.append(angle2)
        frames.append(frame)  # 保存原始帧
    cap.release()
    cv2.destroyAllWindows()
    # 查找极大值点并生成时间戳
    peaks = find_peaks(angles_group1, distance=20, prominence=10)[0]
    
    # 如果第一个点满足条件（角度大于120或小于80），将其添加到峰值列表中
    if angles_group1[0] > 120:
        peaks = np.concatenate(([0], peaks))

    # plot_angles_with_peaks(angles_group1, peaks)    
    # 筛选满足相邻峰间区域条件的峰点
    adjusted_peaks = []
    for i in range(len(peaks) - 1):
        start = peaks[i]
        end = peaks[i+1]
        segment = angles_group1[start:end+1]  # 包含两个峰点间的所有数据
        if np.max(segment) > 120 and np.min(segment) < 80:
            adjusted_peaks = peaks[i:]  # 找到第一个符合条件的峰点，截断数组
            break
    if len(adjusted_peaks) > 0:
        segment_ranges = []
        for i in range(len(adjusted_peaks) - 1):
            segment_ranges.append((adjusted_peaks[i], adjusted_peaks[i + 1]))
        
        # 检查最后一段动作的帧数
        last_segment_start = adjusted_peaks[-1]
        last_segment_end = len(frames) - 1
        last_segment_frames = last_segment_end - last_segment_start + 1
        
        if last_segment_frames >= 25 and last_segment_frames <= 100:  # 如果最后一段动作帧数在25-100帧之间，则保留
            segment_ranges.append((last_segment_start, last_segment_end))
            last_peak_frame = last_segment_end
        elif last_segment_frames > 100:  # 如果最后一段动作帧数大于100帧
            # 向前查找20帧，找到第一个角度大于120的位置
            search_start = max(last_segment_end - 20, last_segment_start)
            for i in range(last_segment_end, search_start - 1, -1):
                if angles_group1[i] > 120:
                    segment_ranges.append((last_segment_start, i))
                    last_peak_frame = i
                    break
            else:  # 如果没找到满足条件的点，使用原来的峰点
                last_peak_frame = last_segment_start
        else:  # 如果最后一段动作帧数小于25帧，则舍弃
            last_peak_frame = last_segment_start
    else:
        segment_ranges = []
        last_peak_frame = len(frames) - 1

    # 生成时间戳和总帧数
    timestamps = []
    total_frames_per_segment = []
    for start, end in segment_ranges:
        start_time = str(datetime.timedelta(seconds=start / fps))
        end_time = str(datetime.timedelta(seconds=end / fps))
        timestamps.append(f"{start_time}-{end_time}")
        total_frames_per_segment.append(end - start + 1)

    # 生成 segment_labels 和 segment_total_frames
    segment_labels = []
    segment_total_frames = []
    for frame_num in range(len(frames)):
        current_segment = None
        for seg_idx, (start, end) in enumerate(segment_ranges):
            if start <= frame_num <= end:
                current_segment = seg_idx
                break
        if current_segment is not None:
            segment_labels.append(timestamps[current_segment])
            segment_total_frames.append(total_frames_per_segment[current_segment])
        else:
            # 如果不在任何分段中（例如在峰点前），标记为无效
            segment_labels.append("invalid")
            segment_total_frames.append(0)

    # 生成数据集时过滤无效帧
    first_peak = adjusted_peaks[0] if len(adjusted_peaks) > 0 else 0
    all_data = [
        [
            segment_labels[frame_num],
            frame_num,
            "group1",
            angles_group1[frame_num],
            "original",
            segment_total_frames[frame_num]
        ]
        for frame_num in range(len(angles_group1))
        if frame_num >= first_peak and segment_labels[frame_num] != "invalid"
    ] + [
        [
            segment_labels[frame_num],
            frame_num,
            "group2",
            angles_group2[frame_num],
            "original",
            segment_total_frames[frame_num]
        ]
        for frame_num in range(len(angles_group2))
        if frame_num >= first_peak and segment_labels[frame_num] != "invalid"
    ]

    df = pd.DataFrame(
        all_data,
        columns=["segment_label", "frame_number", "angle_group", "angle_value", "categories", "segment_total_frames"]
    )

    df.to_csv(output_csv, index=False)

    """
    max_frames = df.groupby(['video_name', 'angle_group'])['frame_number'].max()
    a = max_frames.values
    quantile_75 = int(pd.Series(a).quantile(0.75))
    """

    clean_angles(df)
    processed_data = (
        df.groupby(['segment_label', 'angle_group'], group_keys=False)
        .apply(lambda group: process_video_data(group, 62))
    )
    processed_data.to_csv(output_p, index=False)

    std_df = get_std(std, std_csv)
    aligned_df = align_standard_data(std_df,processed_data,alingn_csv)

    return first_peak, last_peak_frame, aligned_df

def process_video_data(df, target_frames):
    frame_numbers = df['frame_number'].values
    angle_values = df['angle_value'].values
    segment_total_frames = df['segment_total_frames'].iloc[0]  # 获取该片段的总帧数

    if len(frame_numbers) > target_frames:  # 下采样
        indices = np.linspace(0, len(frame_numbers) - 1, target_frames, dtype=int)
    else:  # 补充
        indices = np.round(np.linspace(0, len(frame_numbers) - 1, target_frames)).astype(int)

    frame_numbers_resampled = np.arange(1, target_frames + 1)
    angle_values_resampled = angle_values[indices]

    return pd.DataFrame({
        'segment_label': df['segment_label'].iloc[0],  # 使用片段标识
        'frame_number': frame_numbers_resampled,
        'angle_group': df['angle_group'].iloc[0],
        'angle_value': angle_values_resampled,
        'categories': df['categories'].iloc[0],
        'segment_total_frames': segment_total_frames  # 添加总帧数列
    })

def clean_angles(df):
    """
    针对 DataFrame 中的角度数据进行清洗，消除 0 值并插值。
    
    参数:
        df: 包含以下列的 DataFrame
            - segment_label: 片段标识
            - frame_number: 帧号
            - angle_value: 角度值 (可能包含 0)
    
    返回:
        清洗后的 DataFrame，其中 0 值被替换或插值。
    """
    # 检查输入数据
    if df.empty:
        return df
        
    # 复制输入数据避免修改原始数据
    df_copy = df.copy()
    cleaned_data = []
    
    # 按 segment_label 分组处理
    for segment_label, group in df_copy.groupby("segment_label", as_index=False):
        angles = group["angle_value"].values
        non_zero_indices = np.nonzero(angles)[0]
        
        if len(non_zero_indices) == 0:
            print(f"Warning: Segment '{segment_label}' has all angle values as 0, skipping.")
            continue
            
        # 用第一个非零值填充开头的 0
        if non_zero_indices[0] > 0:
            angles[:non_zero_indices[0]] = angles[non_zero_indices[0]]
        
        # 用最后一个非零值填充结尾的 0
        if non_zero_indices[-1] < len(angles) - 1:
            angles[non_zero_indices[-1] + 1:] = angles[non_zero_indices[-1]]
        
        # 对中间的 0 值插值
        zero_indices = np.where(angles == 0)[0]
        for zero_index in zero_indices:
            # 查找左侧最近的非零值
            left = zero_index - 1
            while left >= 0 and angles[left] == 0:
                left -= 1

            # 查找右侧最近的非零值
            right = zero_index + 1
            while right < len(angles) and angles[right] == 0:
                right += 1

            if left >= 0 and right < len(angles):
                # 左右两侧均有非零值，取平均值
                angles[zero_index] = (angles[left] + angles[right]) / 2
            elif left >= 0:
                # 仅左侧有非零值
                angles[zero_index] = angles[left]
            elif right < len(angles):
                # 仅右侧有非零值
                angles[zero_index] = angles[right]
        
        # 更新处理后的角度值
        group_copy = group.copy()
        group_copy["angle_value"] = angles
        cleaned_data.append(group_copy)
    
    if not cleaned_data:
        print("Warning: No valid data after cleaning.")
        return pd.DataFrame(columns=df.columns)
    
    # 合并所有清洗后的数据，确保不会产生多级索引
    result = pd.concat(cleaned_data, ignore_index=True)
    
    return result

def get_std(data_path, std_csv):
    data = pd.read_csv(data_path)
    case0_data = data[data['categories'] == 'case0']
    # 按照视频名称、角度组和帧数进行分组
    grouped = case0_data[['video_name', 'angle_group', 'frame_number', 'angle_value']]
    # 计算每个组每帧的平均角度
    final_result = grouped.groupby(['angle_group', 'frame_number'])['angle_value'].mean().reset_index()
    # 获取标准平均角度
    standard_angles = final_result.pivot(index='frame_number', columns='angle_group', values='angle_value').reset_index()
    standard_angles.to_csv(std_csv, index=False)
    return standard_angles

def align_standard_data(std_df, video_df, dir):

    # 存储对齐后的数据
    aligned_data = []

    # 遍历视频片段数据，按片段对齐标准数据
    for segment_label, group in video_df.groupby("segment_label"):
        segment_frames = group["segment_total_frames"].iloc[0]  # 当前片段的总帧数

        # 存储每个角度组的对齐结果
        aligned_segment = {"frame_number": np.arange(1, segment_frames + 1)}

        for angle_group in std_df.columns:  # 遍历标准数据中的每个角度组
            std_angle_values = std_df[angle_group].values

            # 对标准片段进行插值处理
            if len(std_angle_values) > segment_frames:  # 如果标准片段帧数大于当前片段帧数，下采样
                indices = np.linspace(0, len(std_angle_values) - 1, segment_frames, dtype=int)
            else:  # 如果标准片段帧数小于当前片段帧数，上采样
                indices = np.round(np.linspace(0, len(std_angle_values) - 1, segment_frames)).astype(int)

            resampled_values = std_angle_values[indices]  # 拉伸或压缩后的标准角度值

            # 将对齐后的角度值存储到相应的列中
            aligned_segment[angle_group] = resampled_values

        # 转为 DataFrame 并添加到列表
        aligned_data.append(pd.DataFrame(aligned_segment))

    # 合并所有片段的对齐数据
    aligned_df = pd.concat(aligned_data, ignore_index=True)
    aligned_df.to_csv(dir, index=False)

    return aligned_df

def data_run_program(video_path_data, file_path_data, model_path_data, point1, point2):
    """
    视频处理入口
    """
    video_path = video_path_data
    output_csv = "angles.csv"
    output_p = "angles_p.csv"
    alingn_csv = "alingn.csv"
    std_csv = "std.csv"
    std = file_path_data
    first_peak_frame, last_peak_frame, aligned_df = process_video(video_path, point1, point2, output_csv, output_p, alingn_csv, std_csv, std, model_path_data)
    return first_peak_frame, last_peak_frame, aligned_df, std_csv, output_p

def draw_angle_info(frame, angle1, angle2, countdown=None, show_ui=True):
    """在画面上绘制角度信息和倒计时"""
    BAR_WIDTH = 300
    BAR_HEIGHT = 30
    MIN_ANGLE = 60
    MAX_ANGLE = 140
    ANGLE1_TOLERANCE = 5  # 角度1允许的误差值
    ANGLE2_MAX = 9
    ANGLE2_TOLERANCE = 1  # 角度2允许的误差值

    # 绘制倒计时（始终显示）
    if countdown is not None:
        text = str(int(countdown))
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 4, 8)
        cv2.putText(frame, text, 
                   ((frame.shape[1]-text_w)//2, (frame.shape[0]+text_h)//2),
                   cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 8, cv2.LINE_AA)
        return frame
    
    # 当不需要显示UI时直接返回
    if not show_ui:
        return frame

    # 创建半透明背景（覆盖两个进度条区域）
    overlay = frame.copy()
    cv2.rectangle(overlay, (15, 115), (22 + BAR_WIDTH, 195), (50, 50, 50), -1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    # ================= 第一个角度（大角度）的进度条 =================
    # 计算有效范围和容差区域
    effective_min = MIN_ANGLE - ANGLE1_TOLERANCE
    effective_max = MAX_ANGLE + ANGLE1_TOLERANCE
    clamped_angle = max(effective_min, min(angle1, effective_max))
    progress1 = (clamped_angle - effective_min) / (effective_max - effective_min)
    
    # 绘制外框
    cv2.rectangle(frame, (20, 120), (20 + BAR_WIDTH, 120 + BAR_HEIGHT), (255, 255, 255), 2)
    
    # 绘制容差区域（渐变效果）
    for x in range(20, 20 + BAR_WIDTH):
        ratio = (x - 20) / BAR_WIDTH
        color = (255, 255, 255)  # 默认白色
        if ratio < ANGLE1_TOLERANCE/(effective_max - MIN_ANGLE):
            color = (0, 255, 255)  # 最小值容差区（黄色）
        elif ratio > 1 - ANGLE1_TOLERANCE/(effective_max - MIN_ANGLE):
            color = (0, 255, 255)  # 最大值容差区（橙色）
        cv2.line(frame, (x, 122), (x, 120 + BAR_HEIGHT - 2), color, 1)
    
    # 绘制实际进度
    cv2.rectangle(frame, 
                 (20, 120), 
                 (20 + int(BAR_WIDTH * progress1), 120 + BAR_HEIGHT),
                 (0, 255, 0), -1)

    # 绘制刻度线（包含容差区域）
    for angle in [effective_min, MIN_ANGLE, 90, 120, MAX_ANGLE, effective_max]:
        pos_x = 20 + int(BAR_WIDTH * (angle - effective_min)/(effective_max - effective_min))
        color = (200, 200, 200) if MIN_ANGLE <= angle <= MAX_ANGLE else (100, 100, 255)
        cv2.line(frame, (pos_x, 118), (pos_x, 118 + BAR_HEIGHT + 4), color, 1)
        if angle in [effective_min, effective_max]:
            cv2.putText(frame, f"{angle}°", (pos_x-15, 118 + BAR_HEIGHT + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 255), 1)

    # 超限提示
    if angle1 > effective_max:
        cv2.putText(frame, f"OVER MAX! ({angle1}°)", 
                   (20 + BAR_WIDTH - 120, 118 + BAR_HEIGHT),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    elif angle1 < effective_min:
        cv2.putText(frame, f"BELOW MIN! ({angle1}°)", 
                   (20 + BAR_WIDTH - 120, 118 + BAR_HEIGHT),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # ================= 第二个角度（小角度）的进度条 =================
    effective_angle2_max = ANGLE2_MAX + ANGLE2_TOLERANCE
    clamped_angle2 = min(angle2, effective_angle2_max)
    progress2 = clamped_angle2 / effective_angle2_max
    
    # 外框和背景
    cv2.rectangle(frame, (20, 160), (20 + BAR_WIDTH, 160 + BAR_HEIGHT), (255, 255, 255), 2)
    
    # 绘制容差区域（红色渐变）
    tolerance_start = ANGLE2_MAX / effective_angle2_max
    for x in range(20, 20 + BAR_WIDTH):
        ratio = (x - 20) / BAR_WIDTH
        color = (255, 255, 255)  # 默认白色
        if ratio > tolerance_start:
            # 红色渐变：从黄色(0,255,255)过渡到红色(0,0,255)
            blend = int(255 * (ratio - tolerance_start)/(1 - tolerance_start))
            color = (0, 255-blend, 255)
        cv2.line(frame, (x, 162), (x, 160 + BAR_HEIGHT - 2), color, 1)
    
    # 实际进度
    cv2.rectangle(frame, 
                 (20, 160), 
                 (20 + int(BAR_WIDTH * progress2), 160 + BAR_HEIGHT),
                 (0, 255, 255), -1)


    # 超限提示
    if angle2 > ANGLE2_MAX:
        warn_color = (0, 255, 255) if angle2 <= effective_angle2_max else (0, 0, 255)
        warn_text = f"WARNING: {angle2}°" if angle2 <= effective_angle2_max else f"OVER MAX! ({angle2}°)"
        cv2.putText(frame, warn_text, 
                   (20 + BAR_WIDTH - 140, 160 + BAR_HEIGHT),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, warn_color, 2)

    return frame

def process_realtime_pose(model_path_data, point1, point2):
    """
    处理实时摄像头画面，提取角度数据进行分析，并保存原始视频，同时实时显示处理后的结果。
    采用多线程分离录制和处理，确保视频录制速度正常，而实时显示只使用最新帧降低延迟。
    """
    # ---------------------- 初始化 AIGym 实例 ----------------------
    gym1 = solutions.AIGym(
        model=model_path_data,
        show=False,
        line_width=1,
        up_angle=120.0,
        down_angle=80.0,
        kpts=point1,
        verbose=False
    )
    gym2 = solutions.AIGym(
        model=model_path_data,
        show=False,
        line_width=1,
        up_angle=120.0,
        down_angle=80.0,
        kpts=point2,
        verbose=False
    )

    # ---------------------- 初始化视频捕获 ----------------------
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    # ---------------------- 开始前的界面等待 ----------------------
    while True:
        ret, frame = cap.read()
        if not ret:
            print("获取摄像头画面失败")
            break
        cv2.putText(frame, "Press SPACE to Start", (100, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        cv2.putText(frame, "Press Q to Exit", (20, frame.shape[0]-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        cv2.imshow("Posture Analysis", frame)
        key = cv2.waitKey(1)
        if key == 32:  # 空格键启动
            break
        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return

    # ---------------------- 倒计时界面 ----------------------
    countdown = 0  # 倒计时3秒
    count_start = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        elapsed = time.time() - count_start
        if elapsed > countdown:
            break
        remaining = countdown - elapsed
        frame = draw_angle_info(frame, 0, 0, countdown=remaining, show_ui=True)
        cv2.imshow("Posture Analysis", frame)
        if cv2.waitKey(1) == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return

    # ---------------------- 初始化视频写入 ----------------------
    output_filename = 'output.mp4'  # 定义文件名变量
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, 30, (width, height))

    # ---------------------- 初始化队列和停止标志 ----------------------
    # 用于处理的队列只保留最新帧，降低延迟
    processing_queue = queue.Queue(maxsize=1)
    # 用于显示的队列只保留最新处理结果
    display_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    # ---------------------- 定义捕获线程 ----------------------
    def capture_thread():
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                stop_event.set()
                break
            # 写入每一帧到视频文件（保证录制原始帧完整）
            out.write(frame)
            # 将帧放入处理队列，若队列已满则先清除旧帧
            if processing_queue.full():
                try:
                    processing_queue.get_nowait()
                except queue.Empty:
                    pass
            try:
                processing_queue.put(frame, timeout=0.1)
            except queue.Full:
                pass

    # ---------------------- 定义处理线程 ----------------------
    def processing_thread():
        while not stop_event.is_set() or not processing_queue.empty():
            try:
                frame = processing_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # 调用 gym 实例处理当前帧（注意 gym2 使用帧副本）
            gym1.monitor(frame)
            gym2.monitor(frame)
            angle1 = gym1.angle[0] if isinstance(gym1.angle, (list, tuple)) else 0
            angle2 = gym2.angle[0] if isinstance(gym2.angle, (list, tuple)) else 0
            # 生成处理后的显示帧
            processed_frame = draw_angle_info(frame.copy(), angle1, angle2, show_ui=True)

            # 将处理结果放入显示队列，若队列已满则替换
            if display_queue.full():
                try:
                    display_queue.get_nowait()
                except queue.Empty:
                    pass
            try:
                display_queue.put(processed_frame, timeout=0.1)
            except queue.Full:
                pass

    # ---------------------- 启动线程 ----------------------
    t_capture = threading.Thread(target=capture_thread)
    t_processing = threading.Thread(target=processing_thread)
    t_capture.start()
    t_processing.start()

    # ---------------------- 主线程中进行显示 ----------------------
    while not stop_event.is_set():
        try:
            disp_frame = display_queue.get(timeout=0.1)
            cv2.imshow("Posture Analysis", disp_frame)
        except queue.Empty:
            pass
        key = cv2.waitKey(1)
        if key == ord('q'):
            stop_event.set()
            break

    # 等待线程退出，释放资源
    t_capture.join()
    t_processing.join()
    out.release()
    cap.release()
    cv2.destroyAllWindows()
    
    return os.path.abspath(output_filename)

# video_path = process_realtime_pose('D:\pyproject\Yolo_pro\proj1 - 副本\public\yolo11x-pose.pt', [6, 8, 10], [8, 6, 12])
# data_run_program('D:\pyproject\\4.mp4', 'D:\pyproject\Yolo_pro\data.csv', 'D:\pyproject\yolo11x-pose.pt', [6, 8, 10], [8, 6, 12])
