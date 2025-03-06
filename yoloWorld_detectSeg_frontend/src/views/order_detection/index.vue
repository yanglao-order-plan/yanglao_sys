<script lang="ts" setup>
import { computed, reactive, ref, watch } from "vue"

import { type IOrderData } from "@/api/order_detection/types/order_detection"
import Argument from '@/components/argument/module.vue'
import { Refresh } from "@element-plus/icons-vue"
import { type IGetOrderData,IWeightData,IArgData,IFlowData,IDetectData,IDOrigin} from "@/api/order_detection/types/order_detection"

import { getAllOrdersApi,getOrderDataApi,switchModelApi,switchFlowApi,switchWeightApi,getCurrentWeightApi,switchParamApi,getCurrentParamApi,getDetectDataApi } from "@/api/order_detection"
import { usePagination } from "@/hooks/usePagination"

import { ElMessage } from "element-plus"
import { Search } from "@element-plus/icons-vue"
import type { CascaderValue } from 'element-plus'
import { el } from "element-plus/es/locale"
import { AgGridVue } from 'ag-grid-vue3'
import type { ColDef } from 'ag-grid-community'
import "ag-grid-community/styles/ag-grid.css"; 
import "ag-grid-community/styles/ag-theme-quartz.css";


// 将模式与参数的加载分开



//????
defineOptions({
  name: "Infer",
  components:{
    AgGridVue
  }
})
const loaded = ref<boolean>(false)
const choosen = ref<boolean>(false)
const loading = ref<boolean>(false)
const loading2= ref<boolean>(false)
const predicting = ref<boolean>(false)
const orderVisible = ref<boolean>(false)
const itemIndex = ref<number>(0)
 

// 结构容器
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()
const flowsData = ref<IFlowData[]>([])
const selectedFlowOptions = ref([])
const flowOptions = ref<{ value: string; label: string; children: { value: string; label: string }[] }[]>([])
const weightOptions = ref<{ [key: string]: { value: string; label: string; disabled: boolean }[]}>({})
const currentParamData = reactive<{ [key: string]: any }>({});
const currentSearchData = reactive({
  orderId:"",
  serviceId: "",
})
const selectedOrderData = reactive({
  serviceId: "",
  orderId: "",
})

const handledParamData = reactive<{ [key: string]: any }>({});
const currentHyperData = reactive<{ [key: string]: any }>({});
const handledHyperData = reactive<{ [key: string]: any }>({});
const selectedWeightData = reactive<{ [key: string]: string }>({});
const currentWeightData = reactive<{ [key: string]: string }>({});

const  orderData = ref<IGetOrderData[]>([])
const weightsData = ref<IWeightData[]>([])
const paramsData = ref<IArgData[]>([])
const hypersData = ref<IArgData[]>([])

const currentFlowData = reactive({
  flow: "", 
  release: "",
})
const selectedFlowData = reactive({
  flowName : "",
  flow: "",
  release: "",
})
const searchData = reactive({
  orderId:"",
  serviceId:"",
})

