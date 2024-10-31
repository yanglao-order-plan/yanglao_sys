<script lang="ts" setup>
import { computed, reactive, ref } from "vue"
import { type IFlowData, IHyperData } from "@/api/infer_local/types/infer_local"
import { Refresh } from "@element-plus/icons-vue"
import { getAllFlowsApi, getCurrentFlowApi, getCurrentHyperApi, switchFlowApi, switchHyperApi, predictModelApi, loadModelApi} from "@/api/infer_local"
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
const flowsData = ref<IFlowData[]>([])
const hypersData = ref<IHyperData[]>([])
// 结构容器
const selectedFlowOptions = ref([])
const selectedWeightOptions = ref({})
const flowOptions = ref<{ value: string; label: string; children: { value: string; label: string }[] }[]>([])
const hyperModules = ref<{ [key: string]: any }>({})
// 当前选择模型数据
const currentFlowData = reactive({
  taskType: "",
  task: "",
  flow: "",
  release: "",
})
const selectedFlowData = reactive({
  taskType: "",
  task: "",
  flow: "",
  release: "",
})
// 动态参数设置与存储
// 定义当前权重数据和已选择的权重数据，只包含一层字典结构
const currentHyperData = reactive<{ [key: string]: any }>({});
const handledHyperData = reactive<{ [key: string]: any }>({});
// 清空方法
const clearSelectedFlow = () => {
  selectedFlowData.taskType = "";
  selectedFlowData.task = "";
  selectedFlowData.release = "";
  selectedFlowData.flow = "";
  selectedFlowData.release = "";
};
const clearHandledHyper = () => {
  for (const key in handledHyperData) {
    delete handledHyperData[key];
  }
  hypersData.value.length = 0
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
const getAllFlows = () => {
  loading.value = true
  getAllFlowsApi()
    .then((res: any) => {
      flowsData.value = res.data
      flowOptions.value = generateFlowCascaderOptions(res.data)
    })
    .catch(() => {
      flowsData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}
const getCurrentFlow = () => {
  getCurrentFlowApi().then((res) => {
    currentFlowData.taskType = res.data.taskTypeName
    currentFlowData.task= res.data.taskName
    currentFlowData.flow = res.data.flowName
    currentFlowData.release = res.data.releaseName
  })
}
const getCurrentHyper = () => {
  getCurrentHyperApi().then((res) => {
    const apiDataArray = res.data;
    apiDataArray.forEach((item) => {
      currentHyperData[item.hyperName] = item.hyperValue;
    });
  }).catch((error) => {
    console.error("Error fetching weight data:", error);
  });
};
// 生成下拉菜单的选项
const generateFlowCascaderOptions = (list: IFlowData[]) => {
  const options: {
    value: string;
    label: string;
    children: {
      value: string;
      label: string;
      children: {
        value: string;
        label: string;
        children: { value: string; label: string }[];
      }[];
    }[];
  }[] = [];

  const map: {
    [key: string]: {
      value: string;
      label: string;
      children: {
        value: string;
        label: string;
        children: {
          value: string;
          label: string;
          children: { value: string; label: string }[];
        }[];
      }[];
    };
  } = {};

  list.forEach((item) => {
    const taskType = item.taskTypeName;
    const task = item.taskName;
    const flowName = item.flowName;
    const releaseName = item.releaseName;
    const releaseShowName = item.releaseShowName;

    if (!map[taskType]) {
      map[taskType] = {
        value: taskType,
        label: taskType,
        children: []
      };
      options.push(map[taskType]);
    }

    let taskObj = map[taskType].children.find((t) => t.value === task);
    if (!taskObj) {
      taskObj = {
        value: task,
        label: task,
        children: []
      };
      map[taskType].children.push(taskObj);
    }

    let flowObj = taskObj.children.find((f) => f.value === flowName);
    if (!flowObj) {
      flowObj = {
        value: flowName,
        label: flowName,
        children: []
      };
      taskObj.children.push(flowObj);
    }

    flowObj.children.push({
      value: releaseName,
      label: releaseShowName
    });
  });

  return options;
};

const generateHyperModules = (list: IHyperData[]) => {
  const modulesMap: { [key: string]: { value: string; label: string; disabled: boolean }[] } = {};
  list.forEach((item) => {
    // 如果该 weightKey 还没有在 optionsMap 中，创建一个新的数组
    if (!modulesMap[item.hyperName]) {
      modulesMap[item.hyperName] = item.hyperDefault;
    }
  });
  return modulesMap; // 返回每个 key 对应的 options 数组
};
// 下拉菜单的选择事件
const handleFlowChange = (selectedOptions: string[]) => {
  if (selectedOptions.length !== 4) return // 如果选中的项数不为2，则返回
  selectedFlowData.taskType = selectedOptions[0]
  selectedFlowData.task = selectedOptions[1]
  selectedFlowData.flow = selectedOptions[2]
  selectedFlowData.release = selectedOptions[3]
  const message = `已选择任务类型：${selectedOptions[0]} 任务：${selectedOptions[1]} 工作流：${selectedOptions[2]} 版本：${selectedOptions[3]}`
  ElMessage({
    message: message,
    type: "success"
  })
}
const handleHyperChange = (hyperName: string |number) => {
  const hyperValue = handledHyperData[hyperName]
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
const handleFlowSwitch = () => {
  if (
    selectedFlowData.flow === currentFlowData.flow &&
    selectedFlowData.release === currentFlowData.release &&
    selectedFlowData.taskType === currentFlowData.taskType &&
    selectedFlowData.task === currentFlowData.task
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
    switchTaskTypeName: selectedFlowData.taskType,
    switchTaskName: selectedFlowData.task,
    switchFlowName: selectedFlowData.flow,
    switchReleaseName: selectedFlowData.release,
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
const handleHyperSwitch = (hyperName: string | number) => {
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
  })
  .catch(() => {
      hypersData.value = []
  })
  .finally(() => {
    loaded.value = false
    loading.value = false
    choosen.value = true
  })
}
const handleLoadModel = () => {
  loadModelApi().then((res) => {
    if (res.data && res.data.length > 0) {
        // 如果 res.data 存在且长度大于 0
        hypersData.value = res.data;
        hyperModules.value = generateHyperModules(res.data);
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
getAllFlows()
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
                <el-text v-model="currentFlowData.taskType" type="success" size="large">
                  {{ currentFlowData.taskType }}
                </el-text>
              </div>
              <div class="SwitchModelCSS">
                当前任务：
                <el-text v-model="currentFlowData.task" type="success" size="large">
                  {{ currentFlowData.task }}
                </el-text>
              </div>
              <div class="SwitchModelCSS">
                当前工作流：
                <el-text v-model="currentFlowData.flow" type="success" size="large">
                  {{ currentFlowData.flow }}
                </el-text>
              </div>
              <div class="SwitchModelCSS">
                当前版本：
                <el-text v-model="currentFlowData.release" type="success" size="large">
                  {{ currentFlowData.release }}
                </el-text>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="3" class="SwitchModelCSS"> 选择其他模式： </el-col>
        <el-col :span="4">
          <div class="m-4">
            <el-cascader
              v-model="selectedFlowOptions"
              :options="flowOptions"
              :props="props"
              @change="handleFlowChange"
              placeholder="请选择模式"
            />
          </div>
        </el-col>
        <el-col :span="4" class="SwitchModelCSS">
          <div class="grid-content ep-bg-purple">
            <el-button type="success" :icon="Refresh" @click="handleFlowSwitch">切换模式</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-button type="primary" @click="handleLoadModel">装载模型</el-button>
    </el-card>
    <!-- 区域2：loaded为true时展示 -->
    <el-card v-if="loaded" v-loading="loading" shadow="never" class="search-wrapper">
      <el-row :gutter="20">
        <el-col :span="12" v-for="(hyperValue, hyperKey) in hyperModules" :key="hyperKey">
          <label>{{ hyperKey }}:</label>
          <el-input 
          v-model="handledHyperData[hyperKey]" 
          placeholder="请输入" 
          :value=hyperValue
          @change="handleHyperChange(hyperKey)" />
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
              :fit="'scaleDown'"
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
              :fit="'scaleDown'"
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
          <el-card v-if="inferImageData.period" class="infer-duration-card">
            <div slot="header">
              <span>推理时长</span>
            </div>
            <p>{{ inferImageData.inferDuration }} 秒</p>
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
