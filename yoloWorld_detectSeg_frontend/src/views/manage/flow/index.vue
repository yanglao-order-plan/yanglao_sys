<script lang="ts" setup>
import { reactive, ref, watch } from "vue"
import { 
  createFlowDataApi, deleteFlowDataApi, updateFlowDataApi, getFlowDataApi, getTaskDataApi
} from "@/api/manage"
import { type IGetFlowData } from "@/api/manage/types/flow"
import { type IGetTaskData } from "@/api/manage/types/task"
import { type FormInstance, type FormRules, ElMessage, ElMessageBox, ElTable } from "element-plus"
import { Search, Refresh, CirclePlus, Delete, Download, RefreshRight } from "@element-plus/icons-vue"
import { usePagination } from "@/hooks/usePagination"
import type { CascaderValue } from 'element-plus'
defineOptions({
  name: "FlowManage"
})
interface CascaderProps {
  expandTrigger?: "click" | "hover"
}
const props: CascaderProps = {
  expandTrigger: "hover" as const
}
const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const multipleTableRef = ref<InstanceType<typeof ElTable>>()

//#region 增
const dialogVisible = ref<boolean>(false)
const formRef = ref<FormInstance | null>(null)
const selectedTaskOptions = ref<number[]>([])
const formData = reactive({
  name: "",
  taskId: 0,
})
const formRules: FormRules = reactive({
  name: [{ required: true, trigger: "blur", message: "请输入工作流名称" }],
  typeId: [{ required: true, trigger: "blur", message: "请选择工作流类型" }],
})
const handleCreate = () => {
  formRef.value?.validate((valid: boolean) => {
    if (valid) {
      if (currentUpdateId.value === undefined) {
        createFlowDataApi({
          name: formData.name,
          taskId: formData.taskId,
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
        updateFlowDataApi({
          id: currentUpdateId.value,
          name: formData.name,
          taskId: formData.taskId,
        }).then(() => {
          ElMessage.success("修改成功")
          dialogVisible.value = false
          getTableData()
        })
      }
    }
  })
}
const resetForm = () => {
  currentUpdateId.value = undefined
  formData.name = ""
  formData.taskId = 0
}
//#region 删
const handleDelete = (row: IGetFlowData) => {
  ElMessageBox.confirm(`正在删除工作流：${row.task}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteFlowDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getTableData()
    })
  })
}
//#endregion

// 批量删除
const handleBatchDelete = () => {
  ElMessageBox.confirm("确认删除选中的工作流？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    const selectionRows = multipleTableRef.value!.getSelectionRows()
    if (selectionRows.length === 0) {
      ElMessage.warning("请先选择要删除的工作流")
      return
    } else {
      selectionRows.forEach((row: any) => {
        deleteFlowDataApi(row.id).then(() => {
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
const handleUpdate = (row: IGetFlowData) => {
  currentUpdateId.value = row.id
  formData.name = row.flow
  formData.taskId = row.taskId
  selectedTaskOptions.value.length = 0
  selectedTaskOptions.value.push(row.typeId, row.taskId)
  dialogVisible.value = true
}
//#endregion

//#region 查
const tableData = ref<IGetFlowData[]>([])
const taskData = ref<IGetTaskData[]>([]) // 添加明确的类型声明
const taskOptions = ref<{ value: number; label: string; children: { value: number; label: string }[] }[]>([])
const currentSearchData = reactive({
  flow: "",
  task: "",
  taskType: ""
})
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  flow: "",
  task: "",
  taskType: ""
})
const generateTaskCascaderOptions = () => {
  const options: { value: number; label: string; children: { value: number; label: string }[] }[] = []
  const map: { [key: string]: { value: number; label: string; children: { value: number; label: string }[] } } = {}
  taskData.value.forEach((item: any) => {
    const id = item.id
    const typeId = item.typeId
    const taskType = item.taskType
    const task = item.task
    if (!map[taskType]) {
      map[taskType] = {
        value: typeId,
        label: taskType,
        children: []
      }
      options.push(map[taskType])
    }
    map[taskType].children.push({
      value: id,
      label: task
    })
  })
  return options
}
const handleTaskChange = (selectedOptions: CascaderValue) => {
  if (!Array.isArray(selectedOptions) || selectedOptions.length !== 2) return
  formData.taskId = selectedOptions[1] as number
}

const getTableData = () => {
  loading.value = true
  getFlowDataApi({
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
const handleSearch = () => {
  if (
    currentSearchData.flow !== searchData.flow ||
    currentSearchData.task !== searchData.task ||
    currentSearchData.taskType !== searchData.taskType
  ){
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
const getTaskData = () => {
  loading.value = true
  getTaskDataApi({
    currentPage: 1,
    size: -1,
    task: undefined,
    taskType: undefined
  })
    .then((res) => {
      taskData.value = res.data.list
      taskOptions.value = generateTaskCascaderOptions()
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
  getTaskData()
}
//#endregion
getTaskData()
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
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card v-loading="loading" shadow="never">
      <div class="toolbar-wrapper">
        <div>
          <el-button type="primary" :icon="CirclePlus" @click="dialogVisible = true">新增工作流</el-button>
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
        <el-table ref="multipleTableRef" :data="tableData">
          <el-table-column type="selection" width="50" align="center" />
          <el-table-column prop="taskType" label="任务类型" align="center" />
          <el-table-column prop="task" label="任务" align="center" />
          <el-table-column prop="flow" label="工作流" align="center" />
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
    <!-- 新增/修改 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentUpdateId === undefined ? '新增工作流' : '修改工作流'"
      @close="resetForm"
      width="30%"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="task" label="任务">
          <el-cascader
              v-model="selectedTaskOptions"
              :options="taskOptions"
              :props="props"
              @change="handleTaskChange"
              placeholder="请选择任务"
            />
        </el-form-item>
        <el-form-item prop="flow" label="工作流">
          <el-input v-model="formData.name" placeholder="请输入" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确认</el-button>
      </template>
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
