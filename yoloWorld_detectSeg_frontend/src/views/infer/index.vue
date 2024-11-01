<script lang="ts" setup>
import { computed, reactive, ref } from "vue"
import { type ITaskData, IFlowData, IWeightData, IArgData, OArgData } from "@/api/infer/types/infer"
import Argument from '@/components/argument/module.vue'
import { Refresh } from "@element-plus/icons-vue"
import { getAllTasksApi, getCurrentTaskApi, getCurrentFlowApi, getCurrentWeightApi, getCurrentParamApi, getCurrentHyperApi,
  switchTaskApi, switchFlowApi, switchWeightApi, switchParamApi, switchHyperApi, predictModelApi, loadModelApi} from "@/api/infer"
import { ElMessage } from "element-plus"
import UploadFile from "@/components/UploadFile/index.vue"
// 将模式与参数的加载分开

defineOptions({
  name: "Infer"
})
// 原始容器
const choosen = ref<boolean>(false)
const loading = ref<boolean>(false)
const loaded = ref<boolean>(false)
const predicting = ref<boolean>(false)
const predicted = ref<boolean>(false)
const tasksData = ref<ITaskData[]>([])
const flowsData = ref<IFlowData[]>([])
const weightsData = ref<IWeightData[]>([])
const paramsData = ref<IArgData[]>([])
const hypersData = ref<IArgData[]>([])
// 结构容器
const selectedTaskOptions = ref([])
const selectedFlowOptions = ref([])
const selectedWeightOptions = ref({})
const taskOptions = ref<{ value: string; label: string; children: { value: string; label: string }[] }[]>([])
const flowOptions = ref<{ value: string; label: string; children: { value: string; label: string }[] }[]>([])
const weightOptions = ref<{ [key: string]: { value: string; label: string; disabled: boolean }[]}>({})
// 当前选择模型数据
const currentTaskData = reactive({
  taskType: "",
  task: "",
})
// 绑定下拉选项数据
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
// 动态参数设置与存储
// 定义当前权重数据和已选择的权重数据，只包含一层字典结构
const currentWeightData = reactive<{ [key: string]: string }>({});
const selectedWeightData = reactive<{ [key: string]: string }>({});
const currentParamData = reactive<{ [key: string]: any }>({});
const handledParamData = reactive<{ [key: string]: any }>({});
const currentHyperData = reactive<{ [key: string]: any }>({});
const handledHyperData = reactive<{ [key: string]: any }>({});
// 清空方法
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
  keys.forEach(key => { // 使用 forEach 遍历数组的值
    if (key === 'flow') clearSelectedFlow();
    else if (key === 'weight') clearSelectedWeight();
    else if (key === 'param') clearHandledParam();
    else if (key === 'hyper') clearHandledHyper();
  });
};

// 检测结果图片
// base64解码
const inferImageData: any = reactive({
  originalBase64: "",
  resultBase64: "",
  originalImageUrl: computed(() => {  // 自动计算url显示原始图片
    if (inferImageData.originalBase64) {
      const blob = dataURItoBlob(inferImageData.originalBase64)
      return URL.createObjectURL(blob)
    } else {
      return ""
    }
  }),
  resultImageUrl: computed(() => {
    if (inferImageData.resultBase64) {  // 同样的，根据base64字符串自动计算
      const blob = dataURItoBlob(inferImageData.resultBase64)
      return URL.createObjectURL(blob)
    } else {
      return ""
    }
  }),
  inferResult: [],
  inferDescription: "",
  inferPeriod: ""
})

