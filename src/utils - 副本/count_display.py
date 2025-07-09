import os
import cv2
from ultralytics import solutions
from ultralytics.utils.plotting import Annotator
import pandas as pd 
import numpy as np
import torch
from train_model import weight_features
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from collections import deque
import matplotlib
matplotlib.use('Agg')  # 设置为非交互式后端
import matplotlib.pyplot as plt
import queue
import threading

import atexit
import warnings
import json
from ultralytics import YOLO

warnings.filterwarnings('ignore')
# 获取标准平均角度
model = None
device = None
first_peak = 0
last_peak = 0
predict_data = None
standard_angles = None
standard_group1 = None
standard_group2 = None
std1 = None
model2 = None
idx = 0
tmp = 0
cur = 0
ndx = 0
prediction_text = "nothing"
predicted_label = "nothing"
label_encoder = None
t_point = None
case_arr = []
score_arr = []

def extract_segment(input_path, output_path, start_frame, end_frame, fps, size):
    """从处理后的视频中截取指定帧范围的片段"""
    cap = cv2.VideoCapture(input_path)
    # 修改输出路径扩展名为.mp4
    output_path = output_path.replace('.avi', '.mp4')
    
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
        
    out = cv2.VideoWriter(output_path, fourcc, fps, size)
    if not out.isOpened():
        # 如果H264/avc1不可用，尝试其他编码器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, size)
    
    current_frame = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if start_frame <= current_frame <= end_frame:
            out.write(frame)
        if current_frame > end_frame:
            break
        current_frame += 1
    cap.release()
    out.release()

stop_event = threading.Event()
segments_info = []  # 存储每个片段的信息

