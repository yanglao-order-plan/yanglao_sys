<script lang="ts" setup>
import { onMounted, watch, nextTick, computed, reactive, ref } from "vue"
import { type ITaskData, IFlowData, IWeightData, IArgData, OWeightData } from "@/api/infer/types/infer"
import Argument from '@/components/argument/module.vue'
import { Refresh } from "@element-plus/icons-vue"
import { getAllTasksApi, getCurrentTaskApi, getCurrentFlowApi, getCurrentWeightApi, getCurrentParamApi, getCurrentHyperApi,
  switchTaskApi, switchFlowApi, switchWeightApi, switchParamApi, switchHyperApi, predictModelApi, loadModelApi, getAllCurrentWeightsApi} from "@/api/infer"
import { ElMessage } from "element-plus"
import type { CascaderValue } from 'element-plus'
import * as echarts from "echarts"

defineOptions({
  name: "Infer"
})

const choosen = ref<boolean>(false)
const loading = ref<boolean>(false)
const loaded = ref<boolean>(false)
const predicting = ref<boolean>(false)
const tasksData = ref<ITaskData[]>([])
const flowsData = ref<IFlowData[]>([])
const weightsData = ref<IWeightData[]>([])
const paramsData = ref<IArgData[]>([])
const hypersData = ref<IArgData[]>([])

const selectedTaskOptions = ref([])
const selectedFlowOptions = ref([])
const taskOptions = ref<{ value: string; label: string; children: { value: string; label: string }[] }[]>([])
const flowOptions = ref<{ value: string; label: string; children: { value: string; label: string }[] }[]>([])
const weightOptions = ref<{ [key: string]: { value: string; label: string; disabled: boolean }[]}>({})

const currentTaskData = reactive({
  taskType: "",
  task: "",
})

const selectedTaskData = reactive({
  taskType: "",
  task: "",
})

const currentFlowData = reactive({
  flow: "",
  release: "",
})

const selectedFlowData = reactive({
  flow: "",
  release: "",
})

const currentWeightData = reactive<{ [key: string]: string }>({});
const selectedWeightData = reactive<{ [key: string]: string }>({});
const currentParamData = reactive<{ [key: string]: any }>({});
const handledParamData = reactive<{ [key: string]: any }>({});
const currentHyperData = reactive<{ [key: string]: any }>({});
const handledHyperData = reactive<{ [key: string]: any }>({});

const clearSelectedFlow = () => {
  selectedFlowData.flow = "";
  selectedFlowData.release = "";
  flowsData.value.length = 0
};

const clearSelectedWeight = () => {
  for (const key in selectedWeightData) {
    delete selectedWeightData[key];
  }
  weightsData.value.length = 0
};

const clearHandledParam = () => {
  for (const key in handledParamData) {
    delete handledParamData[key];
  }
  paramsData.value.length = 0
};

const clearHandledHyper = () => {
  for (const key in handledHyperData) {
    delete handledHyperData[key];
  }
  hypersData.value.length = 0
};

const clearHelper = (keys: string[]) => {
  keys.forEach(key => {
    if (key === 'flow') clearSelectedFlow();
    else if (key === 'weight') clearSelectedWeight();
    else if (key === 'param') clearHandledParam();
    else if (key === 'hyper') clearHandledHyper();
  });
};

const inferImageData: any = reactive({
  resultBase64: [],
  resultImageUrl: computed(() => {
    if (inferImageData.resultBase64.length > 0) {
      return inferImageData.resultBase64.map((base64: string) => {
        const blob = dataURItoBlob(base64);  // 将 base64 转换为 Blob
        return URL.createObjectURL(blob);    // 生成 URL
      });
    } else {
      return [];  // 如果没有 base64 数据，返回空组
    }
  }),
  inferResult: [],
  inferCroppers: computed(() => {
  if (inferImageData.inferResult.length > 0) {
    const res = inferImageData.inferResult.map((item: any) => {
      if (item.cropper){
        const base64 = item.cropper;
        const blob = dataURItoBlob(base64);
        return URL.createObjectURL(blob);
      } else {
        return null
      }
    });
    console.log(res)
    return res
  } else {
    return [];
  }
}),
  inferDescription: "",
  inferPeriod: ""
})

