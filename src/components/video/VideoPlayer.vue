<template>
  <div class="video-player">
    <video
      ref="videoRef"
      :src="src"
      :controls="controls"
      :autoplay="autoplay"
      :muted="muted"
      :loop="loop"
      :poster="poster"
      @play="$emit('play')"
      @pause="$emit('pause')"
      @ended="$emit('ended')"
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleMetadataLoaded"
      @error="handleError"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import videojs from 'video.js'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  controls: {
    type: Boolean,
    default: true
  },
  autoplay: {
    type: Boolean,
    default: false
  },
  muted: {
    type: Boolean,
    default: false
  },
  loop: {
    type: Boolean,
    default: false
  },
  poster: {
    type: String,
    default: ''
  },
  preload: {
    type: String,
    default: 'metadata'
  }
})

const emit = defineEmits(['play', 'pause', 'ended', 'timeupdate', 'error', 'loaded'])

const videoRef = ref(null)
const player = ref(null)

const handleTimeUpdate = (event) => {
  emit('timeupdate', {
    currentTime: event.target.currentTime,
    duration: event.target.duration
  })
}

const handleMetadataLoaded = (event) => {
  emit('loaded', {
    duration: event.target.duration,
    videoWidth: event.target.videoWidth,
    videoHeight: event.target.videoHeight
  })
}

const handleError = (error) => {
  console.error('视频加载错误:', {
    error: error.target.error,
    src: props.src,
    networkState: error.target.networkState,
    readyState: error.target.readyState,
    headers: error.target.getResponseHeader?.('Content-Type')
  });
  
  // 检查是否是播放结束导致的错误
  if (error.target.networkState === 3 && error.target.readyState === 0) {
    // 这是播放结束后的正常状态，不显示错误消息
    emit('ended');
    return;
  }
  
  // 检查是否是视频源不存在
  if (error.target.networkState === 3) {
    console.error('视频源不存在或无法访问');
    ElMessage.error('视频源不存在或无法访问，请检查视频文件是否存在');
    emit('error', error);
    return;
  }
  
  let errorMessage = '视频加载失败';
  if (error.target.error) {
    switch (error.target.error.code) {
      case 1:
        errorMessage = '视频加载被中断';
        break;
      case 2:
        errorMessage = '网络错误导致视频加载失败';
        break;
      case 3:
        errorMessage = '视频解码失败';
        break;
      case 4:
        errorMessage = '视频源不可用';
        break;
      default:
        errorMessage = `视频加载失败: ${error.target.error.message}`;
    }
  }
  
  ElMessage.error(errorMessage);
  emit('error', error);
}

// 添加安全停止视频的方法
const safeStop = () => {
  if (videoRef.value) {
    // 先暂停播放
    videoRef.value.pause();
    // 清空视频源
    videoRef.value.src = '';
    // 重置视频元素
    videoRef.value.load();
  }
}

// 监听src变化，重新加载视频
watch(() => props.src, (newSrc) => {
  if (videoRef.value && newSrc) {
    videoRef.value.load()
  }
})

// 初始化播放器
const initPlayer = () => {
  if (player.value) {
    player.value.dispose()
  }

  player.value = videojs(videoRef.value, {
    controls: props.controls,
    autoplay: props.autoplay,
    preload: props.preload,
    poster: props.poster,
    fluid: true,
    aspectRatio: '16:9',
    playbackRates: [0.5, 1, 1.5, 2],
    controlBar: {
      children: [
        'playToggle',
        'volumePanel',
        'currentTimeDisplay',
        'timeDivider',
        'durationDisplay',
        'progressControl',
        'playbackRateMenuButton',
        'fullscreenToggle'
      ]
    }
  })

  // 监听错误事件
  player.value.on('error', (error) => {
    console.error('视频播放器错误:', error)
    emit('error', error)
  })

  // 监听时间更新事件
  player.value.on('timeupdate', () => {
    emit('timeupdate', player.value.currentTime())
  })
}

// 暴露方法给父组件
defineExpose({
  load: () => {
    if (player.value) {
      player.value.load()
    }
  },
  player: player,
  play: () => videoRef.value?.play(),
  pause: () => videoRef.value?.pause(),
  stop: safeStop,
  seek: (time) => {
    if (videoRef.value) {
      videoRef.value.currentTime = time
    }
  }
})

onMounted(() => {
  if (videoRef.value) {
    console.debug('视频元素已挂载:', {
      src: props.src,
      networkState: videoRef.value.networkState,
      readyState: videoRef.value.readyState
    });
    
    if (props.autoplay) {
      videoRef.value.play().catch((error) => {
        console.error('自动播放失败:', error);
        // 自动播放失败时静音播放
        videoRef.value.muted = true;
        videoRef.value.play();
      });
    }
  }
})

onBeforeUnmount(() => {
  safeStop();
})
</script>

<style lang="scss" scoped>
.video-player {
  width: 100%;
  min-height: 400px;
  max-height: 600px;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  
  video {
    width: 100%;
    height: 100%;
    object-fit: contain;
    max-height: 600px;
  }
}
</style> 