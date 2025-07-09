import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
from torch.optim.lr_scheduler import OneCycleLR
from sklearn.metrics import mean_squared_error, r2_score
import warnings

warnings.filterwarnings('ignore')
def load_and_preprocess_data(file_path):
    data = pd.read_csv(file_path)

    # 筛选出case0的数据
    case0_data = data[data['categories'] == 'case0']

    # 按照视频名称、角度组和帧数进行分组
    grouped = case0_data[['video_name', 'angle_group', 'frame_number', 'angle_value']]

    # 计算每个组每帧的平均角度
    final_result = grouped.groupby(['angle_group', 'frame_number'])['angle_value'].mean().reset_index()

    # 获取标准平均角度
    standard_angles = final_result.pivot(index='frame_number', columns='angle_group', values='angle_value').reset_index()

    # 展示标准平均角度
    return data, standard_angles

# 加权欧氏距离计算函数
def weighted_euclidean_distance(video_group, standard_group, num_weights=5, weight_factor=5, is_group2=False):
    """
    计算加权欧氏距离，对于group2只给中间的帧赋予权重，其他组仍然给前后赋予权重。
    
    :param video_group: 视频的角度数据（按帧排序）
    :param standard_group: 标准的角度数据（按帧排序）
    :param weight_factor: 给指定帧分配的较大权重
    :param num_weights: 需要加权的帧数
    :param is_group2: 是否为group2数据，控制是否只加权中间帧
    :return: 加权欧氏距离
    """
    n = len(video_group)
    
    # 初始化权重向量
    weights = np.ones(n)
    
    if not is_group2:
        # 对于其他组（如group1），加权前后num_weights帧
        weights[:num_weights] = weight_factor  # 前num_weights帧
        weights[-num_weights:] = weight_factor  # 后num_weights帧
    else:
        # 对于group2，只加权中间的num_weights帧
        middle_start = (n - num_weights) // 2
        middle_end = middle_start + num_weights
        weights[middle_start:middle_end] = weight_factor  # 中间num_weights帧加权
    
    # 计算加权欧氏距离
    weighted_diff = (video_group - standard_group) * weights
    distance = np.sqrt(np.sum(weighted_diff ** 2))
    
    return distance

# 计算视频的距离评分
def calculate_video_distances(data, standard_angles):
    #存储评分
    distance_scores = {}

    videos = data.groupby('video_name')

    for video_name, video_data in videos:
        video_grouped = video_data[['angle_group', 'frame_number', 'angle_value']]

        video_group1 = video_grouped[video_grouped['angle_group'] == 'group1'].sort_values(by='frame_number')['angle_value'].values
        video_group2 = video_grouped[video_grouped['angle_group'] == 'group2'].sort_values(by='frame_number')['angle_value'].values
        
        standard_group1 = standard_angles['group1'].values
        standard_group2 = standard_angles['group2'].values
        
        distance_group1 = weighted_euclidean_distance(video_group1, standard_group1, num_weights=3, weight_factor=3)
        distance_group2 = weighted_euclidean_distance(video_group2, standard_group2, num_weights=3, weight_factor=3, is_group2=True)
        
        final_distance = (distance_group1 + distance_group2) / 2
        distance_scores[video_name] = final_distance

    return distance_scores

def normalize_scores(distance_scores):
    min_distance = min(distance_scores.values())
    max_distance = max(distance_scores.values())

    # 将距离反向归一化到 [0, 100] 之间
    normalized_scores = {video_name: 100 - ((score - min_distance) / (max_distance - min_distance)) * 100
                         for video_name, score in distance_scores.items()}
    return normalized_scores

# 生成视频特征并计算标签
def generate_features_and_labels(data, normalized_scores):
    features = []
    labels = []

    for video_name, group in data.groupby('video_name'):
        group1_data = group[group['angle_group'] == 'group1']['angle_value'].values
        group2_data = group[group['angle_group'] == 'group2']['angle_value'].values

        if len(group1_data) == len(group2_data):
            combined_features = np.concatenate([group1_data, group2_data])  # 特征：角度数据
            features.append(combined_features)
            labels.append(normalized_scores[video_name])  # 标签：计算的距离分数

    return np.array(features), np.array(labels)

