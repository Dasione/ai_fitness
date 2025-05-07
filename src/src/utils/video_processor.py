import cv2
import numpy as np
import asyncio
import websockets
import json
import base64
import sys
import os
import time
import threading
import queue
from datetime import datetime
from aiohttp import web
import subprocess

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.utils.process_data import draw_angle_info, solutions, process_realtime_pose 


class VideoProcessor:
    """视频处理器类，用于处理实时视频流和姿态分析"""
    
    def __init__(self):
        # 初始化WebSocket连接和队列
        self.connections = set()
        self.is_running = False
        self.processing_queue = queue.Queue(maxsize=1)
        self.display_queue = queue.Queue(maxsize=1)
        self.stop_event = threading.Event()
        
        # 配置模型和路径
        self.model_path = './public/yolo11x-pose.pt'
        self.video_dir = os.path.join('public', 'uploads', 'videos')
        
        # 定义关键点组
        self.left_hand_points = {
            'point1': [5, 7, 9],   # 左手肘部角度
            'point2': [7, 5, 11]   # 左手肩部角度
        }
        self.right_hand_points = {
            'point1': [6, 8, 10],  # 右手肘部角度
            'point2': [8, 6, 12]   # 右手肩部角度
        }
        
        # 初始化视频相关变量
        self.current_hand = None
        self.main_loop = None
        self.current_video_path = None
        self.cap = None
        self.out = None
        
        # 初始化模型变量
        self.gym1 = None
        self.gym2 = None
        self.gym3 = None
        self.gym4 = None
        
        # 初始化目录和模型
        self._ensure_video_dir()
        self._preload_models()

    def _ensure_video_dir(self):
        """确保视频目录存在"""
        os.makedirs(self.video_dir, exist_ok=True)
        # 设置目录权限为 755
        os.chmod(self.video_dir, 0o755)

    def _generate_video_filename(self):
        """生成带时间戳的视频文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f'training_{timestamp}.mp4'

    def _cleanup_all_videos(self):
        """清理所有临时录制的视频文件"""
        try:
            # 获取所有以'training_'开头的视频文件
            video_files = [f for f in os.listdir(self.video_dir) if f.startswith('training_') and f.endswith('.mp4')]
            
            # 删除所有符合条件的视频文件
            for file_name in video_files:
                file_path = os.path.join(self.video_dir, file_name)
                try:
                    os.remove(file_path)
                    print(f"已删除临时录制文件: {file_path}")
                except Exception as e:
                    print(f"删除文件 {file_path} 失败: {e}")
            
            print(f"已清理所有临时录制文件，共 {len(video_files)} 个文件")
        except Exception as e:
            print(f"清理临时录制文件时出错: {e}")

    def _preload_models(self):
        """预加载AI模型"""
        print("开始预加载AI模型...")
        try:
            # 预加载左手模型
            if self.gym1 is None:
                print("预加载左手模型1...")
                start_time = time.time()
                self.gym1 = solutions.AIGym(
                    model=self.model_path,
                    show=False,
                    line_width=1,
                    up_angle=140.0,
                    down_angle=60.0,
                    kpts=self.left_hand_points['point1'],
                    verbose=False,
                )
                print(f"左手模型1预加载完成，耗时: {time.time() - start_time:.2f}秒")

            if self.gym2 is None:
                print("预加载左手模型2...")
                start_time = time.time()
                self.gym2 = solutions.AIGym(
                    model=self.model_path,
                    show=False,
                    line_width=1,
                    up_angle=140.0,
                    down_angle=60.0,
                    kpts=self.left_hand_points['point2'],
                    verbose=False,
                )
                print(f"左手模型2预加载完成，耗时: {time.time() - start_time:.2f}秒")

            # 预加载右手模型
            if self.gym3 is None:
                print("预加载右手模型1...")
                start_time = time.time()
                self.gym3 = solutions.AIGym(
                    model=self.model_path,
                    show=False,
                    line_width=1,
                    up_angle=140.0,
                    down_angle=60.0,
                    kpts=self.right_hand_points['point1'],
                    verbose=False,
                )
                print(f"右手模型1预加载完成，耗时: {time.time() - start_time:.2f}秒")

            if self.gym4 is None:
                print("预加载右手模型2...")
                start_time = time.time()
                self.gym4 = solutions.AIGym(
                    model=self.model_path,
                    show=False,
                    line_width=1,
                    up_angle=140.0,
                    down_angle=60.0,
                    kpts=self.right_hand_points['point2'],
                    verbose=False,
                )
                print(f"右手模型2预加载完成，耗时: {time.time() - start_time:.2f}秒")

        except Exception as e:
            print(f"模型预加载失败: {e}")
            if hasattr(e, '__traceback__'):
                import traceback
                traceback.print_tb(e.__traceback__)

    def reset_state(self):
        """重置所有状态和资源"""
        print("重置处理器状态")
        self.is_running = False
        self.stop_event.set()
        
        # 等待队列清空
        while not self.processing_queue.empty():
            try:
                self.processing_queue.get_nowait()
            except queue.Empty:
                pass
                
        while not self.display_queue.empty():
            try:
                self.display_queue.get_nowait()
            except queue.Empty:
                pass
        
        # 清理视频捕获
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                print(f"释放视频捕获时出错: {e}")
            self.cap = None
        
        # 清理视频写入器
        if self.out is not None:
            try:
                self.out.release()
            except Exception as e:
                print(f"释放视频写入器时出错: {e}")
            self.out = None
        
        # 重置事件
        self.stop_event.clear()
        print("状态重置完成")

    async def handle_start(self, websocket, hand=None):
        """处理开始录制请求"""
        print(f"尝试启动摄像头，当前状态: {self.get_status()}")
        
        if not hand:
            print("错误：未指定要分析的手")
            return {"status": "error", "message": "未指定要分析的手"}
            
        if hand not in ['left', 'right']:
            print(f"错误：无效的手部选择 '{hand}'")
            return {"status": "error", "message": "无效的手部选择"}
            
        self.current_hand = hand
        print(f"设置当前分析的手: {hand}")
        
        # 如果已经在运行，先停止当前录制
        if self.is_running:
            print("摄像头已在运行中，先停止当前录制")
            await self.handle_stop(websocket)
            await asyncio.sleep(0.5)  # 等待资源释放
            
        # 清理所有视频文件
        self._cleanup_all_videos()
        
        # 重置状态
        self.reset_state()
        
        # 添加连接
        if websocket not in self.connections:
            self.connections.add(websocket)
            print(f"添加新连接，当前连接数: {len(self.connections)}")
        
        # 设置运行状态
        self.is_running = True
        self.stop_event.clear()
        
        # 生成新的视频文件名
        filename = self._generate_video_filename()
        self.current_video_path = os.path.join(self.video_dir, filename)
        
        print(f"开始新录制，保存至: {self.current_video_path}")
        
        try:
            # 启动处理线程
            self.start_processing()
            return {"status": "success", "message": "录制已开始"}
        except Exception as e:
            print(f"启动处理失败: {e}")
            self.reset_state()
            return {"status": "error", "message": f"启动失败: {str(e)}"}

    async def handle_stop(self, websocket):
        """处理停止录制请求"""
        print(f"尝试停止摄像头，当前状态: {self.get_status()}")
        
        if not self.is_running:
            print("摄像头未在运行中")
            return {"status": "warning", "message": "摄像头未在运行中"}
            
        # 停止录制
        self.stop_event.set()
        self.is_running = False
        
        # 等待资源释放
        await asyncio.sleep(1.0)  # 增加等待时间，确保视频文件完全写入
        
        # 重置状态
        self.reset_state()
        
        if self.current_video_path and os.path.exists(self.current_video_path):
            # 检查文件大小
            file_size = os.path.getsize(self.current_video_path)
            if file_size == 0:
                print("视频文件大小为0，删除无效文件")
                os.remove(self.current_video_path)
                return {"status": "error", "message": "视频文件无效"}
            
            # 简化URL生成逻辑，直接使用相对路径
            filename = os.path.basename(self.current_video_path)
            url = f"/uploads/videos/{filename}"
            
            response = {
                "type": "video_ready",
                "data": {
                    "url": url,
                    "filename": filename
                }
            }
            
            if websocket in self.connections:
                await websocket.send(json.dumps(response))
                self.connections.remove(websocket)
            
            print(f"视频文件已生成: {filename}, 大小: {file_size} 字节")
            return {"status": "success", "message": "录制已停止", "video_path": self.current_video_path}
        else:
            print("未找到生成的视频文件")
            return {"status": "error", "message": "未找到生成的视频文件"}

    def get_status(self):
        """获取当前状态"""
        return {
            'is_running': self.is_running,
            'connections': len(self.connections),
            'current_video_path': self.current_video_path
        }

    async def handle_client(self, websocket):
        """处理WebSocket客户端连接"""
        print("新的WebSocket连接已建立")
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print("收到WebSocket消息:", {
                        **data,
                        'connections': len(self.connections),
                        'is_running': self.is_running,
                        'has_cap': self.cap is not None,
                        'has_out': self.out is not None
                    })
                    
                    if data['type'] == 'start':
                        await self.handle_start(websocket, data['hand'])
                    elif data['type'] == 'stop':
                        await self.handle_stop(websocket)
                    
                except json.JSONDecodeError:
                    print("无效的JSON消息")
                    continue
                except Exception as e:
                    print(f"处理消息时出错: {e}")
                    if websocket in self.connections:
                        try:
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': str(e)
                            }))
                        except:
                            pass
                    
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket连接已关闭")
        finally:
            if websocket in self.connections:
                self.connections.remove(websocket)
                print(f"移除连接，当前连接数: {len(self.connections)}")
            if len(self.connections) == 0:
                print("没有活动的WebSocket连接，停止摄像头")
                self.reset_state()

    def start_processing(self):
        """启动视频处理"""
        if self.is_running:
            print("开始视频处理")
            # 启动视频捕获线程
            capture_thread = threading.Thread(target=self.process_video)
            capture_thread.start()
            print("视频捕获线程已启动")
            
            # 启动帧处理线程
            processing_thread = threading.Thread(target=self.process_frame)
            processing_thread.start()
            print("帧处理线程已启动")
            
            # 启动显示线程
            display_thread = threading.Thread(target=self.display_video)
            display_thread.start()
            print("显示线程已启动")

    def process_video(self):
        """处理视频帧的线程函数"""
        try:
            print("开始初始化视频处理资源")
            # 初始化摄像头
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("无法打开摄像头")

            # 获取视频参数
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 确保视频目录存在
            os.makedirs(self.video_dir, exist_ok=True)
            
            # 尝试不同的编码器
            codecs = ['avc1', 'mp4v', 'XVID', 'MJPG']
            self.out = None
            
            for codec in codecs:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    self.out = cv2.VideoWriter(self.current_video_path, fourcc, 30, (width, height))
                    if self.out.isOpened():
                        print(f"使用编码器: {codec}")
                        break
                    else:
                        self.out.release()
                        self.out = None
                except Exception as e:
                    print(f"编码器 {codec} 初始化失败: {e}")
                    if self.out:
                        self.out.release()
                        self.out = None
            
            if not self.out:
                raise Exception("无法初始化任何视频编码器")

            print("检查AI模型状态")
            if self.gym1 is None or self.gym2 is None or self.gym3 is None or self.gym4 is None:
                print("重新加载AI模型")
                self._preload_models()
            
            if self.gym1 is None or self.gym2 is None or self.gym3 is None or self.gym4 is None:
                raise Exception("AI模型未正确加载")

            print("所有资源初始化完成，开始处理视频")
            
            # 倒计时界面
            countdown = 3  # 倒计时3秒
            count_start = time.time()
            while not self.stop_event.is_set():
                ret, frame = self.cap.read()
                if not ret:
                    print("读取视频帧失败")
                    break

                # 倒计时显示
                elapsed = time.time() - count_start
                if elapsed < countdown:
                    remaining = countdown - elapsed
                    frame = draw_angle_info(frame, 0, 0, countdown=remaining, show_ui=True)
                else:
                    # 写入原始帧到视频文件
                    self.out.write(frame)
                    # 将原始帧放入处理队列，若队列已满则先清除旧帧
                    if self.processing_queue.full():
                        try:
                            self.processing_queue.get_nowait()
                        except queue.Empty:
                            pass
                    try:
                        self.processing_queue.put(frame.copy(), timeout=0.1)
                    except queue.Full:
                        pass

        except Exception as e:
            print(f"视频处理线程出错: {e}")
        finally:
            print("开始清理视频处理资源")
            # 清理视频资源
            if self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                    print("视频捕获已释放")
                except Exception as e:
                    print(f"释放视频捕获时出错: {e}")
            
            if self.out:
                try:
                    self.out.release()
                    self.out = None
                    print("视频写入器已释放")
                except Exception as e:
                    print(f"释放视频写入器时出错: {e}")
            
            # 设置视频文件权限
            if os.path.exists(self.current_video_path):
                try:
                    os.chmod(self.current_video_path, 0o644)
                    print(f"视频文件已保存并设置权限: {self.current_video_path}")
                except Exception as e:
                    print(f"设置视频文件权限时出错: {e}")
            
            print("所有资源清理完成")

    def process_frame(self):
        """处理帧的线程函数"""
        while not self.stop_event.is_set() or not self.processing_queue.empty():
            try:
                frame = self.processing_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                if not self.current_hand:
                    print("错误：未设置当前分析的手")
                    continue

                # 根据选择的手调用对应的模型
                if self.current_hand == 'left':
                    self.gym1.monitor(frame)
                    self.gym2.monitor(frame.copy())
                    angle1 = self.gym1.angle[0] if isinstance(self.gym1.angle, (list, tuple)) else 0
                    angle2 = self.gym2.angle[0] if isinstance(self.gym2.angle, (list, tuple)) else 0
                else:  # right
                    self.gym3.monitor(frame)
                    self.gym4.monitor(frame.copy())
                    angle1 = self.gym3.angle[0] if isinstance(self.gym3.angle, (list, tuple)) else 0
                    angle2 = self.gym4.angle[0] if isinstance(self.gym4.angle, (list, tuple)) else 0
                
                # 生成处理后的显示帧
                processed_frame = draw_angle_info(frame.copy(), angle1, angle2, show_ui=True)

                # 将处理结果放入显示队列，若队列已满则替换
                if self.display_queue.full():
                    try:
                        self.display_queue.get_nowait()
                    except queue.Empty:
                        pass
                try:
                    self.display_queue.put(processed_frame, timeout=0.1)
                except queue.Full:
                    pass
            except Exception as e:
                print(f"帧处理失败: {e}")
                if hasattr(e, '__traceback__'):
                    import traceback
                    traceback.print_tb(e.__traceback__)
                continue

    def display_video(self):
        """显示处理后的帧并发送给客户端的线程函数"""
        while not self.stop_event.is_set() or not self.display_queue.empty():
            try:
                frame = self.display_queue.get(timeout=0.1)
                
                # 将帧转换为base64
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # 创建消息
                message = json.dumps({
                    'type': 'frame',
                    'data': frame_base64
                })
                
                # 发送给所有连接的客户端
                for websocket in self.connections.copy():
                    try:
                        # 使用主事件循环发送消息
                        future = asyncio.run_coroutine_threadsafe(
                            self._send_frame(websocket, message),
                            self.main_loop
                        )
                        future.result(timeout=1.0)  # 等待发送完成，最多等待1秒
                    except websockets.exceptions.ConnectionClosed:
                        if websocket in self.connections:
                            self.connections.remove(websocket)
                    except Exception as e:
                        print(f"发送帧时出错: {e}")
                        if websocket in self.connections:
                            self.connections.remove(websocket)
                        
            except queue.Empty:
                continue

    async def _send_frame(self, websocket, message):
        """异步发送帧给客户端"""
        await websocket.send(message)

async def analyze_video(request):
    """处理视频分析请求"""
    try:
        data = await request.json()
        video_path = data.get('video_path')
        hand = data.get('hand')
        
        if not video_path or not hand:
            return web.json_response({
                'error': '缺少必要参数'
            }, status=400)
            
        # 调用 process_video.py 进行分析
        process = await asyncio.create_subprocess_exec(
            'python', 'src/utils/process_video.py', video_path, hand,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return web.json_response({
                'error': f'分析失败: {stderr.decode()}'
            }, status=500)
            
        # 解析输出结果
        output = stdout.decode()
        import re
        json_match = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', output)
        if not json_match:
            return web.json_response({
                'error': '未找到有效的分析结果'
            }, status=500)
            
        result = json.loads(json_match[-1])
        
        # 计算平均分数
        flat_scores = [score for sublist in result['score_arr'] for score in sublist]
        result['average_score'] = sum(flat_scores) / len(flat_scores)
        
        # 生成运动建议
        llm_process = await asyncio.create_subprocess_exec(
            'python', 'src/utils/llm_response.py',
            '--scores', json.dumps(result['score_arr']),
            '--cases', json.dumps(result['case_arr']),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        llm_stdout, llm_stderr = await llm_process.communicate()
        
        if llm_process.returncode == 0:
            result['suggestions'] = llm_stdout.decode().strip()
        else:
            result['suggestions'] = ''
            
        return web.json_response(result)
        
    except Exception as e:
        return web.json_response({
            'error': f'处理请求失败: {str(e)}'
        }, status=500)

async def main():
    processor = VideoProcessor()
    # 保存主事件循环的引用
    processor.main_loop = asyncio.get_event_loop()
    
    # 创建 Web 应用
    app = web.Application()
    app.router.add_post('/analyze', analyze_video)
    
    # 启动 WebSocket 服务器
    ws_server = await websockets.serve(processor.handle_client, "0.0.0.0", 8765)
    print("WebSocket服务器启动在 ws://0.0.0.0:8765")
    
    # 启动 HTTP 服务器
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8766)  # 使用不同的端口
    await site.start()
    print("HTTP服务器启动在 http://0.0.0.0:8766")
    
    # 等待服务器运行
    await asyncio.Future()  # 运行直到被终止

if __name__ == "__main__":
    asyncio.run(main()) 