interface CascaderProps {
  expandTrigger?: "click" | "hover"
}
const props: CascaderProps = {
  expandTrigger: "hover" as const
}




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
      itemIndex.value = 0
      // console.log(orderData.value)
    })
    .catch(() => {
      orderData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}

const originData:any =ref([{
  stage: "",
  url: []
}])


//模型推理返回信息
const detectData: any = ref([{
  field:"",
  msg: "",
  type: "",
  avatars: []
}])
// 控制弹窗显示和要展示的图片
const dialogVisible = ref(false);
const avatarsToShow = ref<string[]>([]);
// 点击按钮时显示 avatars 图片

const columnDefOrigin =ref<ColDef[]>([
  
  {
      headerName: "stage",
      field: "stage"
    },
    {
      headerName: "id",
      field: "id"
    },
    {
      headerName: "base64",
      field: "base64",
      cellRenderer: 'avatarRenderer' // 使用我们自定义的渲染器
    }
])



const columnDefs = ref<ColDef[]>([
  //{ headerName:'模型名称',field:'flow',flex:1},
    { 
      headerName:"field",
      field:"field"
    },
    {
      headerName: "Message Content",
      field: "msg"
    },
    {
      headerName: "Type Name",
      field: "type"
    },
    // {
    //   headerName: "Avatars",
    //   field: "avatars",
    //   cellRenderer: 'avatarRenderer' // 使用我们自定义的渲染器
    // }
])
// const rowData = [{msg:'1',type:'erro',avatars:"http://www.mcwajyfw.com/upload/healthCloud//12/3/de0b8ee6ceed440a8825b5d4c05450281685574116089.jpeg"}
// ];
// 自定义单元格渲染器组件（内联定义）
const AvatarCellRenderer = {
  template: ` <div class="avatar-container">
              <img v-for="(url, index) in params.value" :key="index" :src="url" class="avatar" alt="Avatar"  />
              </div>`,
  setup(props: any) {
    // ag-grid会传入params作为props
    return { params: props.params}
  }
}
// 定义框架组件映射
const frameworkComponents = {
  avatarRenderer: AvatarCellRenderer
}

// 检测工单
const handleDetect = () => {
  getDetectDataApi(Number(selectedOrderData.orderId))
    .then((res) => {
      originData.value=res.data.origin
      // originData.forEach((item :IDOrigin) => {
      //   item.base64.forEach((img,index)=>{
      //     item.base64[index] = deCodeBase64(item.base64[index])
      //   })
      // });
      detectData.value = res.data.result
      // 遍历 res.data.list 并添加到 detectData
      // detectData.forEach((item :IDetectData) => {
      //   item.avatars.forEach((img,index)=>{
      //     item.avatars[index] = deCodeBase64(item.avatars[index])
      //   })
      // });
    })
    .catch(() => {
      ElMessage({
        message: '推理响应有误',
        type: 'warning',
      });
    })
    .finally(() => {
      predicting.value = false;
    });
};

// 切换模型（改检测工单)
// const detectOrder = () => {
//   detectImagesData.length = 0
//   detectOrderApi(Number(selectedOrderData.orderId)).then((res) => {
//     // startImg = res.data.startImg
//     res.data.startImg.forEach((item, index) => {
//       detectImagesData.push(item)
//     })

//     res.data.imgUrl.forEach((item, index) => {
//       // console.log
//       detectImagesData.push(item)
//     })
//     res.data.endImg.forEach((item, index) => {
//       detectImagesData.push(item)
//     })
//     console.log(detectImagesData)
//     detectImagesData.forEach((item:any)=>{
//       item.resultImageUrl = deCodeBase64(item.resultBase64)
//     })
//     console.log(detectImagesData)

//   })
//     .catch(() => {
//       ElMessage({
//         message: "推理响应有误",
//         type: "warning"
//       })
//     })
//     .finally(() => {
//       predicting.value = false
//     })
// }

// 根据请求的工单号 ，返回对应的工作流和对应版本，后端接口为/order/switch/<int:order_id>（工作流和版本的关系是一对多）
const handleOrderSwitch = () =>{
  switchModelApi(Number(selectedOrderData.orderId)).then((res)=>{
    // flowsData.value = res.data
    // console.log(res.data)
    flowOptions.value = generateFlowCascaderOptions(res.data)
  })
}
// 新
const generateFlowCascaderOptions = (list: {}) => {
  const options: { value: string; label: string; children: { value: string; label: string }[] }[] = []
  for(let item in list){
    const map: { [key: string]: { value: string; label: string; children: { value: string; label: string }[] } } = {}
    map[item]={
        value: item,
        label: item,
        children: []
      }
    options.push(map[item])
    list[item].forEach(element => { 
      map[item].children.push({value: element,label: element })
    });
  }
  console.log(options)
  return options
}
//旧
// const generateFlowCascaderOptions = (list: IFlowData[]) => {
//   const options: { value: string; label: string; children: { value: string; label: string }[] }[] = []
//   const map: { [key: string]: { value: string; label: string; children: { value: string; label: string }[] } } = {}
//   list.forEach((item) => {
//     const flow = item.flowName
//     const release = item.releaseName
//     const releaseName = item.releaseShowName
//     if (!map[flow]) {
//       map[flow] = {
//         value: flow,
//         label: flow,
//         children: []
//       }
//       options.push(map[flow])
//     }
//     map[flow].children.push({
//       value: release,
//       label: releaseName
//     })
//   })
//   return options
// }


// 根据模型的版本名，返回para和weight
const handleFlowSwitch = () =>{
  // 对应后端接口/order/switch/<string:release_name>
  switchFlowApi(selectedFlowData.release).then((res)=>{
    // clearHelper(['weight', 'param', 'hyper'])   暂时注释
    weightsData.value = res.data["weight"]
    weightOptions.value = generateWeightOptions(res.data["weight"])
    if (res.data["param"] && res.data["param"].length > 0) {
        paramsData.value = res.data["param"]
        loadDefault('param')
      } else {
        console.warn("No params found in the response.");
      }
      choosen.value=true
    // getCurrentFlow() 
  })
}
// const getCurrentFlow = () => {
//   getCurrentFlowApi().then((res) => {
//     currentFlowData.flow = res.data.flowName
//     currentFlowData.release = res.data.releaseName
//   })
//   .finally(() => {
//     paramsData.value.forEach((element: any) => {  // 提前装载初始值
//       handledParamData[element['argName']] = element['argDefault']
//     });
//     getAllCurrentWeights()
//   })

// }

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


const handleSelect = (row: IGetOrderData) => {
  selectedOrderData.orderId = row.orderId.toString()
  selectedOrderData.serviceId =row.serviceId.toString() 
  orderVisible.value = false

}

const handleSearch = () =>{
  if (paginationData.currentPage === 1) {
    getOrderData()
  }
  // 当paginationData.currentPage发生改变时 , getOrderData会自动调用
  paginationData.currentPage = 1 
}
function showOrder() {
  console.log("1111")
  console.log(orderVisible.value)
  orderVisible.value = !orderVisible.value;
  console.log(orderVisible.value)
}

const handleFlowChange = (selectedOptions: CascaderValue) => {
  console.log(selectedOptions)
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
  // 对应 /order/weight/switch
  switchWeightApi({
    switchParamRelease:selectedFlowData.release,//需要添值
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


// 对应后端 /order/weight/current
const getCurrentWeight = (weigthKey: string|number) => {
  getCurrentWeightApi({
    switchParamRelease: selectedFlowData.release, //需要填充
    currentWeightKey: weigthKey
  }).then((res) => {
    currentWeightData[weigthKey] = res.data.weightName;
    selectedWeightData[weigthKey] = res.data.weightName;
  }).catch((error) => {
    console.error("Error fetching weight data:", error);
  });
};





const handleParamChange = (paramName: string, paramValue: any) => {
  handledParamData[paramName] = paramValue
  handleParamSwitch(paramName)
  const message = `已经完成配置${paramName}: ${paramValue}`
  ElMessage({
    message: message,
    type: "success"
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
  // /order/param/switch
  switchParamApi({
    switchParamRelease: selectedFlowData.release,//待补充
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
//  order/param/current
const getCurrentParam = (paramName: string) => {
  getCurrentParamApi({
    switchParamRelease:selectedFlowData.release,//需要填充
    currentParamName: paramName
  }).then((res) => {
    currentParamData[res.data.argName] = res.data.argValue;
  }).catch((error) => {
    console.error("Error fetching weight data:", error);
  });
};


// const clearHelper = (keys: string[]) => {
//   keys.forEach(key => {
//     if (key === 'flow') clearSelectedFlow();
//     else if (key === 'weight') clearSelectedWeight();
//     else if (key === 'param') clearHandledParam();
//     else if (key === 'hyper') clearHandledHyper();
//   });
// };


// const generateFlowCascaderOptions = (list: IFlowData[]) => {
//   const options: { value: string; label: string; children: { value: string; label: string }[] }[] = []
//   const map: { [key: string]: { value: string; label: string; children: { value: string; label: string }[] } } = {}
//   list.forEach((item) => {
//     const flow = item.flowName
//     const release = item.releaseName
//     const releaseName = item.releaseShowName
//     if (!map[flow]) {
//       map[flow] = {
//         value: flow,
//         label: flow,
//         children: []
//       }
//       options.push(map[flow])
//     }
//     map[flow].children.push({
//       value: release,
//       label: releaseName
//     })
//   })
//   return options
// }
//等待写
const exportExcel = () => {

}
getOrderData()
watch([() => paginationData.currentPage, () => paginationData.pageSize], getOrderData, { immediate: true })

const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement;
  img.src = 'path/to/fallback/image.png'; // Add a fallback image path
  console.error('Image failed to load:', img.src);
};

const showAvatars = (avatars: string[]) => {
  if (!avatars || !Array.isArray(avatars)) {
    ElMessage.warning('No images available');
    return;
  }
  avatarsToShow.value = avatars;
  dialogVisible.value = true;
  console.log('Showing avatars:', avatarsToShow.value);
};
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

              <el-table  :data="orderData" >
                <el-table-column prop="no" label="编号" align="center" />
                <el-table-column prop="orderId" label="工单号" align="center" />
                <el-table-column prop="serviceId" label="服务类型" align="center" />
                <el-table-column prop="projectType" label="服务内容" align="center" />
                <!-- <el-table-column prop="orderContent" label="工单内容" align="center" /> -->
                <el-table-column  fixed="right" label="选择" width="100" align="center">
                  <template #default="scope" slot-scope="scope">
                    <el-button v-if="scope.row.flag==1" type="primary"  text bg size="small" @click="handleSelect(scope.row)">选择</el-button>
                    <el-button v-else type="info"   text bg size="small" plain disabled>没图片</el-button>
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
            <el-button type="success" :icon="Refresh" @click="handleOrderSwitch">确认工单</el-button>
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
                <el-text v-model="selectedFlowData.flow" type="success" size="large">
                  {{ selectedFlowData.flow }}
                </el-text>
              </div>
              <div class="SwitchModelCSS">
                当前版本：
                <el-text v-model="selectedFlowData.flow" type="success" size="large">
                  {{ selectedFlowData.release }}
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
              placeholder="请选择版本"
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


    <el-card v-loading="loading2" shadow="never" class="search-wrapper">
      <div class="grid-content ep-bg-purple">
        <el-button type="success" :icon="Refresh" @click="handleDetect">执行工作流</el-button>
      </div>
      <el-text>原始信息</el-text>
      <el-table :data="originData" style="width: 100%">
            <el-table-column label="Stage" prop="stage"></el-table-column>
            <!-- <el-table-column label="Id" prop="id"></el-table-column> -->
            <el-table-column label="Url">
              <template v-slot="scope">
                <el-button @click="showAvatars(scope.row.url)">
                  Show url
                </el-button>
              </template>
            </el-table-column>
          </el-table>
      <el-text>推理结果</el-text>
      <el-table :data="detectData" style="width: 100%">
        <el-table-column label="Field" prop="field"></el-table-column>
        <el-table-column label="Message" prop="msg"></el-table-column>
        <el-table-column label="Type" prop="type"></el-table-column>
        <el-table-column label="Avatars">
          <template v-slot="scope">
            <el-button @click="showAvatars(scope.row.avatars)">
              Show Avatars
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-dialog 
      v-model="dialogVisible" 
      title="Avatars" 
      width="60%"
      :destroy-on-close="true"
    >
      <div v-if="avatarsToShow && avatarsToShow.length">
        <el-row :gutter="20">
          <el-col v-for="(avatar, index) in avatarsToShow" :key="index" :span="8">
            <el-image 
              :src="avatar"
              alt="Avatar" 
              style="width: 100%; max-height: 500px; object-fit: cover;"
              @error="handleImageError"
            />
            <el-text>{{index}}</el-text>
          </el-col>
        </el-row>
      </div>
      <div v-else>
        No images to display
      </div>
    </el-dialog>
  
    
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