# 为每个视频的前62帧和后62帧增加权重，两组角度
def weight_features(features, num_weights=5, weight_factor=5):
    """
    给每个视频的前62帧和后62帧的特定部分赋予较大的权重。
    
    :param features: 输入的特征数组 (num_samples, feature_size)
    :param num_weights: 需要增加权重的帧数
    :param weight_factor: 头尾帧的权重因子
    :return: 加权后的特征
    """
    weighted_features = features.copy()

    # 遍历每个视频样本
    for i in range(weighted_features.shape[0]):
        # 前62帧的首部和尾部加权
        weighted_features[i, :num_weights] *= weight_factor  # 前num_weights帧
        weighted_features[i, 62 - num_weights:62] *= weight_factor  # 前62帧的尾部

        # 后62帧的中间五帧加权
        start_mid = 62 + (62 - num_weights)  # 后62帧的中间部分起始位置
        end_mid = 62 + (62 + num_weights)  # 后62帧的中间部分结束位置
        weighted_features[i, start_mid:end_mid] *= weight_factor  # 后62帧的中间部分

    return weighted_features

# 定义卷积神经网络模型
class CNNRegressor(nn.Module):
    def __init__(self, input_size):
        super(CNNRegressor, self).__init__()
        # 增加网络深度和特征
        self.conv1 = nn.Conv1d(1, 64, 3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        self.conv2 = nn.Conv1d(64, 128, 3, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        self.conv3 = nn.Conv1d(128, 256, 3, padding=1)  # 新增
        self.bn3 = nn.BatchNorm1d(256)
        
        self.pool = nn.MaxPool1d(2)
        self.dropout = nn.Dropout(p=0.2)  # 增加dropout率
        
        conv_output_size = input_size // 8  # 因为有3次池化
        self.fc1 = nn.Linear(256 * conv_output_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)

    def forward(self, x):
        x = x.unsqueeze(1)
        x = self.pool(torch.relu(self.bn1(self.conv1(x))))
        x = self.pool(torch.relu(self.bn2(self.conv2(x))))
        x = self.pool(torch.relu(self.bn3(self.conv3(x))))
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    
"""添加数据增强"""
def augment_features(features):
    augmented = features.copy()
    # 添加随机噪声
    noise = np.random.normal(0, 0.01, features.shape)
    augmented += noise
    # 随机时间偏移
    shift = np.random.randint(-2, 3)
    if shift > 0:
        augmented = np.roll(augmented, shift, axis=1)
    return augmented

# 训练模型
def train_model(model, train_loader, optimizer, loss_fn, device, scheduler, input_size, epochs = 500, num_trials=20):
    best_loss = float('inf')
    best_model_state = None
    
    for trial in range(num_trials):
        print(f"开始第 {trial + 1} 次训练...")
        model.load_state_dict(model.state_dict())  # 重置模型参数
        model.train()
        epoch_losses = []
        patience = 10
        patience_counter = 0
        trial_best_loss = float('inf')
        
        for epoch in range(epochs):
            epoch_loss = 0
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)

                optimizer.zero_grad()

                # 前向传播
                outputs = model(X_batch)

                # 计算损失
                loss = loss_fn(outputs.squeeze(), y_batch)  # squeeze()去掉维度1

                # 反向传播
                loss.backward()

                # 更新参数
                optimizer.step()

                epoch_loss += loss.item()
            scheduler.step()
            epoch_losses.append(epoch_loss / len(train_loader))
            
            # 早停检查
            if epoch_loss < trial_best_loss:
                trial_best_loss = epoch_loss
                patience_counter = 0
                trial_best_model_state = model.state_dict()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    break
        
        # 如果这次训练的损失比之前的最好结果更好，更新最佳模型
        if trial_best_loss < best_loss:
            best_loss = trial_best_loss
            best_model_state = trial_best_model_state
            torch.save({
                'model_state_dict': best_model_state,
                'input_size':input_size,
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'best_loss': best_loss
            }, 'best_regress_model.pth')
            print(f"第 {trial + 1} 次训练获得更好的模型，损失: {best_loss:.4f}")
    
    # 加载最佳模型状态
    model.load_state_dict(best_model_state)
    return model

# 测试模型
def test_model(model, test_loader, device):
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            outputs = model(X_batch)
            outputs = outputs.squeeze()
            if outputs.dim() == 0:
                outputs = outputs.unsqueeze(0)
            outputs = torch.clamp(outputs, min=0, max=100)
            outputs_np = outputs.cpu().numpy()
            if outputs_np.ndim == 0:
                outputs_np = np.array([outputs_np])
            all_preds.append(outputs_np)
            all_labels.append(y_batch.cpu().numpy())

    all_preds = np.concatenate(all_preds)
    all_labels = np.concatenate(all_labels)
    
    mse = mean_squared_error(all_labels, all_preds)
    r2 = r2_score(all_labels, all_preds)
    
    print(f"\nTest Mean Squared Error: {mse:.4f}")
    print(f"Test R^2 Score: {r2:.4f}")

def load_model(model_path='best_regress_model.pth'):
    """加载保存的回归模型"""
    try:
        print(f"尝试加载模型文件: {model_path}")
        checkpoint = torch.load(model_path)
        print("模型文件加载成功")
        print(f"模型参数: input_size={checkpoint['input_size']}")
        
        # 创建模型时确保使用正确的输入大小
        model = CNNRegressor(checkpoint['input_size'])
        
        # 检查模型结构是否匹配
        saved_state_dict = checkpoint['model_state_dict']
        current_state_dict = model.state_dict()
        
        # 尝试加载模型参数
        try:
            model.load_state_dict(saved_state_dict)
            print("模型参数加载成功")
        except Exception as e:
            print(f"模型参数加载失败: {str(e)}")
            print("将重新训练模型...")
            raise
        
        return model
    except Exception as e:
        print(f"加载模型时出错: {str(e)}")
        raise

def run(file_path_data, load_saved_model=False):
    if load_saved_model:
        try:
            model = load_model()
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = model.to(device)
            return model, device
        except:
            print("无法加载保存的模型，将重新训练...")
            load_saved_model = False  # 确保重新训练
    
    # 加载并预处理数据
    file_path = file_path_data
    data, standard_angles = load_and_preprocess_data(file_path)

    # 计算视频距离
    distance_scores = calculate_video_distances(data, standard_angles)

    # 归一化分数
    normalized_scores = normalize_scores(distance_scores)

    # 生成特征和标签
    features, labels = generate_features_and_labels(data, normalized_scores)

    # 加权特征
    features = weight_features(features, num_weights=5, weight_factor=5)
    features = augment_features(features)
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.4, random_state=42)

    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test, dtype=torch.float32)

    # 创建DataLoader
    train_data = TensorDataset(X_train_tensor, y_train_tensor)
    test_data = TensorDataset(X_test_tensor, y_test_tensor)

    train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=64, shuffle=False)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    input_size = X_train.shape[1]
    model = CNNRegressor(input_size)

    model = model.to(device)

    # 定义损失函数和优化器
    loss_fn = nn.SmoothL1Loss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = OneCycleLR(optimizer, 
                                 max_lr=0.01,
                                 epochs=500,
                                 steps_per_epoch=len(train_loader))

    # 初始化模型
    model.to(device)

    # 训练模型
    model = train_model(model, train_loader, optimizer, loss_fn, device, scheduler, input_size, epochs=500, num_trials=20)

    # 测试模型
    test_model(model, test_loader, device)
    return model, device

# run("D:\Learning\Codes\\vue_code\proj1\public\data.csv", load_saved_model=True)