def workouts(model_path, video_path, point_list, up_angle=130.0, down_angle=70, show=False):
    Annotator.draw_specific_points = new
    cap = cv2.VideoCapture(video_path)

    assert cap.isOpened(), "Error reading video file"
    w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    # 修改输出路径扩展名为.mp4
    out_path = "./runs/" + os.path.splitext(os.path.basename(video_path))[0] + ".mp4"
    
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video_writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    if not video_writer.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

    # 初始化YOLO模型用于人物检测
    yolo_model = YOLO(model_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 59)
    # 读取第一帧进行人物检测
    success, first_frame = cap.read()
    if not success:
        print("无法读取视频第60帧")
        return
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    # 检测人物并获取ROI
    results = yolo_model.predict(first_frame, verbose=False)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()
    person_boxes = boxes[classes == 0]

    if len(person_boxes) == 0:
        print("未检测到人体")
        return

    # 找到面积最大的检测框
    areas = (person_boxes[:, 2] - person_boxes[:, 0]) * (person_boxes[:, 3] - person_boxes[:, 1])
    max_idx = np.argmax(areas)
    x1, y1, x2, y2 = person_boxes[max_idx].astype(int)
    
    # 创建ROI掩码
    roi_points = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.int32)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [roi_points], 255)

    # 将ROI信息保存为全局变量，供new函数使用
    global roi_info_global
    roi_info_global = {
        'points': roi_points.tolist(),
        'bbox': (x1, y1, x2, y2),
        'mask': mask
    }

    gym = solutions.AIGym(
        model=model_path,
        show=show,
        line_width=2,
        up_angle=up_angle,
        down_angle=down_angle,
        kpts=point_list,
        verbose=False
    )

    while cap.isOpened():
        success, im0 = cap.read()
        if not success:
            break
            
        # 创建原始帧的副本
        original_frame = im0.copy()
        
        # 应用掩码到副本
        masked_im = im0.copy()
        masked_im[mask == 0] = 0  # 将非ROI区域设为黑色
        
        # 处理帧
        processed_frame = gym.monitor(masked_im)
        
        # 将处理后的ROI区域复制回原始帧
        original_frame[mask != 0] = processed_frame[mask != 0]
        
        # 绘制ROI边界框
        cv2.rectangle(original_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # 在左上角添加文本信息
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_x = 20  # 距离左边20像素
        text_y = 40  # 距离顶部40像素
        
        # 添加半透明背景
        overlay = original_frame.copy()
        # 计算文本大小
        (text_w1, text_h1), _ = cv2.getTextSize(predicted_label, font, 1, 2)
        (text_w2, text_h2), _ = cv2.getTextSize(prediction_text, font, 1, 2)
        # 创建背景矩形
        padding = 10
        cv2.rectangle(overlay, 
                     (text_x - padding, text_y - text_h1 - padding),
                     (text_x + max(text_w1, text_w2) + padding, text_y + text_h2 + padding),
                     (0, 0, 0), -1)
        # 应用半透明效果
        cv2.addWeighted(overlay, 0.5, original_frame, 0.5, 0, original_frame)
        
        # 显示文本
        cv2.putText(original_frame, predicted_label, (text_x, text_y), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(original_frame, prediction_text, (text_x, text_y + text_h1 + 20), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
        video_writer.write(original_frame)

    cv2.destroyAllWindows()
    video_writer.release()
    
    # 修改处理后视频路径扩展名为.mp4
    processed_video_path = "./runs/" + os.path.splitext(os.path.basename(video_path))[0] + ".mp4"
    output_arr = []
    # 获取原视频文件名（不含扩展名）
    original_video_name = os.path.splitext(os.path.basename(processed_video_path))[0]
    
    for segment in segments_info:
        # 检查条件：分数低于阈值或标签不在预期列表中
        if (segment['score'] < 80):
            # 生成输出路径，使用.mp4扩展名
            output_path = f"./runs/{original_video_name}_segment_{segment['start_frame']}_{segment['end_frame']}.mp4"
        
            # 调用截取函数
            extract_segment(
                processed_video_path,
                output_path,
                segment['start_frame'],
                segment['end_frame'],
                fps, 
                (w, h)
            )
            output_arr.append(output_path)

    # 清空全局变量以备下次使用
    segments_info.clear()
    output_arr.append(processed_video_path)
    return output_arr

def new(self, keypoints, indices=None, radius=2, conf_thres=0.25):
    """
    Draw specific keypoints for gym steps counting.

    Args:
        keypoints (list): Keypoints data to be plotted.
        indices (list, optional): Keypoint indices to be plotted. Defaults to [2, 5, 7].
        radius (int, optional): Keypoint radius. Defaults to 2.
        conf_thres (float, optional): Confidence threshold for keypoints. Defaults to 0.25.

    Returns:
        (numpy.ndarray): Image with drawn keypoints.

    Note:
        Keypoint format: [x, y] or [x, y, confidence].
        Modifies self.im in-place.
    """
    # 使用全局ROI信息
    global roi_info_global
    try:
        roi_info = roi_info_global
        roi_points = roi_info['points']
        x1, y1, x2, y2 = roi_info['bbox']
        mask = roi_info['mask']
        
        # 计算ROI区域的边界框
        roi_x = x1
        roi_y = y1
        roi_w = x2 - x1
        roi_h = y2 - y1
        
        # 创建掩码后的图像
        masked_im = self.im.copy()
        masked_im[mask == 0] = 0  # 将非ROI区域设为黑色
        
        # 绘制ROI边界框
        cv2.rectangle(self.im, 
                     (roi_x, roi_y), 
                     (roi_x + roi_w, roi_y + roi_h),
                     (0, 255, 0), 2)  # 绿色边框，2像素宽度
        
        # 将掩码后的图像复制回原图
        self.im[mask != 0] = masked_im[mask != 0]
    except:
        roi_x = 50
        roi_y = 50

    indices = indices or [2, 5, 7]
    indices2 = []
    if indices == [6, 8, 10]:
        indices2 = [12, 6, 8]
    elif indices == [5, 7, 9]:
        indices2 = [11, 5, 7]

    points = [(int(keypoints[i][0]), int(keypoints[i][1])) for i in indices if keypoints[i][2] >= conf_thres]
    points2 = [(int(keypoints[i][0]), int(keypoints[i][1])) for i in indices2 if keypoints[i][2] >= conf_thres]
    global idx, tmp, cur, prediction_text, ndx, predicted_label, t_point
    # if len(points2) >= 3:
    #     t_point = points[1]
    #     if idx >= first_peak and idx <= last_peak:
    #         angle = std1['group2'][idx - first_peak - tmp]
            # dis1 = np.sqrt((points2[0][0] - points2[1][0]) ** 2 + (points2[0][1] - points2[1][1]) ** 2)
            # dis2 = np.sqrt((points2[1][0] - points2[2][0]) ** 2 + (points2[1][1] - points2[2][1]) ** 2)
            # angle_rad = np.radians(angle)
            # vector_12 = np.array([points2[0][0] - points2[1][0], points2[0][1] - points2[1][1]])
            # unit_vector = vector_12 / np.linalg.norm(vector_12)
            
            # # 判断 indices 是 [6, 8, 10] 还是 [5, 7, 9]，选择旋转方向
            # if indices == [6, 8, 10]:  # 逆时针旋转
            #     rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
            #                                 [np.sin(angle_rad), np.cos(angle_rad)]])
            # elif indices == [5, 7, 9]:  # 顺时针旋转
            #     rotation_matrix = np.array([[np.cos(angle_rad), np.sin(angle_rad)],
            #                                 [-np.sin(angle_rad), np.cos(angle_rad)]])
            
            # rotated_vector = np.dot(rotation_matrix, unit_vector)
            # point_3 = (int(points2[1][0] + rotated_vector[0] * dis2), 
            #         int(points2[1][1] + rotated_vector[1] * dis2))
            # points[1] = point_3

    if len(points) >= 0:
        if idx >= first_peak and idx <= last_peak:
            if ndx != 0:
                while predict_data['segment_label'][ndx] == predict_data['segment_label'][ndx - 1]:
                    ndx = ndx + 1
            cur = cur + 1
            group1_data = predict_data[predict_data['angle_group'] == 'group1']
            group2_data = predict_data[predict_data['angle_group'] == 'group2']
            font = cv2.FONT_HERSHEY_SIMPLEX
            print("cur:", cur)
            print("idx:", idx)
            print("ndx:", ndx)
            print("predict_data['segment_total_frames'][ndx]:", predict_data['segment_total_frames'][ndx])
            if cur == predict_data['segment_total_frames'][ndx]:

                video_name = predict_data['segment_label'][ndx]
                group1_data = group1_data[group1_data['segment_label'] == video_name]
                group2_data = group2_data[group2_data['segment_label'] == video_name]
                group1_features = group1_data['angle_value'].values
                group2_features = group2_data['angle_value'].values
                # 拼接特征
                combined_features = np.concatenate([group1_features, group2_features])
                ff = []
                ff.append(combined_features)
                ff = np.array(ff)
                ff1 = ff
                ff = weight_features(ff, num_weights=5, weight_factor=5)
                
                # 预测新数据
                features_tensor = torch.tensor(ff, dtype=torch.float32).to(device)
                with torch.no_grad():
                    prediction = model(features_tensor)
                # 输出预测结果
                predicted_score = prediction.cpu().numpy()[0]
                if predicted_score > 100:
                    predicted_score = 100
                if predicted_score < 0:
                    predicted_score = 0
                prediction_text = "score: " + str(predicted_score)
                cur = 1

                ff1_tensor = torch.tensor(ff1, dtype=torch.float32).to(device)

                if len(ff1_tensor.shape) == 1:
                    ff1_tensor = ff1_tensor.unsqueeze(0)  # 添加批次维度

                model2.eval()  
                with torch.no_grad():  
                    output = model2(ff1_tensor)
                    _, predicted = torch.max(output, 1)
                    predicted_label = label_encoder.inverse_transform([predicted.item()])[0]
                    predicted_label = "category:" + str(predicted_label)
                
                case_arr.append(predicted_label)
                score_arr.append(predicted_score)
                global segments_info
                segment_total_frames = predict_data['segment_total_frames'][ndx]
                start_frame = idx - segment_total_frames + 1  # 计算起始帧
                end_frame = idx  # 当前idx还未递增，所以结束帧是idx
                segments_info.append({
                    'start_frame': start_frame,
                    'end_frame': end_frame,
                    'score': predicted_score,
                    'label': predicted_label.split(':')[-1]  # 提取纯标签文本
                })
                ndx = ndx + 1
            # 在ROI区域内显示文本
            # 计算文本位置（在ROI右侧）
            text_x = x2 + 10  # ROI右边界右侧10像素
            text_y = y1 + 30  # ROI上边界下方30像素
            
            # 添加半透明背景以提高可读性
            overlay = self.im.copy()
            # 计算文本大小
            (text_w1, text_h1), _ = cv2.getTextSize(predicted_label, font, 1, 2)
            (text_w2, text_h2), _ = cv2.getTextSize(prediction_text, font, 1, 2)
            # 创建背景矩形
            padding = 10
            cv2.rectangle(overlay, 
                         (text_x - padding, text_y - text_h1 - padding),
                         (text_x + max(text_w1, text_w2) + padding, text_y + text_h2 + padding),
                         (0, 0, 0), -1)
            # 应用半透明效果
            cv2.addWeighted(overlay, 0.5, self.im, 0.5, 0, self.im)
            
            # 显示文本
            cv2.putText(self.im, predicted_label, (text_x, text_y), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(self.im, prediction_text, (text_x, text_y + text_h1 + 20), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
            
            # 组合文本并启动线程播报
            angle = std1['group1'][idx - first_peak]
            # dis1 = np.sqrt((points[0][0] - t_point[0]) ** 2 + (points[0][1] - t_point[1]) ** 2)
            # dis2 = np.sqrt((t_point[0] - points[2][0]) ** 2 + (t_point[1] - points[2][1]) ** 2)
            # angle_rad = np.radians(angle)
            # vector_12 = np.array([points[0][0] - points[1][0], points[0][1] - points[1][1]])
            # unit_vector = vector_12 / np.linalg.norm(vector_12)
            
            # 选择旋转方向
            # if indices == [6, 8, 10]:  # 逆时针旋转
            #     rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
            #                                 [np.sin(angle_rad), np.cos(angle_rad)]])
            # elif indices == [5, 7, 9]:  # 顺时针旋转
            #     rotation_matrix = np.array([[np.cos(angle_rad), np.sin(angle_rad)],
            #                                 [-np.sin(angle_rad), np.cos(angle_rad)]])
            
            # rotated_vector = np.dot(rotation_matrix, unit_vector)
            # point_3 = (int(points[1][0] + rotated_vector[0] * dis2), 
            #         int(points[1][1] + rotated_vector[1] * dis2))
    # if t_point != None and len(points2) >= 3:
    #     points[1] = t_point

    idx = idx + 1
    # Draw lines between consecutive points
    for start, end in zip(points[:-1], points[1:]):
        cv2.line(self.im, start, end, (0, 255, 0), 2, lineType=cv2.LINE_AA)

    # Draw circles for keypoints
    for pt in points:
        cv2.circle(self.im, pt, radius, (0, 0, 255), -1, lineType=cv2.LINE_AA)
    
    for start, end in zip(points2[:-1], points2[1:]):
        cv2.line(self.im, start, end, (0, 255, 0), 2, lineType=cv2.LINE_AA)

    # Draw circles for keypoints2
    for pt in points2:
        cv2.circle(self.im, pt, radius, (0, 0, 255), -1, lineType=cv2.LINE_AA)

    return self.im

def run_display_program(model_data, model2_data, device_data, first_peak_data, last_peak_data, model_path_data, video_path_data, point_list_data, aligned_df, std_csv, output_p, label_encoder_data):
    try:
        global model, device, first_peak, last_peak, std1, predict_data, standard_angles, standard_group1, standard_group2, model2, label_encoder
        std1 = aligned_df
        model = model_data
        device = device_data
        model2 = model2_data
        first_peak = first_peak_data
        last_peak = last_peak_data
        model_path = model_path_data
        video_path = video_path_data
        point_list = point_list_data 
        predict_data = pd.read_csv(output_p)
        standard_angles = pd.read_csv(std_csv)
        standard_group1 = standard_angles['group1'].values
        standard_group2 = standard_angles['group2'].values
        label_encoder = label_encoder_data
        output_arr = workouts(model_path, video_path, point_list)
        print(case_arr, score_arr)
        return case_arr, score_arr, output_arr
    finally:
        plt.close("all")

    