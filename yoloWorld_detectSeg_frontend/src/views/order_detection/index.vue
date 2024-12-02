<script lang="ts" setup>
import { computed, reactive, ref, watch } from "vue"

import { type IOrderData } from "@/api/order_detection/types/order_detection"

import { Refresh } from "@element-plus/icons-vue"
import { type IGetOrderData } from "@/api/order_detection/types/order_detection"

import { getAllOrdersApi, detectOrderApi,getOrderDataApi } from "@/api/order_detection"
import { usePagination } from "@/hooks/usePagination"

import { ElMessage } from "element-plus"
import { Search } from "@element-plus/icons-vue"



// 将模式与参数的加载分开




defineOptions({
  name: "Infer"
})
// 原始容器
const loading = ref<boolean>(false)

const predicting = ref<boolean>(false)




const orderVisible = ref<boolean>(false)

// 结构容器
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()


const currentSearchData = reactive({
  orderId:"",
  serviceId: "",
})
const selectedOrderData = reactive({
  serviceId: "",
  orderId: "",
})


const  orderData = ref<IGetOrderData[]>([])





// 检测的工单图片(数组形式，base64编码)
const detectImagesData: any = reactive([{
  originImage:"", //原始图片没加密
  resultBase64: "",//推理图片加密
  resultImageUrl: "",
  inferResult: [],
  inferDescription: "",
  inferPeriod: ""
}])

// const detectImageData: any = {
//   originImage:"", //原始图片没加密
//   resultBase64: "",//推理图片加密
//   // resultImageUrl: computed(() => {
//   //   if (detectImageData.resultBase64) {  // 根据base64字符串自动解密
//   //     const blob = dataURItoBlob(detectImageData.resultBase64)
//   //     return URL.createObjectURL(blob)
//   //   } else {
//   //     return ""
//   //   }
//   // }),
//   resultImageUrl:"",
//   inferResult: [],
//   inferDescription: "",
//   inferPeriod: ""
// }

// const detectImagesData: any = reactive<typeof detectImageData[]>([])
// const startImg: any = reactive<typeof detectImageData[]>([])



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

