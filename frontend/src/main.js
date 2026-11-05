import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
// 图标按需引入：原 `import * as ElementPlusIconsVue` + Object.entries 动态注册，
// 打包器无法 tree-shake，@element-plus/icons-vue 全部 293 个图标都会进产物。
// 下面只列各页面实际用到的图标（脚本扫描 src 得到），仍保持全局注册，
// 因此模板里 <el-icon><Search /></el-icon> 与 icon: 'Coin' 这类写法都无需改动。
// 注：App.vue 里的 <History /> 不在图标包导出列表中（原本就无法解析），故未列入。
import {
  Aim, ArrowLeft, Bell, Bottom, Box, ChatDotRound, CircleCheckFilled,
  CircleCloseFilled, CirclePlus, Clock, Close, Coin, Collection, Connection,
  Cpu, DataAnalysis, DataLine, Delete, Download, EditPen, Files, Fold,
  FolderOpened, Guide, Histogram, InfoFilled, Lightning, List, Loading,
  Location, Lock, MagicStick, Menu, Money, Monitor, Moon, Odometer,
  OfficeBuilding, Platform, Promotion, QuestionFilled, Refresh, Right,
  ScaleToOriginal, Search, Setting, Share, Star, Sunny, SwitchButton, Timer,
  Top, TrendCharts, Trophy, User, UserFilled, Van, Warning
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

const icons = {
  Aim, ArrowLeft, Bell, Bottom, Box, ChatDotRound, CircleCheckFilled,
  CircleCloseFilled, CirclePlus, Clock, Close, Coin, Collection, Connection,
  Cpu, DataAnalysis, DataLine, Delete, Download, EditPen, Files, Fold,
  FolderOpened, Guide, Histogram, InfoFilled, Lightning, List, Loading,
  Location, Lock, MagicStick, Menu, Money, Monitor, Moon, Odometer,
  OfficeBuilding, Platform, Promotion, QuestionFilled, Refresh, Right,
  ScaleToOriginal, Search, Setting, Share, Star, Sunny, SwitchButton, Timer,
  Top, TrendCharts, Trophy, User, UserFilled, Van, Warning
}
for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
