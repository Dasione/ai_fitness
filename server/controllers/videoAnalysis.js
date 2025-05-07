import { VideoAnalysis, Video } from '../models/index.js';
import path from 'path';
import { fileURLToPath } from 'url';
import { join } from 'path';
import fs from 'fs';
import axios from 'axios';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const startAnalysis = async (req, res) => {
    try {
        const { videoId, hand, reAnalyze } = req.body;

        // 检查视频是否存在
        const video = await Video.findByPk(videoId);
        if (!video) {
            return res.status(404).json({ message: '视频不存在' });
        }

        // 如果是重新分析，则删除已存在的记录
        if (reAnalyze) {
            // 删除已存在的分析记录
            await VideoAnalysis.destroy({
                where: {
                    video_id: videoId,
                    hand_choice: hand
                }
            });

            // 删除相关的分析视频文件
            try {
                const baseFileName = videoId;
                const runsDir = path.join(process.cwd(), 'runs');
                const files = fs.readdirSync(runsDir);
                
                // 删除所有相关的分析视频片段
                for (const file of files) {
                    if (file.startsWith(baseFileName)) {
                        const filePath = path.join(runsDir, file);
                        fs.unlinkSync(filePath);
                        console.log('删除分析视频片段:', filePath);
                    }
                }
            } catch (error) {
                console.error('删除分析视频文件失败:', error);
                // 继续执行，不中断删除流程
            }
        } else {
            // 如果是首次分析，检查是否已有相同手臂的分析结果
            const existingAnalysis = await VideoAnalysis.findOne({
                where: {
                    video_id: videoId,
                    hand_choice: hand
                }
            });

            if (existingAnalysis && existingAnalysis.status === 'completed') {
                return res.json({
                    message: '分析结果已存在',
                    analysis: existingAnalysis
                });
            }
        }

        // 创建新的分析记录
        const analysis = await VideoAnalysis.create({
            video_id: videoId,
            hand_choice: hand,
            status: 'processing'
        });

        // 更新视频状态为 processing
        await video.update({ status: 'processing' });

        console.log('视频状态更新:', {
            videoId: video.id,
            oldStatus: video.status,
            newStatus: 'processing',
            reason: '开始分析'
        });

        // 构建完整的视频路径
        const videoPath = join(process.cwd(), video.file_path);
        
        // 通过 HTTP 请求调用 processor 服务进行分析
        try {
            const processorUrl = process.env.PROCESSOR_URL || 'http://localhost:8766';
            const processorResponse = await axios.post(`${processorUrl}/analyze`, {
                video_path: videoPath,
                hand: hand
            }, {
                timeout: 300000 // 设置超时时间为 5 分钟
            });

            const { case_arr, score_arr, output_arr, average_score, suggestions } = processorResponse.data;

            // 更新分析记录
            await analysis.update({
                case_arr,
                score_arr,
                output_arr,
                average_score,
                suggestions,
                status: 'completed'
            });

            // 更新视频状态为 processed
            await video.update({ status: 'processed' });

            return res.json({
                message: '分析完成',
                analysis
            });
        } catch (error) {
            console.error('调用 processor 服务失败:', error);
            
            // 更新错误状态
            await Promise.all([
                video.update({ status: 'error' }),
                analysis.update({ 
                    status: 'error',
                    error_message: `分析失败: ${error.message}`
                })
            ]);

            return res.status(500).json({
                message: '分析失败',
                error: error.message
            });
        }
    } catch (error) {
        console.error('视频分析失败:', error);
        return res.status(500).json({
            message: '视频分析失败',
            error: error.message
        });
    }
};

export const getAnalysisResult = async (req, res) => {
    try {
        const videoId = req.params.id;
        const { hand } = req.query;

        const analysis = await VideoAnalysis.findOne({
            where: {
                video_id: videoId,
                hand_choice: hand
            }
        });

        if (!analysis) {
            return res.status(404).json({ message: '分析结果不存在' });
        }
        res.json(analysis);
    } catch (error) {
        console.error('获取分析结果时出错:', error);
        res.status(500).json({ 
            message: '服务器错误',
            error: error.message 
        });
    }
};

export const deleteAnalysis = async (req, res) => {
    try {
        const videoId = req.params.id;
        const { hand } = req.query;

        if (!hand) {
            return res.status(400).json({ message: '缺少手部参数' });
        }

        // 删除分析记录
        const result = await VideoAnalysis.destroy({
            where: {
                video_id: videoId,
                hand_choice: hand
            }
        });

        // 删除相关的分析视频文件
        try {
            const baseFileName = videoId;
            const runsDir = path.join(process.cwd(), 'runs');
            const files = fs.readdirSync(runsDir);
            
            // 删除所有相关的分析视频片段
            for (const file of files) {
                if (file.startsWith(baseFileName)) {
                    const filePath = path.join(runsDir, file);
                    fs.unlinkSync(filePath);
                    console.log('删除分析视频片段:', filePath);
                }
            }
        } catch (error) {
            console.error('删除分析视频文件失败:', error);
            // 继续执行，不中断删除流程
        }

        if (result > 0) {
            res.json({ message: '分析记录已删除' });
        } else {
            res.status(404).json({ message: '分析记录不存在' });
        }
    } catch (error) {
        console.error('删除分析记录失败:', error);
        res.status(500).json({ 
            message: '服务器错误',
            error: error.message 
        });
    }
}; 