function deCodeBase64(code : string){
     if (code) {  // 根据base64字符串自动解密
      const blob = dataURItoBlob(code)
      return URL.createObjectURL(blob)
    } else {
      return ""
    }
}
//既可以获取全部信息，也可以搜索
const getOrderData = () => {
  loading.value = true
  getOrderDataApi({
    currentPage: paginationData.currentPage,
    size: paginationData.pageSize,
    orderId: Number(searchData.orderId) || undefined,
    serviceId: Number(searchData.serviceId) || undefined,
  })
    .then((res) => {
      paginationData.total = res.data.total
      orderData.value = res.data.list
      // console.log(orderData.value)
    })
    .catch(() => {
      orderData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}


// 切换模型（改检测工单)
const detectOrder = () => {
  detectImagesData.length = 0
  detectOrderApi(Number(selectedOrderData.orderId)).then((res) => {
    // startImg = res.data.startImg
    res.data.startImg.forEach((item, index) => {
      detectImagesData.push(item)
    })

    res.data.imgUrl.forEach((item, index) => {
      // console.log
      detectImagesData.push(item)
    })
    res.data.endImg.forEach((item, index) => {
      detectImagesData.push(item)
    })
    console.log(detectImagesData)
    detectImagesData.forEach((item:any)=>{
      console.log("11")
      item.resultImageUrl = deCodeBase64(item.resultBase64)
    })
    console.log(detectImagesData)

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

const handleSelect = (row: IGetOrderData) => {
  selectedOrderData.orderId = row.orderId.toString()
  selectedOrderData.serviceId =row.serviceId.toString() 
  orderVisible.value = false

}
const searchData = reactive({
  orderId:"",
  serviceId:"",
})

const handleSearch = () =>{
  if (paginationData.currentPage === 1) {
    getOrderData()
  }
  // 当paginationData.currentPage发生改变时 , getOrderData会自动调用
  paginationData.currentPage = 1 
}
function showOrder() {
  orderVisible.value = !orderVisible.value;
}

//等待写
const exportExcel = () => {

}
getOrderData()
watch([() => paginationData.currentPage, () => paginationData.pageSize], getOrderData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-row>
        <el-col :span="14">
          <div class="grid-content">
            <div>
              <div class="SwitchModelCSS">
                服务类型：
                <el-text v-model="selectedOrderData.serviceId" type="success" size="large">
                  {{ selectedOrderData.serviceId }}
                </el-text>
              </div>
              <div class="SwitchModelCSS">
                工单号：
                <el-text v-model="selectedOrderData.orderId" type="success" size="large">
                  {{ selectedOrderData.orderId }}
                </el-text>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="4" class="SwitchModelCSS">
          <div class="grid-content ep-bg-purple">
            <el-button type="primary" :icon="Refresh" @click="showOrder">选择工单</el-button>
          </div>
          <el-dialog title="工单信息" v-model="orderVisible">
            <el-form  :inline="true" :model="searchData">
              <el-form-item prop="serviceId" label="任务类型id">
                  <el-input v-model="searchData.serviceId" placeholder="请输入" />
              </el-form-item>
              <el-form-item prop="orderId" label="工单id">
                  <el-input v-model="searchData.orderId" placeholder="请输入" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
              </el-form-item>
            </el-form>
            <!-- <el-form-item>
              <el-button type="primary"  @click="handleSearch">查询</el-button>
            </el-form-item> -->
            <div class="table-wrapper">

              <el-table  :data="orderData">
                <el-table-column prop="no" label="编号" align="center" />
                <el-table-column prop="orderId" label="工单号" align="center" />
                <el-table-column prop="serviceId" label="服务类型" align="center" />
                <el-table-column prop="projectType" label="服务内容" align="center" />
                <!-- <el-table-column prop="orderContent" label="工单内容" align="center" /> -->
                <el-table-column fixed="right" label="选择" width="100" align="center">
                  <template #default="scope">
                    <el-button type="primary" text bg size="small" @click="handleSelect(scope.row)">选择</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div class="pager-wrapper">
              <el-pagination background :layout="paginationData.layout" :page-sizes="paginationData.pageSizes"
                :total="paginationData.total" :page-size="paginationData.pageSize"
                :currentPage="paginationData.currentPage" @size-change="handleSizeChange"
                @current-change="handleCurrentChange" />
            </div>
          </el-dialog>
        </el-col>
        <el-col :span="4" class="SwitchModelCSS">
          <div class="grid-content ep-bg-purple">
            <el-button type="success" :icon="Refresh" @click="detectOrder">检测工单</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>



    <el-card v-loading="predicting" shadow="never" class="search-wrapper">
      <el-button type="primary" @click="exportExcel">excel导出</el-button>
      <div class="grid-content text-description" >
        <el-row>
          <el-col :span="10">原始图片 </el-col>
          <el-col :span="10"> 推测图片</el-col>
        </el-row>
      </div>
      <el-row :gutter="20" v-for=" item in detectImagesData ">
        <el-col :span="10">
          <div class="grid-content ep-bg-purple">
            <el-image v-if="item.originImage" :src="item.originImage" :fit="'scale-down'"
              :preview-src-list="[item.originImage]" />
            <div v-else class="image-placeholder">原始图片</div>
          </div>
        </el-col>
        <el-col :span="10">
          <div class="grid-content ep-bg-purple">
            <el-image
              v-if="item.resultBase64"
              :src="item.resultImageUrl"
              :fit="'scaleDown'"
              :preview-src-list="[item.resultImageUrl]"
            />
            <div v-else class="image-placeholder">检测结果图片</div>
          </div>
        </el-col>
      <el-col :span="20" v-if="item.inferDescription">
        <el-collapse>
          <el-collapse-item title="检测结果">
            <div>检测描述:   {{item.inferDescription}}</div>
          </el-collapse-item>
        </el-collapse>
      </el-col>
        <!-- <el-col :span="18">
          <div class="grid-content ep-bg-purple">
            <el-table :data="inferImageData.inferResult"
              v-if="inferImageData.inferResult && inferImageData.inferResult.length > 0">
              <el-table-column prop="label" label="检测类别" />
              <el-table-column prop="score" label="置信度" />
              <el-table-column prop="points" label="锚点集" />
              <el-table-column prop="group_id" label="分组" />
              <el-table-column prop="description" label="描述" />
            </el-table>
            <div v-else class="image-placeholder">暂无结果</div>
          </div>
        </el-col> -->
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
.text-description{
  text-align: center;
}
</style>

