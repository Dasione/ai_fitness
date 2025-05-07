<template>
  <div class="realtime-training">
    <div class="video-container">
      <canvas ref="processedCanvas" class="processed-feed"></canvas>
      <div v-if="!isCameraConnected" class="camera-placeholder">
        <el-icon><VideoCamera /></el-icon>
        <p>请开始录制</p>
      </div>
      <div v-if="isRecording" class="recording-indicator">
        <el-icon color="#ff4949"><VideoCamera /></el-icon>
        录制中...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'
import { useVideoStore } from '@/store/modules/video'

const emit = defineEmits(['update:isRecording', 'update:recordedVideoFile'])

const processedCanvas = ref(null)
const isRecording = ref(false)
const websocket = ref(null)
const recordedVideoFile = ref(null)
const videoStore = useVideoStore()
const isCameraConnected = ref(false)

// 处理WebSocket消息
const handleWebSocketMessage = (event) => {
  try {
    const data = JSON.parse(event.data)
    console.log('[WebSocket] 收到消息:', {
      type: data.type,
      data: data.data,
      isRecording: isRecording.value,
      wsState: websocket.value?.readyState
    })
    
    switch (data.type) {
      case 'frame':
        updateCanvas(data.data)
        break
      case 'video_ready':
        console.log('[WebSocket] 收到视频就绪消息:', {
          url: data.data?.url,
          isRecording: isRecording.value,
          wsState: websocket.value?.readyState
        })
        handleVideoReady(data.data)
        break
      case 'error':
        console.error('[WebSocket] 收到错误消息:', {
          message: data.message,
          isRecording: isRecording.value,
          wsState: websocket.value?.readyState
        })
        ElMessage.error(data.message || '处理视频时发生错误')
        break
      default:
        console.warn('[WebSocket] 未知消息类型:', {
          type: data.type,
          isRecording: isRecording.value,
          wsState: websocket.value?.readyState
        })
    }
  } catch (error) {
    console.error('[WebSocket] 处理消息失败:', {
      error,
      eventData: event.data,
      isRecording: isRecording.value,
      wsState: websocket.value?.readyState
    })
  }
}

// 初始化WebSocket连接
const initWebSocket = () => {
  console.log('[WebSocket] 开始初始化连接...', {
    currentWS: websocket.value,
    isRecording: isRecording.value
  })

  if (websocket.value?.readyState === WebSocket.OPEN) {
    console.log('[WebSocket] 已存在活跃连接，先关闭')
    closeWebSocket()
  }

  // 添加延迟，等待服务完全启动
  setTimeout(() => {
    try {
      websocket.value = new WebSocket('ws://localhost:8765')
      
      websocket.value.onopen = () => {
        console.log('[WebSocket] 连接已建立:', {
          readyState: websocket.value.readyState,
          isRecording: isRecording.value
        })
        // 不立即设置连接状态，等待服务完全加载
        setTimeout(() => {
          isCameraConnected.value = true
          ElMessage.success('视频处理服务已连接')
        }, 5000) // 等待5秒，确保服务完全加载
      }
      
      websocket.value.onmessage = handleWebSocketMessage
      
      websocket.value.onerror = (error) => {
        console.error('[WebSocket] 连接错误:', {
          error,
          readyState: websocket.value?.readyState,
          isRecording: isRecording.value
        })
        isCameraConnected.value = false
        ElMessage.error('视频处理服务连接失败')
      }
      
      websocket.value.onclose = (event) => {
        console.log('[WebSocket] 连接已关闭:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          readyState: websocket.value?.readyState,
          isRecording: isRecording.value
        })
        
        isCameraConnected.value = false
        
        if (event.code !== 1000 && event.code !== 1001) {
          console.log('[WebSocket] 非正常关闭，尝试重连')
          reconnectWebSocket()
        }
      }
    } catch (error) {
      console.error('[WebSocket] 创建连接失败:', error)
      isCameraConnected.value = false
      ElMessage.error('创建视频处理服务连接失败')
    }
  }, 2000) // 等待2秒让服务完全启动
}

// 更新Canvas显示处理后的帧
const updateCanvas = (base64Frame) => {
  const canvas = processedCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const img = new Image()
  img.onload = () => {
    canvas.width = img.width
    canvas.height = img.height
    ctx.drawImage(img, 0, 0)
  }
  img.src = 'data:image/jpeg;base64,' + base64Frame
}

