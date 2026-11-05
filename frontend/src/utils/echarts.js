import * as echarts from 'echarts/core'
import {
  BarChart, LineChart, PieChart,
  ScatterChart, RadarChart, SunburstChart,
  TreeChart, TreemapChart, GraphChart,
  MapChart, GaugeChart, FunnelChart,
  EffectScatterChart, HeatmapChart
} from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent,
  DataZoomComponent, MarkLineComponent, MarkPointComponent,
  TitleComponent, VisualMapComponent, GeoComponent,
  ToolboxComponent, BrushComponent, RadarComponent,
  GraphicComponent, DatasetComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart, LineChart, PieChart,
  ScatterChart, RadarChart, SunburstChart,
  TreeChart, TreemapChart, GraphChart,
  MapChart, GaugeChart, FunnelChart,
  EffectScatterChart, HeatmapChart,
  GridComponent, TooltipComponent, LegendComponent,
  DataZoomComponent, MarkLineComponent, MarkPointComponent,
  TitleComponent, VisualMapComponent, GeoComponent,
  ToolboxComponent, BrushComponent, RadarComponent,
  GraphicComponent, DatasetComponent,
  CanvasRenderer
])

export default echarts
export { echarts }