const originImageUrl = computed(() => {
  if(handledHyperData["origin_image"] !== null &&
     handledHyperData["origin_image"] !== undefined
  ) {
    console.log(handledHyperData["origin_image"])
    const blob = dataURItoBlob(handledHyperData["origin_image"])
    return URL.createObjectURL(blob)
  }
  return null
})

const dataURItoBlob = (dataURI: any) => {
  const byteString = atob(dataURI.split(",")[1])
  const mimeString = dataURI.split(",")[0].split(":")[1].split(";")[0]
  const ab = new ArrayBuffer(byteString.length)
  const ia = new Uint8Array(ab)
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i)
  }
  return new Blob([ab], { type: mimeString })
}

const getAllTasks = () => {
  loading.value = true
  getAllTasksApi()
    .then((res: any) => {
      tasksData.value = res.data
      taskOptions.value = generateTaskCascaderOptions(res.data)
    })
    .catch(() => {
      tasksData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}

const getCurrentTask = () => {
  getCurrentTaskApi().then((res) => {
    currentTaskData.taskType = res.data.taskTypeName
    currentTaskData.task = res.data.taskName
  })
}

const getCurrentFlow = () => {
  getCurrentFlowApi().then((res) => {
    currentFlowData.flow = res.data.flowName
    currentFlowData.release = res.data.releaseName
  })
  .finally(() => {
    paramsData.value.forEach((element: any) => {  // 提前装载初始值
      handledParamData[element['argName']] = element['argDefault']
    });
    getAllCurrentWeights()
  })

}

const getAllCurrentWeights = () => {
  getAllCurrentWeightsApi().then((res) => {
    res.data.forEach((element: any) => {  // 提前装载初始值
      selectedWeightData[element.weightKey] = element.weightName
    });
  }).catch((error) => {
    console.error("Error fetching weight data:", error);
  });
};

const getCurrentWeight = (weigthKey: string|number) => {
  getCurrentWeightApi({
    currentWeightKey: weigthKey
  }).then((res) => {
    currentWeightData[weigthKey] = res.data.weightName;
    selectedWeightData[weigthKey] = res.data.weightName;
  }).catch((error) => {
    console.error("Error fetching weight data:", error);
  });
};

const getCurrentParam = (paramName: string) => {
  getCurrentParamApi({currentParamName: paramName}).then((res) => {
    currentParamData[res.data.argName] = res.data.argValue;
  }).catch((error) => {
    console.error("Error fetching weight data:", error);
  });
};

const getCurrentHyper = (hyperName: string) => {
  getCurrentHyperApi({currentHyperName: hyperName}).then((res) => {
    currentHyperData[res.data.argName] = res.data.argValue;
  }).catch((error) => {
    console.error("Error fetching weight data:", error);
  });
};

const generateTaskCascaderOptions = (list: ITaskData[]) => {
  const options: { value: string; label: string; children: { value: string; label: string }[] }[] = []
  const map: { [key: string]: { value: string; label: string; children: { value: string; label: string }[] } } = {}
  list.forEach((item) => {
    const taskType = item.taskTypeName
    const task = item.taskName
    if (!map[taskType]) {
      map[taskType] = {
        value: taskType,
        label: taskType,
        children: []
      }
      options.push(map[taskType])
    }
    map[taskType].children.push({
      value: task,
      label: task
    })
  })
  return options
}

const generateFlowCascaderOptions = (list: IFlowData[]) => {
  const options: { value: string; label: string; children: { value: string; label: string }[] }[] = []
  const map: { [key: string]: { value: string; label: string; children: { value: string; label: string }[] } } = {}
  list.forEach((item) => {
    const flow = item.flowName
    const release = item.releaseName
    const releaseName = item.releaseShowName
    if (!map[flow]) {
      map[flow] = {
        value: flow,
        label: flow,
        children: []
      }
      options.push(map[flow])
    }
    map[flow].children.push({
      value: release,
      label: releaseName
    })
  })
  return options
}

const generateWeightOptions = (list: IWeightData[]) => {
  const optionsMap: { [key: string]: { value: string; label: string; disabled: boolean }[] } = {};
  list.forEach((item) => {
    if (!optionsMap[item.weightKey]) {
      optionsMap[item.weightKey] = [];
    }
    optionsMap[item.weightKey].push({
      value: item.weightName,
      label: item.weightName,
      disabled: !item.weightEnable
    });
  });
  return optionsMap;
};

const handleTaskChange = (selectedOptions: CascaderValue) => {
  if (!Array.isArray(selectedOptions) || selectedOptions.length !== 2) return
  selectedTaskData.taskType = selectedOptions[0] as string
  selectedTaskData.task = selectedOptions[1] as string
  const message = `已选择任务类型：${selectedOptions[0]} 任务：${selectedOptions[1]}`
  ElMessage({
    message: message,
    type: "success"
  })
}

const handleFlowChange = (selectedOptions: CascaderValue) => {
  if (!Array.isArray(selectedOptions) || selectedOptions.length !== 2) return
  selectedFlowData.flow = selectedOptions[0] as string
  selectedFlowData.release = selectedOptions[1] as string
  const message = `已选择工作流：${selectedOptions[0]} 版本：${selectedOptions[1]}`
  ElMessage({
    message: message,
    type: "success"
  })
}

const handleWeightChange = (weightKey: string|number) => {
  const weightName = selectedWeightData[weightKey]
  handleWeightSwitch(weightKey)
  const message = `已经选择权重${weightKey}: ${weightName}`
    ElMessage({
      message: message,
      type: "success"
    })
}

const handleParamChange = (paramName: string, paramValue: any) => {
  handledParamData[paramName] = paramValue
  handleParamSwitch(paramName)
  const message = `已经完成配置${paramName}: ${paramValue}`
  ElMessage({
    message: message,
    type: "success"
  })
}

const handleHyperChange = (hyperName: string, hyperValue: any) => {
  handledHyperData[hyperName] = hyperValue
  handleHyperSwitch(hyperName)
  const message = `已经完成参数${hyperName}: ${hyperValue}`
  ElMessage({
    message: message,
    type: "success"
  })
}

interface CascaderProps {
  expandTrigger?: "click" | "hover"
}

const props: CascaderProps = {
  expandTrigger: "hover" as const
}

const handleTaskSwitch = () => {
  if (
    selectedTaskData.taskType === currentTaskData.taskType &&
    selectedTaskData.task === currentTaskData.task
  ) {
    ElMessage({
      message: "当前选中的已经是该任务",
      type: "warning"
    })
    return
  } else if (selectedTaskData.taskType === "" || selectedTaskData.task === "") {
    ElMessage({
      message: "请先选择任务",
      type: "warning"
    })
    return
  }
  switchTaskApi({
    switchTaskTypeName: selectedTaskData.taskType,
    switchTaskName: selectedTaskData.task,
  }).then((res) => {
    clearHelper(['flow', 'weight', 'param', 'hyper'])
    flowsData.value = res.data
    flowOptions.value = generateFlowCascaderOptions(res.data)
    getCurrentTask()
  })
  .catch(() => {
      tasksData.value = []
  })
  .finally(() => {
    choosen.value = false
    loaded.value = false
    loading.value = false
  })
}

const loadDefault = (mode: string ) => {
  if (mode === 'param'){
    paramsData.value.forEach((element: any) => {
      handledParamData[element.argName] = element?.argDefault
    });
  } else if (mode === 'hyper'){
    hypersData.value.forEach((element: any) => {
      handledHyperData[element.argName] = element?.argDefault
    });
  }
}

const handleFlowSwitch = () => {
  if (
    selectedFlowData.flow === currentFlowData.flow &&
    selectedFlowData.release === currentFlowData.release
  ) {
    ElMessage({
      message: "当前选中的已经是该模型",
      type: "warning"
    })
    return
  } else if (selectedFlowData.flow === "" || selectedFlowData.release === "") {
    ElMessage({
      message: "请先选择模型",
      type: "warning"
    })
    return
  }
  switchFlowApi({
    switchFlowName: selectedFlowData.flow,
    switchReleaseName: selectedFlowData.release,
  }).then((res) => {
    clearHelper(['weight', 'param', 'hyper'])
    weightsData.value = res.data["weight"]
    weightOptions.value = generateWeightOptions(res.data["weight"])
    if (res.data["param"] && res.data["param"].length > 0) {
        paramsData.value = res.data["param"]
        loadDefault('param')
      } else {
        console.warn("No params found in the response.");
      }
    getCurrentFlow()
  })
  .catch(() => {
      flowsData.value = []
  })
  .finally(() => {
    loaded.value = false
    loading.value = false
    choosen.value = true
  })
}

const handleWeightSwitch = (weightKey: string|number) => {
  const selectedWeightName = selectedWeightData[weightKey]
  if (  // 字典值比较
  selectedWeightName === currentWeightData[weightKey]
  ) {
    ElMessage({
      message: "当前选中的已经是该权重",
      type: "warning"
    })
    return
  } else if (selectedWeightName === "") {
    ElMessage({
      message: "请先选择权重",
      type: "warning"
    })
    return
  }
  switchWeightApi({
    switchWeightKey: weightKey,
    switchWeightName: selectedWeightName,
  }).then(() => {
    getCurrentWeight(weightKey)
  })
  .catch(() => {
      weightsData.value = []
  })
  .finally(() => {
    loaded.value = false
    loading.value = false
    choosen.value = true
  })
}

const handleParamSwitch = (paramName: string) => {
  const handledParamValue = handledParamData[paramName]
  if (  // 字典值比较
    handledParamValue === currentParamData[paramName]
  ) {
    ElMessage({
      message: "当前设置参数已是该值",
      type: "warning"
    })
    return
  } else if (handledParamValue === "") {
    ElMessage({
      message: "请先设置参数",
      type: "warning"
    })
    return
  }
  switchParamApi({
    switchParamName: paramName,
    switchParamValue: handledParamValue,
  }).then(() => {
    getCurrentParam(paramName)
  })
  .catch(() => {
      paramsData.value = []
  })
  .finally(() => {
    loaded.value = false
    loading.value = false
    choosen.value = true
  })
}

const handleHyperSwitch = (hyperName: string) => {
  const handledHyperValue = handledHyperData[hyperName]
  if (  // 字典值比较
    handledHyperValue === currentHyperData[hyperName]
  ) {
    ElMessage({
      message: "当前设置参数已是该值",
      type: "warning"
    })
    return
  } else if (handledHyperValue === "") {
    ElMessage({
      message: "请先设置参数",
      type: "warning"
    })
    return
  }
  switchHyperApi({
    switchHyperName: hyperName,
    switchHyperValue: handledHyperValue,
  }).then(() => {
    getCurrentHyper(hyperName)
  })
  .catch(() => {
      hypersData.value = []
  })
  .finally(() => {
    loaded.value = true
    loading.value = false
    choosen.value = true
  })
}

const handleLoadModel = () => {
  loadModelApi().then((res) => {
    if (res.data && res.data.length > 0) {
        hypersData.value = res.data;
        console.log(res.data)
        loadDefault('hyper')
      } else {
        console.warn("No hypers found in the response.");
      }
  })
  .catch(() => {
    ElMessage({
      message: "",
      type: "warning"
    })
  })
  .finally(() => {
    loading.value = false
    loaded.value = true
  })
}

const handleModelPredict = () => {
  predictModelApi().then((res) => {
    inferImageData.resultBase64 = res.data.resultBase64
    inferImageData.inferResult = res.data.inferResult
    inferImageData.inferPeriod = res.data.inferPeriod
    inferImageData.inferDescription = res.data.inferDescription
  })
  .catch(() => {
    ElMessage({
      message: "推理响应有误",
      type: "warning"
    })
  })
  .finally(() => {
    predicting.value = false
  })
}

const resetResult = () => {
  inferImageData.resultBase64 = ""
  inferImageData.inferResult = []
  inferImageData.inferDescription = ""
  inferImageData.inferPeriod = ""

  if (inferImageData.resultImageUrl) {
    URL.revokeObjectURL(inferImageData.resultImageUrl)
  }
  ElMessage({
      message: "结果清除成功",
      type: "success"
    })
}

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts

const updateChart = () => {
  if (!chartInstance || !chartRef.value) return

  const categoryCounts = inferImageData.inferResult.reduce((acc: Record<string, number>, item: any) => {
    acc[item.label] = (acc[item.label] || 0) + 1
    return acc
  }, {})

  const categories = Object.keys(categoryCounts)
  const counts = Object.values(categoryCounts)

  const option = {
    title: {
      text: '检测类别统计'
    },
    tooltip: {},
    xAxis: {
      type: 'category',
      data: categories
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      name: '数量',
      data: counts,
      type: 'bar'
    }]
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }
})

