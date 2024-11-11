<script lang="ts" setup>
import { reactive, ref, watch, computed } from "vue"
import { 
  createWeightDataApi, deleteWeightDataApi, updateWeightDataApi, getWeightDataApi,
} from "@/api/manage"
import { type IGetWeightData } from "@/api/manage/types/weight"
import { type FormInstance, type FormRules, ElMessage, ElMessageBox, ElTable } from "element-plus"
import { Search, Refresh, CirclePlus, Delete, Download, RefreshRight } from "@element-plus/icons-vue"
import { usePagination } from "@/hooks/usePagination"

defineOptions({
  name: "WeightManage"
})

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const multipleTableRef = ref<InstanceType<typeof ElTable>>()

//#region 增
const dialogVisible = ref<boolean>(false)
const formRef = ref<FormInstance | null>(null)
const formData = reactive({
  name: "",
  localPath: "",
  onlineUrl: "",
  enable: 1
})
const formRules: FormRules = reactive({
  name: [{ required: true, trigger: "blur", message: "请输入权重名称" }],
  localPath: [{ required: false, trigger: "blur", message: "请配置本地路径" }],
  onlineUrl: [{ required: false, trigger: "blur", message: "请配置在线路径" }],
  enable: [{ required: true, trigger: "blur", message: "请确认是否可用" }],
})
const handleCreate = () => {
  formRef.value?.validate((valid: boolean) => {
    if (valid) {
      if (currentUpdateId.value === undefined) {
        createWeightDataApi({
          name: formData.name,
          localPath: formData.localPath,
          onlineUrl: formData.onlineUrl,
          enable: formData.enable
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
        updateWeightDataApi({
          id: currentUpdateId.value,
          name: formData.name,
          localPath: formData.localPath,
          onlineUrl: formData.onlineUrl,
          enable: formData.enable
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
  formData.localPath= "",
  formData.onlineUrl= "",
  formData.enable= 1
}
//#region 删
const handleDelete = (row: IGetWeightData) => {
  console.log(row)
  ElMessageBox.confirm(`正在删除权重：${row.weight}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteWeightDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getTableData()
    })
  })
}
//#endregion

// 批量删除
const handleBatchDelete = () => {
  ElMessageBox.confirm("确认删除选中的权重？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    const selectionRows = multipleTableRef.value!.getSelectionRows()
    if (selectionRows.length === 0) {
      ElMessage.warning("请先选择要删除的权重")
      return
    } else {
      selectionRows.forEach((row: any) => {
        deleteWeightDataApi(row.id).then(() => {
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
const handleUpdate = (row: IGetWeightData) => {
  currentUpdateId.value = row.id
  formData.name = row.weight
  formData.localPath = row.localPath
  formData.onlineUrl = row.onlineUrl
  formData.enable = row.enable
  dialogVisible.value = true
}
//#endregion

//#region 查
const tableData = ref<IGetWeightData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  weight: "",
  enable: 1,
})
const searchEnable = computed({
  get() {
    return searchData.enable === 1 ? true : false;
  },
  set(value) {
    searchData.enable = value ? 1 : 0;
  }
});
const currentSearchData = reactive({
  weight: "",
  enable: 1,
})
const getTableData = () => {
  loading.value = true
  console.log(currentSearchData.enable)
  getWeightDataApi({
    currentPage: paginationData.currentPage,
    size: paginationData.pageSize,
    weight: currentSearchData.weight,
    enable: currentSearchData.enable
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
    currentSearchData.weight !== searchData.weight ||
    currentSearchData.enable !== searchData.enable
  ){
    currentSearchData.weight = searchData.weight
    currentSearchData.enable = searchData.enable
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
const handleRefresh = () => {
  getTableData()
}
//#endregion

/** 监听分页参数的变化 */
watch([() => paginationData.currentPage, () => paginationData.pageSize], getTableData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="weigh" label="权重名称">
          <el-input v-model="searchData.weight" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="weightEnable" label="是否可用">
          <el-checkbox v-model="searchEnable" placeholder="请确认" />
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
          <el-button type="primary" :icon="CirclePlus" @click="dialogVisible = true">新增权重</el-button>
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
          <el-table-column prop="weight" label="权重名称" align="center" />
          <el-table-column prop="localPath" label="本地路径" align="center" />
          <el-table-column prop="onlineUrl" label="在线路径" align="center" />
          <el-table-column prop="enable" label="可用性" align="center">
            <template #default="slotProps">
              <span :style="{ color: slotProps.row.enable ? 'green' : 'red' }">
                {{ slotProps.row.enable ? '是' : '否' }}
              </span>
            </template>
          </el-table-column>
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
      :title="currentUpdateId === undefined ? '新增权重' : '修改权重'"
      @close="resetForm"
      width="30%"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="name" label="权重名称">
          <el-input v-model="formData.name" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="localPath" label="本地路径">
          <el-input v-model="formData.localPath" placeholder="请选择" />
        </el-form-item>
        <el-form-item prop="onlineUrl" label="在线路径">
          <el-input v-model="formData.onlineUrl" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="enable" label="可用性">
          <el-checkbox v-model="formData.enable" placeholder="请确认" />
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