// 处理视频就绪消息
const handleVideoReady = async (data) => {
  console.log('[视频处理] 开始处理就绪视频:', {
    data,
    isRecording: isRecording.value,
    wsState: websocket.value?.readyState
  })

  try {
    if (!data.url) {
      throw new Error('视频URL不存在')
    }

    // 构建完整的URL
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'
    const fullUrl = `${baseUrl}${data.url}`
    console.log('[视频处理] 请求视频URL:', fullUrl)

    // 获取视频数据
    const response = await fetch(fullUrl)
    if (!response.ok) {
      throw new Error(`获取视频数据失败: ${response.status} ${response.statusText}`)
    }
    
    console.log('[视频处理] 获取视频数据成功')
    
    // 获取视频blob
    const blob = await response.blob()
    console.log('[视频处理] 获取视频blob成功:', {
      size: blob.size,
      type: blob.type
    })
    
    // 创建视频文件对象
    recordedVideoFile.value = new File([blob], data.filename || 'training-video.mp4', { type: 'video/mp4' })
    emit('update:recordedVideoFile', recordedVideoFile.value)
    
    console.log('[视频处理] 视频文件已创建:', {
      name: recordedVideoFile.value.name,
      size: recordedVideoFile.value.size,
      type: recordedVideoFile.value.type
    })
    
    // 重置录制状态
    isRecording.value = false
    emit('update:isRecording', false)

    console.log('[WebSocket] 准备重置连接')
    // 关闭当前WebSocket连接
    closeWebSocket()
    
    // 延迟一段时间后重新初始化WebSocket
    setTimeout(() => {
      console.log('[WebSocket] 开始重新初始化连接')
      initWebSocket()
    }, 1000)
  } catch (error) {
    console.error('[视频处理] 处理失败:', {
      error,
      isRecording: isRecording.value,
      wsState: websocket.value?.readyState
    })
    ElMessage.error(`处理视频数据失败: ${error.message}`)
    
    // 重置状态
    isRecording.value = false
    emit('update:isRecording', false)
    recordedVideoFile.value = null
    emit('update:recordedVideoFile', null)

    // 关闭并重新初始化WebSocket连接
    closeWebSocket()
    setTimeout(() => {
      initWebSocket()
    }, 1000)
  }
}

// 开始录制
const startRecording = async (hand) => {
  console.log('[录制] 尝试开始录制:', {
    websocketState: websocket.value?.readyState,
    isRecording: isRecording.value,
    hand: hand
  })
  
  try {
    if (!websocket.value || websocket.value.readyState !== WebSocket.OPEN) {
      console.log('[录制] WebSocket未连接，尝试重新连接')
      initWebSocket()
      return
    }

    isRecording.value = true
    emit('update:isRecording', true)
    const message = { 
      type: 'start',
      hand: hand,
      timestamp: Date.now()
    }
    console.log('[录制] 发送开始录制消息:', message)
    websocket.value.send(JSON.stringify(message))
    ElMessage.success('开始录制')
  } catch (error) {
    console.error('[录制] 开始录制失败:', {
      error,
      websocketState: websocket.value?.readyState,
      isRecording: isRecording.value
    })
    ElMessage.error('开始录制失败: ' + error.message)
    isRecording.value = false
    emit('update:isRecording', false)
  }
}

// 停止录制
const stopRecording = () => {
  console.log('[录制] 尝试停止录制:', {
    websocketState: websocket.value?.readyState,
    isRecording: isRecording.value
  })
  
  if (isRecording.value) {
    try {
      if (!websocket.value || websocket.value.readyState !== WebSocket.OPEN) {
        throw new Error('视频处理服务未连接')
      }

      // 发送停止请求
      const message = { 
        type: 'stop',
        timestamp: Date.now()
      }
      console.log('[录制] 发送停止录制消息:', message)
      websocket.value.send(JSON.stringify(message))
      
      console.log('[录制] 等待视频处理完成')
      ElMessage.success('录制已停止，正在处理视频...')
    } catch (error) {
      console.error('[录制] 停止录制失败:', {
        error,
        websocketState: websocket.value?.readyState,
        isRecording: isRecording.value
      })
      ElMessage.error('停止录制失败: ' + error.message)
      
      // 重置状态并重新初始化连接
      isRecording.value = false
      emit('update:isRecording', false)
      closeWebSocket()
      setTimeout(() => {
        initWebSocket()
      }, 1000)
    }
  }
}