// 处理上传文件
const onHandleUpload = (file: any) => {
  // 如果后端的数据没有以 data:image/jpeg;base64 则需要判断加上
  const a = new FileReader()
      a.readAsDataURL(file.raw)
      a.onload = (e) => {
        if (e.target) {
          inferImageData.originalBase64 = e.target.result
        }
      }
}
// 图片base64解码
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
/** 获取当前调用权重 */
const getCurrentTask = () => {
  getCurrentTaskApi().then((res) => {
    currentTaskData.taskType = res.data.taskTypeName
    currentTaskData.task = res.data.taskName
  })
}
// 除了获取当前工作流，还要将配置载入
const getCurrentFlow = () => {
  getCurrentFlowApi().then((res) => {
    currentFlowData.flow = res.data.flowName
    currentFlowData.release = res.data.releaseName
  })
  .finally(() => {
    paramsData.value.forEach((element: any) => {  // 提前装载初始值
      handledParamData[element['argName']] = element['argDefault']
    });
  })
}
// 从 API 获取当前的 weight 数据并赋值
const getCurrentWeight = (weigthKey: string|number) => {
  getCurrentWeightApi({
    currentWeightKey: weigthKey
  }).then((res) => {
    currentWeightData[res.data.weightKey] = res.data.weightName;
    console.log(currentWeightData)
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
// 生成下拉菜单的选项
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
// 定义每个 weightKey 对应的 select 选项
const generateWeightOptions = (list: IWeightData[]) => {
  const optionsMap: { [key: string]: { value: string; label: string; disabled: boolean }[] } = {};
  list.forEach((item) => {
    // 如果该 weightKey 还没有在 optionsMap 中，创建一个新的数组
    if (!optionsMap[item.weightKey]) {
      optionsMap[item.weightKey] = [];
    }
    // 为该 weightKey 添加对应的选项
    optionsMap[item.weightKey].push({
      value: item.weightName,
      label: item.weightName,
      disabled: !item.weightEnable
    });
  });
  return optionsMap; // 返回每个 key 对应的 options 数组
};
// 下拉菜单的选择事件
const handleTaskChange = (selectedOptions: string[]) => {
  if (selectedOptions.length !== 2) return // 如果选中的项数不为2，则返回
  selectedTaskData.taskType = selectedOptions[0]
  selectedTaskData.task = selectedOptions[1]
  const message = `已选择任务类型：${selectedOptions[0]} 任务：${selectedOptions[1]}`
  ElMessage({
    message: message,
    type: "success"
  })
}
const handleFlowChange = (selectedOptions: string[]) => {
  if (selectedOptions.length !== 2) return // 如果选中的项数不为2，则返回
  selectedFlowData.flow = selectedOptions[0]
  selectedFlowData.release = selectedOptions[1]
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
  console.log(hyperName, hyperValue)
  handledHyperData[hyperName] = hyperValue
  handleHyperSwitch(hyperName)
  const message = `已经完成参数${hyperName}: ${hyperValue}`
  ElMessage({
    message: message,
    type: "success"
  })
}
// 下拉菜单的展开方式
interface CascaderProps {
  expandTrigger?: "click" | "hover"
}
const props: CascaderProps = {
  expandTrigger: "hover" as const
}
// 切换模型
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
    paramsData.value.forEach(element => {
      handledParamData[element.argName] = element?.argDefault
    });
  } else if (mode === 'hyper'){
    hypersData.value.forEach(element => {
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
  console.log(weightKey)
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
        // 如果 res.data 存在且长度大于 0
        hypersData.value = res.data;
        console.log(res.data)
        loadDefault('hyper')
      } else {
        // 如果 res.data 为空或长度为 0，执行相应的处理
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
  predictModelApi({'originalBase64': inferImageData.originalBase64}).then((res) => {
    inferImageData.resultBase64 = res.data.resultBase64
    inferImageData.inferResult = res.data.inferResult
    inferImageData.inferPeriod = res.data.inferPeriod
    inferImageData.inferDescription = res.data.inferDescription
    console.log(10000)
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
// getCurrentTask()
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
    <!-- 区域1：choosen为true时展示 -->
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
    <!-- 区域2：loaded为true时展示 -->
    <el-card v-if="loaded" v-loading="loading" shadow="never" class="search-wrapper">
      <el-row :gutter="20">
        <el-col :span="12" v-for="(hyperItem, idx) in hypersData" :key="idx">
          <Argument
            :imageUrl="inferImageData.originalImageUrl"
            :argName="hyperItem.argName"
            :argType="hyperItem.argType"
            :argValue="handledHyperData[hyperItem.argName]"
            :argConfig="hyperItem.argConfig"
            @argChange="handleHyperChange"
          />
        </el-col>
      </el-row>
    </el-card>

    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <UploadFile @handleUpload="onHandleUpload" />
    </el-card>
    <el-card v-loading="predicting" shadow="never" class="search-wrapper">
      <el-button type="primary" @click="handleModelPredict">开始推理</el-button>
      <el-row :gutter="20">
        <el-col :span="10">
          <div class="grid-content ep-bg-purple">
            <el-image
              v-if="inferImageData.originalBase64"
              :src="inferImageData.originalImageUrl"
              :fit="'scale-down'"
              :preview-src-list="[inferImageData.originalImageUrl]"
            />
            <div v-else class="image-placeholder">原始图片</div>
          </div>
        </el-col>
        <el-col :span="10">
          <div class="grid-content ep-bg-purple">
            <el-image
              v-if="inferImageData.resultBase64"
              :src="inferImageData.resultImageUrl"
              :fit="'scale-down'"
              :preview-src-list="[inferImageData.resultImageUrl]"
            />
            <div v-else class="image-placeholder">检测结果图片</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="grid-content ep-bg-purple">
            <el-table
              :data="inferImageData.inferDescription"
              v-if="inferImageData.inferDescription && inferImageData.inferDescription.length > 0"
            >
              <el-table-column prop="className" label="检测类别" />
              <el-table-column prop="confidence" label="置信度" />
            </el-table>
            <div v-else class="image-placeholder">暂无结果</div>
          </div>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <div class="grid-content ep-bg-purple">
          <el-input
            type="textarea"
            v-if="inferImageData.predictDescription"
            :value="inferImageData.predictDescription"
            :rows="10"
            disabled
            class="no-margin-input"
          />
          <div v-else class="image-placeholder">暂无描述</div>
        </div>
          <!-- 推理时长组件 -->
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
  </div>
</template>

<style lang="scss" scoped>
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
</style>
