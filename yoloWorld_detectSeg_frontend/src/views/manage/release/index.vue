<script lang="ts" setup>
import { reactive, ref, watch, computed} from "vue"
import { 
  createReleaseDataApi, deleteReleaseDataApi, updateReleaseDataApi, getReleaseDataApi, getFlowDataApi,
  getModelDataApi, getArugmentDataApi,deleteModelDataApi, deleteArgumentDataApi, createModelDataApi,
  updateModelDataApi, updateArgumentDataApi, getWeightDataApi, createArgumentDataApi
} from "@/api/manage"
import { type IGetFlowData } from "@/api/manage/types/flow"
import { type IGetWeightData } from "@/api/manage/types/weight"
import { type IGetReleaseData, IGetModelData, IGetArgumentData } from "@/api/manage/types/release"
import { type FormInstance, type FormRules, ElMessage, ElMessageBox, ElTable } from "element-plus"
import { Search, Refresh, CirclePlus, Delete, Download, RefreshRight } from "@element-plus/icons-vue"
import { usePagination } from "@/hooks/usePagination"
import type { CascaderValue } from 'element-plus'
import JsonEditorVue from 'json-editor-vue3'
import { template } from "xe-utils"
defineOptions({
  name: "ReleaseManage"
})
interface CascaderProps {
  expandTrigger?: "click" | "hover"
}
const props: CascaderProps = {
  expandTrigger: "hover" as const
}
const loading = ref<boolean>(false)
const loadingModel = ref<boolean>(false)
const loadingArgument = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const multipleTableRef = ref<InstanceType<typeof ElTable>>()
const multipleModelTableRef = ref<InstanceType<typeof ElTable>>()
const multipleArgumentTableRef = ref<InstanceType<typeof ElTable>>()
//#region 增
const dialogVisible = ref<boolean>(false)
const dialogModelVisible = ref<boolean>(false)
const dialogArgumentVisible = ref<boolean>(false)
const dialogDefaultVisible = ref<boolean>(false)
const editDefault = ref<boolean>(false)
const editConfig = ref<boolean>(false)
const dialogConfigVisible = ref<boolean>(false)
const formArgumentRef = ref<FormInstance | null>(null)
const formModelRef = ref<FormInstance | null>(null)
const formRef = ref<FormInstance | null>(null)
const activeName = ref('')
const selectedFlowOptions = ref<number[]>([])
const formData = reactive({
  name: "",
  showName: "",
  models: [],
  arguments: [],
  flowId: 0,
})
const formModelData = reactive({
  name: "", 
  weightId: 0,
  releaseId: 0
})
const formWeightId = computed(() => {
  return formModelData.weightId === 0 ? '' : formModelData.weightId;
});
const currentDefault = ref()
const currentConfig = ref()
const formArgumentData = reactive({
  name: "",
  type: "",
  default: JSON,
  config: JSON,
  dynamic: 0,
  releaseId: 0,
})
const formRules: FormRules = reactive({
  name: [{ required: true, trigger: "blur", message: "请输入版本名称" }],
  showName: [{ required: true, trigger: "blur", message: "请输入版本显示名称" }],
  flowId: [{ required: true, trigger: "blur", message: "请选择工作流" }],
})
const formModelRules: FormRules = reactive({
  name: [{ required: true, trigger: "blur", message: "请输入模型名称" }],
  weightId: [{ required: true, trigger: "blur", message: "请选择权重" }],
})
const formArgumentRules: FormRules = reactive({
  name: [{ required: true, trigger: "blur", message: "请输入参数名称" }],
  type: [{ required: true, trigger: "blur", message: "请输入参数类型名称" }],
  default: [{ required: false, trigger: "blur", message: "请输入参数初始值" }],
  config: [{ required: false, trigger: "blur", message: "请设置参数配置" }],
  dynamic: [{ required: true, trigger: "blur", message: "请设置参数动态性" }],
})
const handleShow = (rowId: number, which: number, where: number) => {
  let temper;
  let edit = false;
  if (where === 0){
    temper = argumentData.value[currentShowId.value][rowId]
    edit=false
  } else if (where === 1) {
    temper = formArgumentData
    edit=true
  }
  if (which === 0){
    currentDefault.value = temper?.default
    editDefault.value = edit
    dialogDefaultVisible.value=true
  } else if (which === 1){
    currentConfig.value = temper?.config
    editConfig.value = edit
    dialogConfigVisible.value=true
  }
}
const handleCreate = () => {
  formRef.value?.validate((valid: boolean) => {
    if (valid) {
      if (currentUpdateId.value === undefined) {
        createReleaseDataApi({
          name: formData.name,
          showName: formData.showName,
          models: formData.models,
          arguments: formData.arguments,
          flowId: formData.flowId,
        }).then((res) => {
          if (res.code === 0) {
            ElMessage.success("新增成功")
            dialogVisible.value = false
            getTableData()
          } else {
            ElMessage.error(res.message)
          }
        })
      } else {
        updateReleaseDataApi({
          id: currentUpdateId.value,
          name: formData.name,
          showName: formData.showName,
          models: formData.models,
          arguments: formData.arguments,
          flowId: formData.flowId,
        }).then(() => {
          ElMessage.success("修改成功")
          dialogVisible.value = false
          getTableData()
        })
      }
    }
  })
}
const handleModelCreate = () => {
  formModelRef.value?.validate((valid: boolean) => {
    if (valid) {
      if (currentModelUpdateId.value === undefined) {
        createModelDataApi({
          name: formModelData.name,
          weightId: formModelData.weightId,
          releaseId: formModelData.releaseId,
        }).then((res) => {
          if (res.code === 0) {
            ElMessage.success("新增成功")
            dialogModelVisible.value = false
            getModelData(formModelData.releaseId)
          } else {
            ElMessage.error(res.message)
          }
        })
      } else {
        updateModelDataApi({ 
          id: currentModelUpdateId.value,
          name: formModelData.name,
          weight: formModelData.name,  // 不算
          weightId: formModelData.weightId,
        }).then(() => {
          ElMessage.success("修改成功")
          dialogModelVisible.value = false
          getModelData(formModelData.releaseId)
        })
      }
    }
  })
}
const handleArgumentCreate = () => {
  formArgumentRef.value?.validate((valid: boolean) => {
    if (valid) {
      if (currentArgumentUpdateId.value === undefined) {
        console.log(formArgumentData.default)
        console.log(formArgumentData.config)
        createArgumentDataApi({
          name: formArgumentData.name,
          type: formArgumentData.type,
          default: formArgumentData.default,
          config: formArgumentData.config,
          dynamic: formArgumentData.dynamic,
          releaseId: formModelData.releaseId,
        }).then((res) => {
          if (res.code === 0) {
            ElMessage.success("新增成功")
            dialogArgumentVisible.value = false
            getArgumentData(formArgumentData.releaseId)
          } else {
            console.log(1000)
            ElMessage.error(res.message)
          }
        })
      } else {
        updateArgumentDataApi({  //更新不考虑迁移到其他版本下
          id: currentArgumentUpdateId.value,
          name: formModelData.name,
          type: formArgumentData.type,
          default: formArgumentData.default,
          config: formArgumentData.config,
          dynamic: formArgumentData.dynamic,
        }).then(() => {
          ElMessage.success("修改成功")
          dialogArgumentVisible.value = false
          getModelData(formModelData.releaseId)
        })
      }
    }
  })
}
const resetForm = () => {
  currentUpdateId.value = undefined
  formData.name = ""
  formData.showName = "",
  formData.models = [],
  formData.arguments = [],
  formData.flowId = 0
}
const resetModelForm = () => {
  currentModelUpdateId.value = undefined
  formModelData.name = ""
  formModelData.releaseId = 0,
  formModelData.weightId = 0
}
const resetArgumentForm = () => {
  currentArgumentUpdateId.value = undefined
  formArgumentData.name = ""
  formArgumentData.releaseId = 0,
  formArgumentData.default = JSON
  formArgumentData.config = JSON
}
const resetEditForm = (which: number) => {
  if (which === 0) {
    if (editDefault) formArgumentData.default = currentDefault.value
  } else if (which === 1) {
    if (editConfig) formArgumentData.config = currentConfig.value
  }
}
//#region 删
const handleDelete = (row: IGetFlowData) => {
  ElMessageBox.confirm(`正在删除版本：${row.task}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteReleaseDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getTableData()
    })
  })
}
const handleModelDelete = (row: IGetModelData) => {
  ElMessageBox.confirm(`正在删除模型：${row.name}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteModelDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getModelData(formModelData.releaseId)
    })
  })
}
const handleArgumentDelete = (row: IGetArgumentData) => {
  ElMessageBox.confirm(`正在删除参数：${row.name}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteArgumentDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getArgumentData(formArgumentData.releaseId)
    })
  })
}
//#endregion

// 批量删除
const handleModelBatchDelete = () => {
  ElMessageBox.confirm("确认删除选中的模型？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    const selectionRows = multipleModelTableRef.value!.getSelectionRows()
    if (selectionRows.length === 0) {
      ElMessage.warning("请先选择要删除的模型")
      return
    } else {
      selectionRows.forEach((row: any) => {
        deleteModelDataApi(row.id).then(() => {
          getModelData(formModelData.releaseId)
        })
      })
      ElMessage.success("删除成功")
      handleModelRefresh()
    }
  })
}
const handleArgumentBatchDelete = () => {
  ElMessageBox.confirm("确认删除选中的参数？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    const selectionRows = multipleArgumentTableRef.value!.getSelectionRows()
    if (selectionRows.length === 0) {
      ElMessage.warning("请先选择要删除的参数")
      return
    } else {
      selectionRows.forEach((row: any) => {
        deleteArgumentDataApi(row.id).then(() => {
          getArgumentData(formArgumentData.releaseId)
        })
      })
      ElMessage.success("删除成功")
      handleArgumentRefresh()
    }
  })
}
const handleBatchDelete = () => {
  ElMessageBox.confirm("确认删除选中的版本？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    const selectionRows = multipleTableRef.value!.getSelectionRows()
    if (selectionRows.length === 0) {
      ElMessage.warning("请先选择要删除的版本")
      return
    } else {
      selectionRows.forEach((row: any) => {
        deleteReleaseDataApi(row.id).then(() => {
          getTableData()
        })
      })
      ElMessage.success("删除成功")
      handleRefresh()
    }
  })
}
//#region 改
const currentUpdateId = ref<undefined | number>(undefined)
const currentShowId = ref(0)
const currentModelUpdateId = ref<undefined | number>(undefined)
const currentArgumentUpdateId = ref<undefined | number>(undefined)
const handleUpdate = (row: IGetReleaseData) => {
  currentUpdateId.value = row.id
  formData.name = row.flow
  formData.flowId = row.taskId
  selectedFlowOptions.value.length = 0
  selectedFlowOptions.value.push(row.typeId, row.taskId, row.flowId)
  dialogVisible.value = true
}
const handleModelUpdate = (row: IGetModelData, releaseId: number) => {
  currentModelUpdateId.value = row.id
  formModelData.name = row.name
  formModelData.weightId = row.weightId
  formModelData.releaseId = releaseId
  dialogModelVisible.value = true
}
const handleArgumentUpdate = (row: IGetArgumentData, releaseId: number) => {
  currentArgumentUpdateId.value = row.id
  formArgumentData.name = row.name
  formArgumentData.type = row.type
  formArgumentData.default = row.default
  formArgumentData.config = row.config
  formArgumentData.dynamic = row.dynamic
  formArgumentData.releaseId = releaseId
  dialogArgumentVisible.value = true
}
//#region 查
const tableData = ref<IGetReleaseData[]>([])
const modelData = ref<{[releaseId: number]: IGetModelData[]}>({})
const weightData = ref<IGetWeightData[]>([]) // 添加明确的类型声明
const argumentData = ref<{[releaseId: number]: IGetArgumentData[]}>({})
const flowData = ref<IGetFlowData[]>([]) // 添加明确的类型声明
const flowOptions = ref<{ value: number; label: string; children: { value: number; label: string; children: { value: number; label: string}[] }[] }[]>([])
const currentSearchData = reactive({
  releaseShow: "",
  release: "",
  flow: "",
  task: "",
  taskType: ""
})
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  releaseShow: "",
  release: "",
  flow: "",
  task: "",
  taskType: ""
})
const generateFlowCascaderOptions = () => {
  const options: {
    value: number;
    label: string;
    children: {
      value: number;
      label: string;
      children: {
        value: number;
        label: string;
      }[];
    }[];
  }[] = [];

  const map: {
    [key: string]: {
      value: number;
      label: string;
      children: {
        value: number;
        label: string;
        children: {
          value: number;
          label: string;
        }[];
      }[];
    };
  } = {};

  flowData.value.forEach((item: any) => {
    const {id, flow, task, taskId, taskType, typeId} = item
    if (!map[taskType]) {
      map[taskType] = {
        value: typeId,
        label: taskType,
        children: []
      };
      options.push(map[taskType]);
    }

    let taskObj = map[taskType].children.find((t) => t.value === task);
    if (!taskObj) {
      taskObj = {
        value: taskId,
        label: task,
        children: []
      };
      map[taskType].children.push(taskObj);
    }

    let flowObj = taskObj.children.find((f) => f.value === flow);
    if (!flowObj) {
      flowObj = {
        value: id,
        label: flow,
      };
      taskObj.children.push(flowObj);
    }
  });

  return options;
};

const handleFlowChange = (selectedOptions: CascaderValue) => {
  if (!Array.isArray(selectedOptions) || selectedOptions.length !== 3) return
  formData.flowId = selectedOptions[2] as number
}

const getTableData = () => {
  loading.value = true
  getReleaseDataApi({
    currentPage: paginationData.currentPage,
    size: paginationData.pageSize,
    flow: currentSearchData.flow || undefined,
    task: currentSearchData.task || undefined,
    taskType: currentSearchData.taskType || undefined,
  })
    .then((res) => {
      paginationData.total = res.data.total
      tableData.value = res.data.list
    })
    .catch(() => {
      tableData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}
const getModelData = (releaseId: number) => {
  loadingModel.value = true
  getModelDataApi({
    releaseId: releaseId
  })
    .then((res) => {
      modelData.value[releaseId] = res.data.list
    })
    .catch(() => {
      modelData.value = []
    })
    .finally(() => {
      loadingModel.value = false
    })
}
const getArgumentData = (releaseId: number) => {
  loadingArgument.value = true
  getArugmentDataApi({
    releaseId: releaseId
  })
    .then((res) => {
      argumentData.value[releaseId] = res.data.list
    })
    .catch(() => {
      argumentData.value = []
    })
    .finally(() => {
      loadingArgument.value = false
    })
}
const handleExpandChange = (row: IGetFlowData) => {
  currentShowId.value = row.id
  getModelData(row.id)
  getArgumentData(row.id)
  formModelData.releaseId = row.id
  formArgumentData.releaseId = row.id
}
const handleSearch = () => {
  if (
    currentSearchData.releaseShow !== searchData.releaseShow ||
    currentSearchData.release !== searchData.release ||
    currentSearchData.flow !== searchData.flow ||
    currentSearchData.task !== searchData.task ||
    currentSearchData.taskType !== searchData.taskType
  ){
    currentSearchData.releaseShow = searchData.releaseShow
    currentSearchData.release = searchData.release
    currentSearchData.flow = searchData.flow
    currentSearchData.task = searchData.task
    currentSearchData.taskType = searchData.taskType
  }
  if (paginationData.currentPage === 1) {
    getTableData()
  }
  paginationData.currentPage = 1
}
const resetSearch = () => {
  searchFormRef.value?.resetFields()
  if (paginationData.currentPage === 1) {
    getTableData()
  }
  paginationData.currentPage = 1
}
const getFlowData = () => {
  loading.value = true
  getFlowDataApi({
    currentPage: 1,
    size: -1,
    task: undefined,
    taskType: undefined
  })
    .then((res) => {
      flowData.value = res.data.list
      flowOptions.value = generateFlowCascaderOptions()
    })
    .catch(() => {
      tableData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}
const getWeightData = () => {
  loading.value = true
  getWeightDataApi({
    currentPage: 1,
    size: -1,
  })
    .then((res) => {
      weightData.value = res.data.list
    })
    .catch(() => {
      tableData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}
const handleRefresh = () => {
  getTableData()
  getFlowData()
  getWeightData()
}
const handleModelRefresh = () => {
  getModelData(formModelData.releaseId)
}
const handleArgumentRefresh = () => {
  getArgumentData(formArgumentData.releaseId)
}
//#endregion
getFlowData()
getWeightData()
/** 监听分页参数的变化 */
watch([() => paginationData.currentPage, () => paginationData.pageSize], getTableData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="taskType" label="任务类型名称">
          <el-input v-model="searchData.taskType" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="task" label="任务名称">
          <el-input v-model="searchData.task" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="task" label="工作流名称">
          <el-input v-model="searchData.flow" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="task" label="版本名称">
          <el-input v-model="searchData.release" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="task" label="展示名称">
          <el-input v-model="searchData.releaseShow" placeholder="请输入" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card v-loading="loading" shadow="never">
      <div class="toolbar-wrapper">
        <div>
          <el-button type="primary" :icon="CirclePlus" @click="dialogVisible = true">新增版本</el-button>
          <el-button type="danger" :icon="Delete" @click="handleBatchDelete">批量删除</el-button>
        </div>
        <div>
          <el-tooltip content="下载">
            <el-button type="primary" :icon="Download" circle />
          </el-tooltip>
          <el-tooltip content="刷新表格">
            <el-button type="primary" :icon="RefreshRight" circle @click="handleRefresh" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table ref="multipleTableRef" :data="tableData" @expand-change="handleExpandChange">
          <el-table-column type="expand">
            <template class="demo-table-expand" #default="slotProps">
              <el-tabs type="border-card" v-model="activeName" class="demo-tabs">
                <el-tab-pane label="模型配置" name='0'>
                  <el-card v-loading="loadingModel" shadow="never">
                    <div class="toolbar-wrapper">
                      <div>
                        <el-button type="primary" :icon="CirclePlus" @click="dialogModelVisible = true">新增模型</el-button>
                        <el-button type="danger" :icon="Delete" @click="handleModelBatchDelete">批量删除</el-button>
                      </div>
                      <div>
                        <el-tooltip content="下载">
                          <el-button type="primary" :icon="Download" circle />
                        </el-tooltip>
                        <el-tooltip content="刷新表格">
                          <el-button type="primary" :icon="RefreshRight" circle @click="handleModelRefresh" />
                        </el-tooltip>
                      </div>
                    </div>
                    <div class="table-wrapper">
                      <el-table ref="multipleModelTableRef" :data="modelData[slotProps.row.id]">
                        <el-table-column prop="name" label="模型名称" align="center" /> 
                        <el-table-column prop="weight" label="权重名称" align="center" />
                        <el-table-column fixed="right" label="操作" width="150" align="center">
                          <template #default="scope">
                            <el-button type="primary" text bg size="small" @click="handleModelUpdate(scope.row, slotProps.row.id)">修改</el-button>
                            <el-button type="danger" text bg size="small" @click="handleModelDelete(scope.row)">删除</el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                    </div>
                  </el-card>
                </el-tab-pane>
                <el-tab-pane label="参数配置" name='1'>
                  <el-card v-loading="loadingArgument" shadow="never">
                    <div class="toolbar-wrapper">
                      <div>
                        <el-button type="primary" :icon="CirclePlus" @click="dialogArgumentVisible = true">新增参数</el-button>
                        <el-button type="danger" :icon="Delete" @click="handleArgumentBatchDelete">批量删除</el-button>
                      </div>
                      <div>
                        <el-tooltip content="下载">
                          <el-button type="primary" :icon="Download" circle />
                        </el-tooltip>
                        <el-tooltip content="刷新表格">
                          <el-button type="primary" :icon="RefreshRight" circle @click="handleArgumentRefresh" />
                        </el-tooltip>
                      </div>
                    </div>
                    <div class="table-wrapper">
                      <el-table ref="multipleArgumentTableRef" :data="argumentData[slotProps.row.id]">
                        <el-table-column prop="name" label="参数名称" align="center" /> 
                        <el-table-column prop="type" label="参数类型" align="center" />
                        <el-table-column prop="defult" label="参数初始值" align="center">
                          <template #default="scope">
                            <el-button @click="handleShow(scope.$index, 0, 0)"/>
                          </template>
                        </el-table-column>
                        <el-table-column prop="config" label="参数配置" align="center">
                          <template #default="scope">
                            <el-button @click="handleShow(scope.$index, 1, 0)"/>
                          </template>
                        </el-table-column>
                        <el-table-column prop="dynamic" label="动态性" align="center" />
                        <el-table-column fixed="right" label="操作" width="150" align="center">
                          <template #default="scope">
                            <el-button type="primary" text bg size="small" @click="handleArgumentUpdate(scope.row, slotProps.row.id)">修改</el-button>
                            <el-button type="danger" text bg size="small" @click="handleArgumentDelete(scope.row)">删除</el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                    </div>
                  </el-card>
                </el-tab-pane>
              </el-tabs>
            </template>
          </el-table-column>
          <el-table-column type="selection" width="50" align="center" />
          <el-table-column prop="taskType" label="任务类型" align="center" />
          <el-table-column prop="task" label="任务" align="center" />
          <el-table-column prop="flow" label="工作流" align="center" />
          <el-table-column prop="release" label="版本" align="center" />
          <el-table-column prop="releaseShow" label="展示" align="center" />
          <el-table-column fixed="right" label="操作" width="150" align="center">
            <template #default="scope">
              <el-button type="primary" text bg size="small" @click="handleUpdate(scope.row)">修改</el-button>
              <el-button type="danger" text bg size="small" @click="handleDelete(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pager-wrapper">
        <el-pagination
          background
          :layout="paginationData.layout"
          :page-sizes="paginationData.pageSizes"
          :total="paginationData.total"
          :page-size="paginationData.pageSize"
          :currentPage="paginationData.currentPage"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    <!-- 新增/修改release -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentUpdateId === undefined ? '新增版本' : '修改版本'"
      @close="resetForm"
      width="30%"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="flowId" label="工作流">
          <el-cascader
              v-model="selectedFlowOptions"
              :options="flowOptions"
              :props="props"
              @change="handleFlowChange"
              placeholder="请选择工作流"
            />
        </el-form-item>
        <el-form-item prop="name" label="版本名称">
          <el-input v-model="formData.name" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="showName" label="展示名称">
          <el-input v-model="formData.showName" placeholder="请输入" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确认</el-button>
      </template>
    </el-dialog>
    <!-- 新增/修改model-->
    <el-dialog
      v-model="dialogModelVisible"
      :title="currentModelUpdateId === undefined ? '新增模型' : '修改模型'"
      @close="resetModelForm"
      width="30%"
    >
      <el-form ref="formModelRef" :model="formModelData" :rules="formModelRules" label-width="100px" label-position="left">
        <el-form-item prop="name" label="模型名称">
          <el-input v-model="formModelData.name" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="weightId" label="权重对象">
          <el-select v-model="formWeightId" placeholder="请选择权重">
            <el-option
              v-for="weight in weightData"
              :key="weight.id"
              :label="weight.weight"
              :value="weight.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogModelVisible = false">取消</el-button>
        <el-button type="primary" @click="handleModelCreate">确认</el-button>
      </template>
    </el-dialog>
    <!-- 新增/修改argument -->
    <el-dialog
      v-model="dialogArgumentVisible"
      :title="currentArgumentUpdateId === undefined ? '新增参数' : '修改参数'"
      @close="resetArgumentForm"
      width="30%"
    >
      <el-form ref="formArgumentRef" :model="formArgumentData" :rules="formArgumentRules" label-width="100px" label-position="left">
        <el-form-item prop="name" label="名称">
          <el-input v-model="formArgumentData.name" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="type" label="类型">
          <el-input v-model="formArgumentData.type" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="default" label="初始值">
          <el-button @click="handleShow(-1, 0, 1)"/>    
        </el-form-item>
        <el-form-item prop="config" label="配置">
          <el-button @click="handleShow(-1, 1, 1)"/>  
        </el-form-item>
        <el-form-item prop="dynamic" label="动态性">
          <el-checkbox v-model="formArgumentData.dynamic" placeholder="请选择" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogArgumentVisible = false">取消</el-button>
        <el-button type="primary" @click="handleArgumentCreate">确认</el-button>
      </template>
    </el-dialog>
    <el-dialog 
    v-model="dialogDefaultVisible" title="参数默认值"
    @close="resetEditForm(0)">
      <div>
        <JsonEditorVue v-if="editDefault" v-model="currentDefault"
        :modeList="['code']" :currentMode="'code'" />
        <JsonEditorVue v-else v-model="currentDefault"
        :modeList="['view']" :currentMode="'view'" />
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogDefaultVisible = false">关闭</el-button>
      </span>
    </el-dialog>
    <el-dialog 
    v-model="dialogConfigVisible" title="参数配置"
    @close="resetEditForm(1)">
      <div>
        <JsonEditorVue v-if="editConfig" v-model="currentConfig"
        :modeList="['code']" :currentMode="'code'"/>
        <JsonEditorVue v-else v-model="currentConfig"
        :modeList="['view']" :currentMode="'view'"/>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogConfigVisible = false">关闭</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.search-wrapper {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding-bottom: 2px;
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