// 处理上传成功
const handleUploadSuccess = () => {
  recordedVideoFile.value = null
  emit('update:recordedVideoFile', null)
  ElMessage.success('视频上传成功')
  
  // 重置摄像头画面
  const canvas = processedCanvas.value
  if (canvas) {
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
  
  // 重置连接状态
  isCameraConnected.value = false
}

// 关闭WebSocket连接
const closeWebSocket = () => {
  console.log('[WebSocket] 准备关闭连接:', {
    websocketState: websocket.value?.readyState,
    isRecording: isRecording.value
  })
  
  if (websocket.value) {
    // 如果正在录制，先发送停止消息
    if (isRecording.value) {
      try {
        const message = { 
          type: 'stop',
          timestamp: Date.now()
        }
        console.log('[WebSocket] 发送停止录制消息:', message)
        websocket.value.send(JSON.stringify(message))
      } catch (error) {
        console.error('[WebSocket] 发送停止消息失败:', error)
      }
    }
    
    // 重置状态
    isRecording.value = false
    emit('update:isRecording', false)
    
    // 关闭连接
    try {
      websocket.value.close(1000, '正常关闭')
      console.log('[WebSocket] 连接已关闭')
    } catch (error) {
      console.error('[WebSocket] 关闭连接失败:', error)
    }
    websocket.value = null
  }
}

// 重新连接WebSocket
const reconnectWebSocket = () => {
  console.log('[WebSocket] 准备重新连接:', {
    websocketState: websocket.value?.readyState,
    isRecording: isRecording.value
  })
  
  if (!websocket.value || websocket.value.readyState === WebSocket.CLOSED) {
    console.log('[WebSocket] 连接已断开，尝试重新连接')
    
    // 如果之前正在录制，重置录制状态
    if (isRecording.value) {
      isRecording.value = false
      emit('update:isRecording', false)
      ElMessage.warning('录制因连接断开而中止')
    }
    
    // 延迟3秒后重新连接
    setTimeout(() => {
      console.log('[WebSocket] 开始重新连接')
      initWebSocket()
    }, 3000)
  }
}

// 添加WebSocket状态监听
watch(() => websocket.value?.readyState, (state, oldState) => {
  console.log('WebSocket状态变化:', {
    oldState,
    newState: state,
    isRecording: isRecording.value
  })
  
  if (state === WebSocket.CLOSED) {
    console.log('WebSocket连接已关闭，尝试重新连接...')
    reconnectWebSocket()
  } else if (state === WebSocket.OPEN && oldState === WebSocket.CONNECTING) {
    console.log('WebSocket重新连接成功')
    ElMessage.success('视频处理服务已连接')
  }
})

// 监听服务状态变化
watch(() => true, (newValue) => {
  if (newValue) {
    console.log('[WebSocket] 服务已启动，初始化连接')
    initWebSocket()
  } else {
    console.log('[WebSocket] 服务已停止，关闭连接')
    closeWebSocket()
  }
})

// 暴露方法给父组件
defineExpose({
  startRecording,
  stopRecording,
  handleUploadSuccess
})

onMounted(() => {
  initWebSocket()
})

onUnmounted(() => {
  // 组件卸载时关闭WebSocket连接
  closeWebSocket()
})
</script>

<style lang="scss" scoped>
.realtime-training {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .video-container {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    background-color: #f5f7fa;
    border-radius: 8px;
    overflow: hidden;
    
    .processed-feed {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    .camera-placeholder {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: #909399;
      font-size: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      
      .el-icon {
        font-size: 32px;
      }
    }
    
    .recording-indicator {
      position: absolute;
      top: 10px;
      right: 10px;
      background: rgba(255, 73, 73, 0.8);
      color: white;
      padding: 5px 10px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 5px;
      z-index: 3;
      
      .el-icon {
        animation: pulse 1.5s infinite;
      }
    }
  }
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style> 