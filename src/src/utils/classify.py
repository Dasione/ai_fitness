import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import f1_score
import warnings

warnings.filterwarnings('ignore')
def load_and_preprocess_data(file_path):
    # 加载数据
    data = pd.read_csv(file_path)
    
    # 按照视频名称分组
    grouped = data.groupby('video_name')
    
    features = []
    labels = []

    # 遍历每个视频，将group1和group2的数据合并，提取类别作为标签
    for video_name, group in grouped:
        group1_data = group[group['angle_group'] == 'group1']['angle_value'].values
        group2_data = group[group['angle_group'] == 'group2']['angle_value'].values
        categories = group['categories'].iloc[0]  # 每个视频的类别标签
        # 确保group1和group2的长度相同
        if len(group1_data) == len(group2_data):
            # 将group1和group2合并
            combined_features = np.concatenate([group1_data, group2_data])
            features.append(combined_features)
            labels.append(categories)

    # 转换为NumPy数组
    features = np.array(features)
    labels = np.array(labels)
    # 类别标签编码
    label_encoder = LabelEncoder()
    labels_encoded = label_encoder.fit_transform(labels)

    return features, labels_encoded, label_encoder

def create_dataloaders(features, labels_encoded, test_size=0.4, batch_size=64):
    # 数据集划分
    X_train, X_test, y_train, y_test = train_test_split(features, labels_encoded, test_size=test_size, random_state=42)

    # 转换为PyTorch张量
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.long)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test, dtype=torch.long)

    # 创建DataLoader
    train_data = TensorDataset(X_train_tensor, y_train_tensor)
    test_data = TensorDataset(X_test_tensor, y_test_tensor)

    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader

class ImprovedNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(ImprovedNN, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.BatchNorm1d(hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size // 2, output_size)
        )

    def forward(self, x):
        return self.layers(x)
    
def augment_data(features):
    """数据增强函数"""
    augmented_features = features.copy()
    
    # 添加随机噪声
    noise = np.random.normal(0, 0.01, features.shape)
    augmented_features += noise
    
    # 随机时间偏移
    shift = np.random.randint(-2, 3)
    augmented_features = np.roll(augmented_features, shift, axis=1)
    
    return augmented_features

def train_model(model, train_loader, optimizer, loss_fn, device, scheduler, label_encoder, epochs=100, num_trials=5):
    best_accuracy = 0
    best_model_state = None
    patience = 10
    patience_counter = 0
    
    for trial in range(num_trials):
        print(f"开始第 {trial + 1} 次训练...")
        model.load_state_dict(model.state_dict())  # 重置模型参数
        patience_counter = 0
        trial_best_accuracy = 0
        
        for epoch in range(epochs):
            model.train()
            epoch_loss = 0
            correct_preds = 0
            total_preds = 0
            
            for X_batch, y_batch in train_loader:
                # 数据增强
                X_batch = torch.tensor(augment_data(X_batch.numpy()), dtype=torch.float32)
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                
                optimizer.zero_grad()
                outputs = model(X_batch)
                loss = loss_fn(outputs, y_batch)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                correct_preds += (predicted == y_batch).sum().item()
                total_preds += y_batch.size(0)
            
            accuracy = correct_preds / total_preds * 100
            
            # 更新学习率
            scheduler.step(accuracy)
            
            # 早停检查
            if accuracy > trial_best_accuracy:
                trial_best_accuracy = accuracy
                patience_counter = 0
                trial_best_model_state = model.state_dict()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    break
        
        # 如果这次训练的准确率比之前的最好结果更好，更新最佳模型
        if trial_best_accuracy > best_accuracy:
            best_accuracy = trial_best_accuracy
            best_model_state = trial_best_model_state
            input_size = model.layers[0].in_features
            hidden_size = model.layers[0].out_features
            output_size = model.layers[-1].out_features
            # 保存最佳模型
            torch.save({
                'model_state_dict': best_model_state,
                'label_encoder': label_encoder,
                'input_size': input_size,
                'hidden_size': hidden_size,
                'output_size': output_size,
                'best_accuracy': best_accuracy
            }, 'best_classify_model.pth')
            print(f"第 {trial + 1} 次训练获得更好的模型，准确率: {best_accuracy:.2f}%")
    
    # 加载最佳模型状态
    model.load_state_dict(best_model_state)
    return model

def load_model(model_path='best_classify_model.pth'):
    """加载保存的分类模型"""
    try:
        print(f"尝试加载模型文件: {model_path}")
        checkpoint = torch.load(model_path)
        print("模型文件加载成功")
        print(f"模型参数: input_size={checkpoint['input_size']}, hidden_size={checkpoint['hidden_size']}, output_size={checkpoint['output_size']}")
        model = ImprovedNN(checkpoint['input_size'], checkpoint['hidden_size'], checkpoint['output_size'])
        model.load_state_dict(checkpoint['model_state_dict'])
        print("模型参数加载成功")
        return model, checkpoint['label_encoder']
    except Exception as e:
        print(f"加载模型时出错: {str(e)}")
        raise

def test_model(model, test_loader, device):
    model.eval()
    correct_preds = 0
    total_preds = 0
    y_true = []
    y_pred_all = []
    
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            outputs = model(X_batch)
            _, predicted = torch.max(outputs, 1)
            
            correct_preds += (predicted == y_batch).sum().item()
            total_preds += y_batch.size(0)
            
            # 收集真实标签和预测标签（转换到 CPU 上）
            y_true.extend(y_batch.cpu().numpy())
            y_pred_all.extend(predicted.cpu().numpy())

    accuracy = correct_preds / total_preds * 100
    f1 = f1_score(y_true, y_pred_all, average='weighted')
    print(f"Test Accuracy: {accuracy:.2f}%")
    print(f"F1 Score: {f1:.2f}")

def run_classify(file_path_data, load_saved_model=False):
    if load_saved_model:
        try:
            model, label_encoder = load_model()
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = model.to(device)
            return model, label_encoder
        except:
            print("无法加载保存的模型，将重新训练...")
    
    # 加载数据并预处理
    features, labels_encoded, label_encoder = load_and_preprocess_data(file_path_data)
    features = augment_data(features)
    # 创建数据加载器
    train_loader, test_loader = create_dataloaders(features, labels_encoded)

    # 利用GPU加速
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # print(f"Using device: {device}")

    # 定义模型
    input_size = features.shape[1]  # 输入特征的维度
    hidden_size = 64  # 隐藏层大小
    output_size = len(label_encoder.classes_)  # 类别数目
    model = ImprovedNN(input_size, hidden_size, output_size)
    model = model.to(device)

    # 定义损失函数和优化器
    loss_fn = nn.CrossEntropyLoss()  # 用于分类任务的交叉熵损失
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=5, verbose=False
    )
    
    # 训练模型
    model = train_model(model, train_loader, optimizer, loss_fn, device, scheduler, label_encoder, epochs=50, num_trials=5)
    
    # 测试模型
    test_model(model, test_loader, device)

    
    return model, label_encoder


# run_classify("D:\\pyproject\\Yolo_pro\\data.csv",load_saved_model = True)