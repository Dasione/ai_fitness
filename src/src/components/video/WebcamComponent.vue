<template>
  <div class="webcam-container">
    <video
      ref="video"
      :width="width"
      :height="height"
      autoplay
      playsinline
      class="webcam-video"
    ></video>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  width: {
    type: [Number, String],
    default: 640
  },
  height: {
    type: [Number, String],
    default: 480
  },
  deviceId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['error', 'started', 'stopped', 'cameras'])

const video = ref(null)
let stream = null

// 获取摄像头列表
const getCameras = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    const cameras = devices.filter(device => device.kind === 'videoinput')
    emit('cameras', cameras)
    return cameras
  } catch (error) {
    emit('error', error)
    return []
  }
}

// 启动摄像头
const start = async () => {
  try {
    const constraints = {
      video: props.deviceId
        ? { deviceId: { exact: props.deviceId } }
        : true
    }
    
    stream = await navigator.mediaDevices.getUserMedia(constraints)
    if (video.value) {
      video.value.srcObject = stream
    }
    emit('started', stream)
  } catch (error) {
    emit('error', error)
  }
}

// 停止摄像头
const stop = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
    if (video.value) {
      video.value.srcObject = null
    }
    emit('stopped')
  }
}

// 获取当前视频流
const getStream = () => stream

// 在组件挂载时初始化
onMounted(async () => {
  await getCameras()
  await start()
})

// 在组件卸载前清理
onBeforeUnmount(() => {
  stop()
})

// 监听设备ID变化
watch(() => props.deviceId, async (newDeviceId) => {
  if (stream) {
    stop()
  }
  if (newDeviceId) {
    await start()
  }
})

// 暴露方法给父组件
defineExpose({
  start,
  stop,
  getStream,
  getCameras
})
</script>

<style scoped>
.webcam-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.webcam-video {
  background-color: #000;
  border-radius: 8px;
}
</style> 