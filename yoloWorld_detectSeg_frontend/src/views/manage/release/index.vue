<script lang="ts" setup>
import { reactive, ref, watch, computed} from "vue"
import {
  createReleaseDataApi, deleteReleaseDataApi, updateReleaseDataApi, getReleaseDataApi, getFlowDataApi,
  getModelDataApi, getArugmentDataApi,deleteModelDataApi, deleteArgumentDataApi, createModelDataApi,
  updateModelDataApi, updateArgumentDataApi, getWeightDataApi, createArgumentDataApi, deleteArgumentBlurApi
} from "@/api/manage"
import { type IGetFlowData } from "@/api/manage/types/flow"
import { type IGetWeightData } from "@/api/manage/types/weight"
import { type IGetReleaseData, IGetModelData, IGetArgumentData } from "@/api/manage/types/release"
import { type FormInstance, type FormRules, ElMessage, ElMessageBox, ElTable, selectKey } from "element-plus"
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
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const loading = ref<boolean>(false)
const loadingModel = ref<boolean>(false)
const loadingArgument = ref<boolean>(false)
const multipleTableRef = ref<InstanceType<typeof ElTable>>()
const multipleModelTableRef = ref<InstanceType<typeof ElTable>>()
const multipleArgumentTableRef = ref<InstanceType<typeof ElTable>>()
//#region 增
const dialogVisible = ref<boolean>(false)
const dialogModelVisible = ref<boolean>(false)
const dialogArgumentVisible = ref<boolean>(false)
const batchAddArgument = ref<boolean>(false)
const batchDeleteArgument = ref<boolean>(false)
const copyArgument = ref<boolean>(false)
const copyModel = ref<boolean>(false)
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
const formWeightId = computed({
  get() {
    return formModelData.weightId === 0 ? '' : formModelData.weightId;
  },
  set(value) {
    formModelData.weightId = value === '' ? 0 : value;
  }
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
    editDefault.value = edit
    currentDefault.value = temper?.default
    dialogDefaultVisible.value=true
  } else if (which === 1){
    editConfig.value = edit
    currentConfig.value = temper?.config
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
const handleModel = () => {
  if (copyModel.value) handleModelCopy()
  else handleModelCreate()
}
const handleModelCopy = () => {
  ElMessageBox.confirm(`正在拷贝模型：${formModelData.name}，确认拷贝？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    if (currentShowId.value === formModelData.releaseId) {
      ElMessage.error(`拷贝失败，目标版本与当前版本相同：${formArgumentData.name}`)
    }
    createModelDataApi({
      name: formModelData.name,
      weightId: formModelData.weightId,
      releaseId: formModelData.releaseId
    }).then(() => {
      ElMessage.success("拷贝成功")
      if (check_in(formModelData.releaseId)) {
        getModelData(formModelData.releaseId)
      }
      dialogModelVisible.value = false
    })
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

const handleArgument = () => {
  if (batchAddArgument.value) handleBatchCreateArgument()
  else if (batchDeleteArgument.value) handleBatchDeleteArgument()
  else if (copyArgument.value) handleArgumentCopy()
  else handleArgumentCreate()
}
const handleArgumentCreate = () => {
  formArgumentRef.value?.validate((valid: boolean) => {
    if (valid) {
      if (currentArgumentUpdateId.value === undefined) {
        createArgumentDataApi({
          name: formArgumentData.name,
          type: formArgumentData.type,
          default: formArgumentData.default,
          config: formArgumentData.config,
          dynamic: formArgumentData.dynamic,
          releaseId: formArgumentData.releaseId,
        }).then((res) => {
          if (res.code === 0) {
            ElMessage.success("新增成功")
            getArgumentData(formArgumentData.releaseId)
            dialogArgumentVisible.value = false
          } else {
            ElMessage.error(res.message)
          }
        })
      } else {
        updateArgumentDataApi({  //更新不考虑迁移到其他版本下
          id: currentArgumentUpdateId.value,
          name: formArgumentData.name,
          type: formArgumentData.type,
          default: formArgumentData.default,
          config: formArgumentData.config,
          dynamic: formArgumentData.dynamic,
        }).then(() => {
          ElMessage.success("修改成功")
          getArgumentData(formModelData.releaseId)
          dialogArgumentVisible.value = false
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
  formArgumentData.type = ""
  formArgumentData.default = JSON
  formArgumentData.config = JSON
  formArgumentData.dynamic = 0
  formArgumentData.releaseId = 0
  batchAddArgument.value = false
  batchDeleteArgument.value = false
  copyArgument.value = false
}
const resetEditForm = (which: number) => {
  if (which === 0) {  // 编辑初始值
    if (editDefault.value){
      formArgumentData.default = currentDefault.value
      currentDefault.value = null
    } 
  } else if (which === 1) {  // 编辑配置
    if (editConfig.value) {
      formArgumentData.config = currentConfig.value
      currentConfig.value = null
    }
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
const handleModelDelete = (row: IGetModelData, releaseId: number) => {
  ElMessageBox.confirm(`正在删除模型：${row.name}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteModelDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getModelData(releaseId)
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
      getArgumentData(currentShowId.value)
    })
  })
}
const preHandleArgumentCopy = (row: IGetArgumentData) => {
  formArgumentData.name = row.name
  formArgumentData.type = row.type
  formArgumentData.default = row.default
  formArgumentData.config = row.config
  formArgumentData.dynamic = row.dynamic
  formArgumentData.releaseId = currentShowId.value
  dialogArgumentVisible.value = true
  copyArgument.value = true
}
const preHandleModelCopy = (row: IGetModelData) => {
  formModelData.name = row.name
  formModelData.weightId = row.weightId
  formModelData.releaseId = currentShowId.value  // 借用
  dialogModelVisible.value = true
  copyModel.value = true
}
const handleArgumentCopy = () => {
  ElMessageBox.confirm(`正在拷贝参数：${formArgumentData.name}，确认拷贝？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    if (currentShowId.value === formArgumentData.releaseId) {
      ElMessage.error(`拷贝失败，目标版本与当前版本相同：${formArgumentData.name}`)
    }
    createArgumentDataApi({
      name: formArgumentData.name,
      type: formArgumentData.type,
      default: formArgumentData.default,
      config: formArgumentData.config,
      dynamic: formArgumentData.dynamic,
      releaseId: formArgumentData.releaseId
    }).then(() => {
      ElMessage.success("拷贝成功")
      if (check_in(formArgumentData.releaseId)) {
        getArgumentData(formArgumentData.releaseId)
      }
      dialogArgumentVisible.value = false
    })
  })
}
//#endregion
const check_select = () => {
  Object.entries(tableKey.value).forEach(([id, _]) => {
    if(tableKey.value[Number(id)]) return true
  })
  return false
}
const check_in = (rid: number) => {
  tableData.value.forEach((item) => {
    if (item.id === rid) return true
  });
  return false
}
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
      handleModelRefresh(formModelData.releaseId)
    }
  })
}
const handleArgumentBatchDelete = () => {
  ElMessageBox.confirm("确认删除选中的参数？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    if (check_select()) {
      ElMessage.warning("请先选择要删除的参数")
      return
    } else {
      Object.entries(tableKey.value).forEach(([id, _]) => {
        deleteArgumentDataApi(Number(id)).then(() => {
          if (Number(id) in argumentData) getArgumentData(Number(id))
        })
      })
      dialogArgumentVisible.value = false
      ElMessage.success("批量删除成功")
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
const handleBatchCreateArgument = () => {
  ElMessageBox.confirm("确认批量添加参数？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    if (check_select()) {
      ElMessage.warning("请先选择关联的版本")
      return
    } else {
      Object.entries(tableKey.value).forEach(([id, _]) => {
        createArgumentDataApi({
          name: formArgumentData.name,
          type: formArgumentData.type,
          default: formArgumentData.default,
          config: formArgumentData.config,
          dynamic: formArgumentData.dynamic,
          releaseId: Number(id),
        })
        if (Number(id) in argumentData) getArgumentData(Number(id))
      })
      dialogArgumentVisible.value = false
      ElMessage.success("批量添加成功")
    }
  })
}
const handleBatchDeleteArgument = () => {
  ElMessageBox.confirm("确认批量删除参数？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    const selectionRows = multipleTableRef.value!.getSelectionRows()
    if (selectionRows.length === 0) {
      ElMessage.warning("请先选择关联的版本")
      return
    } else {
      Object.entries(tableKey.value).forEach(([id, _]) => {
        deleteArgumentBlurApi({
          argument: formArgumentData.name,
          type: formArgumentData.type,
          dynamic: formArgumentData.dynamic,
          releaseId: Number(id)
        })
        if (Number(id) in argumentData) getArgumentData(Number(id))
      })
      dialogArgumentVisible.value = false
      ElMessage.success("批量删除成功")
    }
  })
}
//#region 改
const expands = ref<string[]>([]);
const currentUpdateId = ref<undefined | number>(undefined)
const currentShowId = ref(0)
const currentModelUpdateId = ref<undefined | number>(undefined)
const currentArgumentUpdateId = ref<undefined | number>(undefined)
const handleUpdate = (row: IGetReleaseData) => {
  currentUpdateId.value = row.id
  formData.name = row.release
  formData.showName = row.releaseName
  formData.flowId = row.flowId
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
const handleArgumentUpdate = (row: IGetArgumentData) => {
  currentArgumentUpdateId.value = row.id
  formArgumentData.name = row.name
  formArgumentData.type = row.type
  formArgumentData.default = row.default
  formArgumentData.config = row.config
  formArgumentData.dynamic = row.dynamic
  formArgumentData.releaseId = currentShowId.value
  dialogArgumentVisible.value = true
}
//#region 查
const isAboveSelected = ref(false); // 全页全选状态
const isAllSelected = ref(false); // 全页全选状态
const tableData = ref<IGetReleaseData[]>([])
const tableKey = ref<{ [key: number]: boolean }>({});
const tableName = ref<{ [key: number]: string }>({});
const modelData = ref<{[releaseId: number]: IGetModelData[]}>({})
const weightData = ref<IGetWeightData[]>([]) // 添加明确的类型声明
const argumentData = ref<{[releaseId: number]: IGetArgumentData[]}>({})
const flowData = ref<IGetFlowData[]>([]) // 添加明确的类型声明
const flowOptions = ref<{ value: number; label: string; children: { value: number; label: string; children: { value: number; label: string; }[] }[]}[]>([])
const currentSearchData = reactive({
  releaseName: "",
  release: "",
  flow: "",
  task: "",
  taskType: ""
})
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  releaseName: "",
  release: "",
  flow: "",
  task: "",
  taskType: ""
})  

const titleText = computed(() => {
  if (batchDeleteArgument.value) return '批量删除参数'
  else if (copyArgument.value) return '拷贝参数'
  return currentArgumentUpdateId.value === undefined ? '新增参数' : '修改参数';
});

const handleToggleSelectAbove = () => {
  if (multipleTableRef.value) {
    if (isAboveSelected.value) {
      tableData.value.forEach((row) => {
        tableKey.value[row.id] = true; // 更新选中状态
      });
    } else {
      tableData.value.forEach((row) => {
        tableKey.value[row.id] = false; // 更新选中状态
      });
    }
  }
};
const handleToggleSelectAll = () => {
  if (multipleTableRef.value) {
    if (isAllSelected.value) {
      { 
        Object.entries(tableKey.value).forEach(([id, _]) => {
          tableKey.value[Number(id)] = true;
        })
        isAboveSelected.value = true
      }
    } else { 
        Object.entries(tableKey.value).forEach(([id, _]) => {
          tableKey.value[Number(id)] = false;
        })
        isAboveSelected.value = false
      }
  }
}
const generateFlowCascaderOptions = () => {
  const options: { value: number; label: string; children: { value: number; label: string; children: { value: number; label: string }[] }[] }[] = [];
  const map: { [key: string]: { value: number; label: string; children: { value: number; label: string; children: { value: number; label: string }[] }[] } } = {};

  flowData.value.forEach((item: any) => {
    const { flow, id, task, taskId, taskType, typeId } = item;

    // 处理 taskType 层级，确保每个 taskType 只有一个唯一项
    if (!map[taskType]) {
      map[taskType] = {
        value: typeId,
        label: taskType,
        children: []
      };
      options.push(map[taskType]);  // 将新的 taskType 加入最终的选项列表
    }

    // 处理 task 层级，确保每个 task 在该 taskType 下只有唯一项
    let taskObj = map[taskType].children.find(t => t.value === taskId);
    if (!taskObj) {
      taskObj = {
        value: taskId,
        label: task,
        children: []  // 新的 task 不包含子项，flow 会是它的子项
      };
      map[taskType].children.push(taskObj);  // 将新的 task 加入该 taskType 的 children
    }

    // 处理 flow 层级，确保每个 task 下的 flow 唯一
    let flowObj = taskObj.children.find(f => f.value === id);
    if (!flowObj) {
      flowObj = {
        value: id,
        label: flow,
      };
      taskObj.children.push(flowObj);  // 将新的 flow 加入该 task 的 children
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
    release: currentSearchData.release,
    releaseName: currentSearchData.releaseName,
    flow: currentSearchData.flow || undefined,
    task: currentSearchData.task || undefined,
    taskType: currentSearchData.taskType || undefined,
  })
    .then((res) => {
      paginationData.total = res.data.total
      tableData.value = res.data.list
      for (const key in res.data.whole) {
        const id = Number(key);
        if (!(id in tableKey.value)) {
          tableKey.value[id] = false;
        }
        if (!(id in tableName.value)) {
          tableName.value[id] = res.data.whole[id];
        }
      }
      tableName.value = res.data.whole
      for (const id in tableKey.value) {
        if (!(id in res.data.whole)) {
          delete tableKey.value[id];
        }
      }
      for (const id in tableName.value) {
        if (!(id in res.data.whole)) {
          delete tableName.value[id];
        }
      }
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
    model: "",
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
    argument: "",
    type: "",
    dynamic: -1,
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
const handleExpandChange = (row: IGetFlowData, expandedRows: Array<number>) => {
  currentShowId.value = row.id
  getModelData(row.id)
  getArgumentData(row.id)
  formModelData.releaseId = row.id
  formArgumentData.releaseId = row.id

  if (expandedRows.length) { 
    //展开
    expands.value = []; //先干掉之前展开的行
    if (row) {
      expands.value.push(String(row.id)); //push新的行 (原理有点类似防抖)
    }
  } else {
    expands.value = []; //折叠 就清空expand-row-keys对应的数组
  }

}
const handleSearch = () => {
  if (
    currentSearchData.releaseName !== searchData.releaseName ||
    currentSearchData.release !== searchData.release ||
    currentSearchData.flow !== searchData.flow ||
    currentSearchData.task !== searchData.task ||
    currentSearchData.taskType !== searchData.taskType
  ){
    currentSearchData.releaseName = searchData.releaseName
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
const handleModelRefresh = (releaseId: number) => {
  getModelData(releaseId)
}
const handleArgumentRefresh = (releaseId: number) => {
  getArgumentData(releaseId)
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
          <el-input v-model="searchData.releaseName" placeholder="请输入" />
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
          <el-button type="primary" :icon="CirclePlus" @click="()=>{dialogArgumentVisible=true;batchAddArgument=true}">批量新增参数</el-button>
          <el-button type="danger" :icon="Delete" @click="()=>{dialogArgumentVisible=true;batchDeleteArgument=true}">批量删除参数</el-button>
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
        <el-table ref="multipleTableRef" :data="tableData" @expand-change="handleExpandChange" :expand-row-keys="expands"
            :row-key="row => row.id">
            <el-table-column width="50" align="center">
              <template #header>
                <div style="display: flex; align-items: center; justify-content: center;">
                  <el-checkbox v-model="isAboveSelected" @change="handleToggleSelectAbove" style="margin-right: 4px;"/>
                  <el-checkbox v-model="isAllSelected" @change="handleToggleSelectAll"/>
                </div>
              </template>
              <template #default="{ row }">
                <el-checkbox v-model="tableKey[row.id]" />
              </template>
            </el-table-column>
          <el-table-column type="expand">
            <template class="demo-table-expand" #default="slotProps">
              <el-tabs type="border-card" v-model="activeName" class="demo-tabs">
                <el-tab-pane label="模型配置" name='0'>
                  <el-card v-loading="loadingModel" shadow="never">
                    <div class="toolbar-wrapper">
                      <div>
                        <el-button type="primary" :icon="CirclePlus" @click="()=>{dialogModelVisible = true; 
                          formModelData.releaseId=slotProps.row.id}">新增模型</el-button>
                        <el-button type="danger" :icon="Delete" @click="handleModelBatchDelete">批量删除</el-button>
                      </div>
                      <div>
                        <el-tooltip content="下载">
                          <el-button type="primary" :icon="Download" circle />
                        </el-tooltip>
                        <el-tooltip content="刷新表格">
                          <el-button type="primary" :icon="RefreshRight" circle @click="handleModelRefresh(slotProps.row.id)" />
                        </el-tooltip>
                      </div>
                    </div>
                    <div class="table-wrapper">
                      <el-table ref="multipleModelTableRef" :data="modelData[slotProps.row.id]">
                        <el-table-column prop="name" label="模型名称" align="center" />
                        <el-table-column prop="weight" label="权重名称" align="center" />
                        <el-table-column fixed="right" label="操作" width="200" align="center">
                          <template #default="scope">
                            <el-button type="primary" text bg size="small" @click="handleModelUpdate(scope.row, slotProps.row.id)">修改</el-button>
                            <el-button type="success" text bg size="small" @click="preHandleModelCopy(scope.row)">拷贝</el-button>
                            <el-button type="danger" text bg size="small" @click="handleModelDelete(scope.row, slotProps.row.id)">删除</el-button>
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
                        <el-button type="primary" :icon="CirclePlus" @click="()=>{dialogArgumentVisible = true; 
                          formArgumentData.releaseId=slotProps.row.id}">新增参数</el-button>
                        <el-button type="danger" :icon="Delete" @click="handleArgumentBatchDelete">批量删除</el-button>
                      </div>
                      <div>
                        <el-tooltip content="下载">
                          <el-button type="primary" :icon="Download" circle />
                        </el-tooltip>
                        <el-tooltip content="刷新表格">
                          <el-button type="primary" :icon="RefreshRight" circle @click="handleArgumentRefresh(slotProps.row.id)" />
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
                        <el-table-column fixed="right" label="操作" width="200" align="center">
                          <template #default="scope">
                            <el-button type="primary" text bg size="small" @click="handleArgumentUpdate(scope.row)">修改</el-button>
                            <el-button type="success" text bg size="small" @click="preHandleArgumentCopy(scope.row)">拷贝</el-button>
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
          <el-table-column prop="taskType" label="任务类型" align="center" />
          <el-table-column prop="task" label="任务" align="center" />
          <el-table-column prop="flow" label="工作流" align="center" />
          <el-table-column prop="release" label="版本" align="center" />
          <el-table-column prop="releaseName" label="展示" align="center" />
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
        <el-form-item prop="flowId" label="工作流" >
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
        <el-select v-if="copyModel" v-model="formModelData.releaseId" placeholder="请选择目标版本" filterable>
          <el-option
            v-for="([rid, rname]) in Object.entries(tableName)"
            :key="Number(rid)"
            :label="rname"
            :value="Number(rid)"
          />
        </el-select>
        <el-form-item prop="name" label="模型名称">
          <el-input v-model="formModelData.name" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="weightId" label="权重对象">
          <el-select v-model="formWeightId" placeholder="请选择权重" filterable>
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
        <el-button type="primary" @click="handleModel">确认</el-button>
      </template>
    </el-dialog>
    <!-- 新增/修改argument -->
    <el-dialog
      v-model="dialogArgumentVisible"
      :title="titleText"
      @close="resetArgumentForm"
      width="30%"
    >
      <el-form ref="formArgumentRef" :model="formArgumentData" :rules="formArgumentRules" label-width="100px" label-position="left">
        <el-select v-if="copyArgument" v-model="formArgumentData.releaseId" placeholder="请选择目标版本" filterable>
          <el-option
            v-for="([rid, rname]) in Object.entries(tableName)"
            :key="Number(rid)"
            :label="rname"
            :value="Number(rid)"
          />
        </el-select>
        <el-form-item prop="name" label="名称">
          <el-input v-model="formArgumentData.name" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="type" label="类型">
          <el-input v-model="formArgumentData.type" placeholder="请输入" />
        </el-form-item>
        <el-form-item v-if="!batchDeleteArgument" prop="default" label="初始值">
          <el-button @click="handleShow(-1, 0, 1)"/>
        </el-form-item>
        <el-form-item v-if="!batchDeleteArgument" prop="config" label="配置">
          <el-button @click="handleShow(-1, 1, 1)"/>
        </el-form-item>
        <el-form-item prop="dynamic" label="动态性">
          <el-checkbox v-model="formArgumentData.dynamic" placeholder="请选择" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogArgumentVisible=false">关闭</el-button>
        <el-button type="primary" @click="handleArgument">确认</el-button>
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
