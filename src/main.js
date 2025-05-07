/**
 * 应用程序入口文件
 * 配置Vue应用实例和全局插件
 */
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './router'
import pinia from './store'

const app = createApp(App)

// 注册Element Plus图标组件
Object.entries(ElementPlusIconsVue).forEach(([key, component]) => {
  app.component(key, component)
})

app.use(pinia)
   .use(router)
   .use(ElementPlus)
   .mount('#app')