watch(() => inferImageData.inferResult, () => {
  updateChart()
}, { deep: true })

const tableRowClassName = ({ rowIndex }: { rowIndex: number }) => {
  if (rowIndex % 2 === 0) {
    return 'even-row'
  }
  return 'odd-row'
}

const activeCollapse = ref(['1'])

getAllTasks()
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-row>
        <el-col :span="7">
          <div class="grid-content">
            <div>
              <div class="SwitchModelCSS">
                当前类型：
                <el-text v-model="currentTaskData.taskType" type="success" size="large">
                  {{ currentTaskData.taskType }}
                </el-text>
              </div>
              <div class="SwitchModelCSS">
                当前任务：
                <el-text v-model="currentTaskData.task" type="success" size="large">
                  {{ currentTaskData.task }}
                </el-text>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="3" class="SwitchModelCSS"> 选择其他类型&任务： </el-col>
        <el-col :span="4">
          <div class="m-4">
            <el-cascader
              v-model="selectedTaskOptions"
              :options="taskOptions"
              :props="props"
              @change="handleTaskChange"
              placeholder="请选择任务"
            />
          </div>
        </el-col>
        <el-col :span="4" class="SwitchModelCSS">
          <div class="grid-content ep-bg-purple">
            <el-button type="success" :icon="Refresh" @click="handleTaskSwitch">切换任务</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-row>
        <el-col :span="7">
          <div class="grid-content">
            <div>
              <div class="SwitchModelCSS">
                当前工作流：
                <el-text v-model="currentFlowData.flow" type="success" size="large">
                  {{ currentFlowData.flow }}
                </el-text>
              </div>
              <div class="SwitchModelCSS">
                当前版本：
                <el-text v-model="currentFlowData.flow" type="success" size="large">
                  {{ currentFlowData.release }}
                </el-text>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="3" class="SwitchModelCSS"> 选择其他工作流&版本： </el-col>
        <el-col :span="4">
          <div class="m-4">
            <el-cascader
              v-model="selectedFlowOptions"
              :options="flowOptions"
              :props="props"
              @change="handleFlowChange"
              placeholder="请选择模型"
            />
          </div>
        </el-col>
        <el-col :span="4" class="SwitchModelCSS">
          <div class="grid-content ep-bg-purple">
            <el-button type="success" :icon="Refresh" @click="handleFlowSwitch">切换模型</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>
    <el-card v-if="choosen" v-loading="loading" shadow="never" class="search-wrapper">
      <el-row :gutter="20">
        <el-col :span="12" v-for="(options, weightKey) in weightOptions" :key="weightKey">
          <label>{{ weightKey }}:</label>
          <el-select
            v-model="selectedWeightData[weightKey]"
            @change="handleWeightChange(weightKey)"
            placeholder="请选择权重">
            <el-option
              v-for="option in options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              :disabled="option.disabled">
            </el-option>
          </el-select>
        </el-col>
      </el-row>
      <el-row v-if="Object.keys(paramsData).length > 0" :gutter="20">
        <el-col :span="12" v-for="(paramItem, idx) in paramsData" :key="idx">
          <Argument
            :imageUrl=null
            :argName="paramItem.argName"
            :argType="paramItem.argType"
            :argValue="handledParamData[paramItem.argName]"
            :argConfig="paramItem.argConfig"
            @argChange="handleParamChange"
          />
        </el-col>
      </el-row>
    </el-card>
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-button type="primary" @click="handleLoadModel">装载模型</el-button>
    </el-card>
    <el-card v-if="loaded" v-loading="loading" shadow="never" class="search-wrapper">
      <el-row :gutter="20">
        <el-col :span="12" v-for="(hyperItem, idx) in hypersData" :key="idx">
          <Argument
            :imageUrl="originImageUrl"
            :argName="hyperItem.argName"
            :argType="hyperItem.argType"
            :argValue="handledHyperData[hyperItem.argName]"
            :argConfig="hyperItem.argConfig"
            @argChange="handleHyperChange"
          />
        </el-col>
      </el-row>
    </el-card>

    <el-card v-loading="predicting" shadow="never" class="search-wrapper">
      <el-button type="primary" @click="handleModelPredict">开始推理</el-button>
      <el-button type="primary" @click="resetResult">结果清除</el-button>
      <el-row :gutter="20">
        <el-col :span="10">
          <div class="grid-content ep-bg-purple">
            <el-image
              v-if="inferImageData.resultBase64.length>0"
              :src="inferImageData.resultImageUrl[0]"
              :fit="'scale-down'"
              :preview-src-list="inferImageData.resultImageUrl"
            />
            <div v-else class="image-placeholder">检测结果图���</div>
          </div>
        </el-col>
        <el-col :span="10">
          <div v-if="inferImageData.inferResult && inferImageData.inferResult.length > 0"
            class="grid-content ep-bg-purple">
            <el-collapse v-model="activeCollapse">
              <el-collapse-item title="检测结果" name="1">
                <el-table
                  :data="inferImageData.inferResult"
                  :row-class-name="tableRowClassName"
                  style="width: 100%"
                  :default-expand-all="false">
                  <el-table-column type="expand">
                    <template #default="props">
                      <el-form label-position="left" inline class="demo-table-expand">
                        <el-form-item label="裁剪对象" v-if="inferImageData.inferCroppers.length>0
                                                            && inferImageData.inferCroppers[props.$index]">
                          <el-image
                            v-if="inferImageData.inferCroppers[props.$index]"
                            :src="inferImageData.inferCroppers[props.$index]"
                            :fit="'scale-down'"
                            :preview-src-list="[inferImageData.inferCroppers[props.$index]]"
                          />
                        </el-form-item>
                        <el-form-item label="锚点集">
                          <span>{{ props.row.points }}</span>
                        </el-form-item>
                        <el-form-item label="分组">
                          <span>{{ props.row.group_id }}</span>
                        </el-form-item>
                        <el-form-item label="描述">
                          <span>{{ props.row.description }}</span>
                        </el-form-item>
                      </el-form>
                    </template>
                  </el-table-column>
                  <el-table-column prop="label" label="检测类别" />
                  <el-table-column prop="score" label="置信度">
                    <template #default="scope">
                      {{ Number(scope.row.score).toFixed(4) }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>
          <div v-else class="image-placeholder">暂无结果</div>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="24" class="infer-duration-container">
          <div class="grid-content ep-bg-purple">
            <el-input
              type="textarea"
              v-if="inferImageData.inferDescription"
              :value="inferImageData.inferDescription"
              :rows="10"
              disabled
              class="no-margin-input"
            />
            <div v-else class="image-placeholder">暂无描述</div>
          </div>
        </el-col>
          <el-col :span="24" class="infer-duration-container">
          <el-card v-if="inferImageData.inferPeriod" class="infer-duration-card">
            <div slot="header">
              <span>推理时长</span>
            </div>
            <p>{{ inferImageData.inferPeriod }} 秒</p>
          </el-card>
          <div v-else class="image-placeholder">推理时长信息不可用</div>
        </el-col>
      </el-row>
    </el-card>
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <div ref="chartRef" style="width: 100%; height: 400px;"></div>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.el-carousel .el-carousel-item {
  display: flex;
  justify-content: center;  /* 水平居中 */
  align-items: center;      /* 垂直居中 */
  height: auto;             /* 让容器的高度根据图像自动调整 */
}
.el-image {
  width: auto;              /* 保持图像的原始宽度 */
  height: auto;             /* 保持图像的原始高度 */
}
.image-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 300px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  font-size: 15px;
}
.el-row {
  margin-bottom: 20px;
}
.el-row:last-child {
  margin-bottom: 0;
}
.el-col {
  border-radius: 4px;
}
.grid-content {
  border-radius: 4px;
  min-height: 36px;
}
.SwitchModelCSS {
  display: flex;
  font-size: 15px;
  font-weight: 500;
  padding: 5px;
  justify-content: flex-start;
  align-items: center;
}
.search-wrapper {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding-bottom: 15px;
  }
}
.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.table-wrapper {
  margin-bottom: 20px;
}
.pager-wrapper {
  display: flex;
  justify-content: flex-end;
}
.demo-table-expand {
  font-size: 0;

  .el-form-item {
    margin-right: 0;
    margin-bottom: 0;
    width: 100%;

    &__label {
      width: 90px;
      color: #99a9bf;
    }

    &__content {
      width: calc(100% - 90px);
    }
  }
}

.even-row {
  background: #fafafa;
}

.odd-row {
  background: #ffffff;
}

:deep(.el-table__expanded-cell) {
  padding: 20px !important;
}

:deep(.el-table__expand-icon) {
  &:hover {
    .el-icon {
      color: var(--el-color-primary);
    }
  }
}

:deep(.el-collapse) {
  border-top: none;
  border-bottom: none;
}

:deep(.el-collapse-item__header) {
  font-size: 16px;
  font-weight: bold;
  color: var(--el-color-primary);
}

:deep(.el-collapse-item__content) {
  padding-bottom: 0;
}
</style>
