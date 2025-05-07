import { defineStore } from 'pinia'
import api from '@/utils/api'

export const useVideoStore = defineStore('video', {
  state: () => ({
    videos: [],
    currentVideo: null,
    loading: false,
    error: null,
    analyzing: false,
    dashboardStats: {
      totalVideos: 0,
      totalDuration: 0,
      totalAnalysis: 0,
      scoreDistribution: {
        excellent: 0,
        good: 0,
        fair: 0,
        poor: 0
      },
      scoreTrend: [],
      uploadTrend: [],
      recentAnalysis: []
    },
    totalVideos: 0
  }),

  getters: {
    getAllVideos: (state) => state.videos, 
    getCurrentVideo: (state) => state.currentVideo,
    getVideos: (state) => state.videos,
    getDashboardStats: (state) => state.dashboardStats
  },

  actions: {
    async fetchVideos(params = { page: 1, pageSize: 10 }) {
      this.loading = true;
      try {
        console.debug('开始获取视频列表...', params);
        console.debug('当前 token:', localStorage.getItem('token'));
        
        const queryParams = {
          page: params.page,
          limit: params.pageSize
        };
        
        const response = await api.get('/videos', { params: queryParams });
        console.info('视频列表响应数据:', {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
          data: response.data
        });
        
        if (response.data) {
          console.debug('处理视频数据:', response.data);
          this.videos = response.data.videos.map(video => {
            const processedVideo = {
              ...video,
              id: video.id,
              title: video.title || '未命名视频',
              url: `/uploads/videos/${video.file_path.split('\\').pop()}`,
              thumbnail: video.thumbnail_path ? `/${video.thumbnail_path}` : null,
              duration: video.duration || 0,
              status: video.status || 'unprocessed',
              createdAt: video.created_at || new Date().toISOString()
            };
            console.debug('处理后的视频对象:', processedVideo);
            return processedVideo;
          });
          // 更新总数
          this.totalVideos = response.data.total || 0;
        } else {
          console.warn('响应数据格式不正确:', response.data);
          this.videos = [];
          this.totalVideos = 0;
        }
        
        console.info('最终存储的视频列表:', this.videos);
        return {
          videos: this.videos,
          total: this.totalVideos
        };
      } catch (error) {
        console.error('获取视频列表失败:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          stack: error.stack
        });
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    async uploadVideo(videoData) {
      this.loading = true;
      try {
        const formData = new FormData();
        formData.append('video', videoData.file);
        formData.append('title', videoData.title);
        formData.append('description', videoData.description);

        const response = await api.post('/videos', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        // 处理上传后的视频数据
        const processedVideo = {
          ...response.data,
          url: `/uploads/videos/${response.data.file_path.split('\\').pop()}`,
          thumbnail: response.data.thumbnail_path ? `/${response.data.thumbnail_path}` : null,
          duration: response.data.duration || 0,
          status: response.data.status || 'unprocessed',
          createdAt: response.data.created_at || new Date().toISOString()
        };
        
        if (Array.isArray(this.videos)) {
          this.videos.unshift(processedVideo);
        } else {
          this.videos = [processedVideo];
        }
        
        this.error = null;
        return processedVideo;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async recordVideo(streamData) {
      this.loading = true;
      try {
        const response = await api.post('/videos/record', streamData, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        this.videos.unshift(response.data);
        this.error = null;
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async deleteVideo(videoId) {
      try {
        await api.delete(`/videos/${videoId}`);
        this.videos = this.videos.filter(v => v.id !== videoId);
      } catch (error) {
        throw error;
      }
    },

    async deleteVideos(videoIds) {
      try {
        console.log('开始批量删除视频:', videoIds);
        await api.post('/videos/batch-delete', { videoIds });
        this.videos = this.videos.filter(v => !videoIds.includes(v.id));
        console.log('批量删除视频成功');
      } catch (error) {
        console.error('批量删除视频失败:', error);
        throw error;
      }
    },

    async analyzeVideo(videoId) {
      this.analyzing = true;
      try {
        const response = await api.post(`/videos/${videoId}/analyze`);
        
        const index = this.videos.findIndex(v => v.id === videoId);
        if (index !== -1) {
          this.videos[index] = {
            ...this.videos[index],
            analysis: response.data,
            status: 'processed'
          };
        }
        
        this.error = null;
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      } finally {
        this.analyzing = false;
      }
    },

    async startAnalysis(videoId, hand) {
      this.analyzing = true;
      try {
        console.debug('开始分析视频:', videoId, '手:', hand);
        
        const response = await api.post(`/videos/${videoId}/analyze`, {
          videoId,
          hand
        });
        
        return response.data;
      } catch (error) {
        console.error('视频分析失败:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          stack: error.stack
        });
        this.error = error.message;
        throw error;
      } finally {
        this.analyzing = false;
      }
    },

    async reAnalyze(videoId, hand) {
      this.analyzing = true;
      try {
        console.debug('重新分析视频:', videoId, '手:', hand);
        
        // 先删除旧的分析记录
        await api.delete(`/videos/${videoId}/analysis`, {
          params: { hand }
        });
        
        const response = await api.post(`/videos/${videoId}/analyze`, {
          videoId,
          hand,
          reAnalyze: true
        });
        
        return response.data;
      } catch (error) {
        console.error('视频重新分析失败:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          stack: error.stack
        });
        this.error = error.message;
        throw error;
      } finally {
        this.analyzing = false;
      }
    },

    async getAnalysisResult(videoId, hand) {
      try {
        const response = await api.get(`/videos/${videoId}/analysis`, {
          params: { hand }
        });
        return response.data;
      } catch (error) {
        if (error.response?.status === 404) {
          return null;
        }
        console.error('获取分析结果失败:', error);
        this.error = error.message;
        throw error;
      }
    },

    setCurrentVideo(video) {
      this.currentVideo = video
    },

    async fetchDashboardStats() {
      try {
        console.log('开始获取仪表盘数据...');
        const response = await api.get('/videos/dashboard');
        console.log('获取到的仪表盘数据:', response.data);
        
        // 确保返回的数据格式正确
        const data = response.data || {
          totalVideos: 0,
          totalDuration: 0,
          totalAnalysis: 0,
          scoreDistribution: {
            excellent: 0,
            good: 0,
            fair: 0,
            poor: 0
          },
          scoreTrend: [],
          uploadTrend: [],
          recentAnalysis: []
        };
        
        console.log('处理后的仪表盘数据:', data);
        
        // 更新store中的状态
        this.dashboardStats = {
          ...this.dashboardStats,
          ...data
        };
        
        console.log('更新后的 store 状态:', this.dashboardStats);
        return this.dashboardStats;
      } catch (error) {
        console.error('获取仪表盘数据失败:', error);
        this.error = error.message;
        throw error;
      }
    },
    
    async fetchUserRanking(params = {}) {
      try {
        console.log('开始获取用户排行榜数据...', params);
        const response = await api.get('/stats/user-ranking', { params });
        
        // 处理用户数据，确保所有必要字段都存在
        const processedData = Array.isArray(response.data) ? response.data.map(user => {
          // 默认设为null，这样在组件中可以使用默认头像（用户名首字母）
          let avatar = null;
          
          // 处理头像路径，只有在avatar字段存在且不为null/undefined/空字符串时进行处理
          if (user.avatar) {
            if (user.avatar.startsWith('http://') || user.avatar.startsWith('https://')) {
              avatar = user.avatar;
            } else if (user.avatar.startsWith('/')) {
              avatar = user.avatar;
            } else if (user.avatar.startsWith('uploads/')) {
              avatar = '/' + user.avatar;
            } else {
              avatar = `/uploads/avatars/${user.avatar}`;
            }
          }
          
          return {
            ...user,
            // 确保其他字段也有默认值
            avatar,
            username: user.username || '未知用户',
            videoCount: user.videoCount || 0,
            totalDuration: user.totalDuration || 0,
            averageScore: user.averageScore || 0,
            lastActivity: user.lastActivity || new Date().toISOString()
          };
        }) : [];
        
        return {
          data: processedData,
          totalCount: parseInt(response.headers['x-total-count'] || processedData.length)
        };
      } catch (error) {
        console.error('获取用户排行榜失败:', error);
        this.error = error.message;
        throw error;
      }
    }
  }
})