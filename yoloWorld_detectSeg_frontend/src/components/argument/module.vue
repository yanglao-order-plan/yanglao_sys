<template>
    <el-card>
        <p>{{ props.argName }}</p>
        <el-input v-if="props.argType === 'text'" 
            v-model="argValue"
            @change="argChange"
            :disabled="props.argConfig?.disabled ?? false"
            :placeholder="props.argConfig?.placeholder ?? null"
            :clearable="props.argConfig?.clearable ?? true"
        />
        <el-input-number v-else-if="props.argType === 'number'"
            v-model="argValue"
            @change="argChange"
            :min="props.argConfig?.min ?? -Infinity"
            :max="props.argConfig?.max ?? Infinity"
            :step="props.argConfig?.step ?? 1"
            :disabled="props.argConfig?.disabled ?? false"
        />
        <!-- 布尔选择开关 -->
        <el-switch v-else-if="props.argType === 'ratio'"
            v-model="argValue"
            @change="argChange"
            :disabled="props.argConfig?.disabled ?? false"
        />
        <el-select v-else-if="props.argType === 'select'"
            v-model="argValue"
            @change="argChange"
            :disabled="props.argConfig?.disabled ?? false"> 
                <el-option v-if="props.argConfig?.options"
                    v-for="(option, index) in argConfig.options"
                    :key="index"
                    :label="Array.isArray(argConfig.options) ? option : index"
                    :value="option"
                />
        </el-select>
        <Annotation v-else-if="props.argType === 'draw'"
              style="width: 100%"
              :img-src="props.imageUrl??null"
              :typeList="props?.argConfig?.modes??null"
              @on-update="annChange"
        />
        <div v-else-if="props.argType === 'json'">
            <JsonEditorVue
                class="json-editor" 
                :modelValue="argValue" 
                :currentMode="props.argConfig?.disabled? 'view':'code'"
            />
            <el-button type="primary" @click="argChange">完成配置</el-button>
        </div>
        <div v-else-if="props.argType === 'base64'" class="grid-content ep-bg-purple">
          <UploadFile @handleUpload="onHandleUpload"/>
          <el-image
            v-if="base64Data.originalBase64"
            :src="base64Data.originalImageUrl"
            :fit="'scale-down'"
            :preview-src-list="[base64Data.originalImageUrl]"
            @load="base64Change"
          />
        </div>
    </el-card>
</template>

<script lang="ts" setup>
import {ref, reactive, computed, toRaw} from 'vue'
import Annotation from './annotation.vue'
import UploadFile from "@/components/UploadFile/index.vue"
import JsonEditorVue from 'json-editor-vue3'
export interface ArgProps {
  imageUrl: string | null
  argName: string
  argType: string
  argValue: any
  argConfig: Record<string, any>  //自动解析
}
const props = defineProps<ArgProps>()
const argValue = ref(props.argValue)
const base64Data: any = reactive({
  originalBase64: "",
  originalImageUrl: computed(() => {  // 自动计算url显示原始图片
    if (base64Data.originalBase64) {
      const blob = dataURItoBlob(base64Data.originalBase64)
      return URL.createObjectURL(blob)
    } else {
      return ""
    }
  }),
})
// 向外部暴露的事件接口
const emit = defineEmits([
	'argChange', 
])
// 提醒父组件数据改变
const argChange = () => {
	emit('argChange', props.argName, argValue)
}
const annChange = (argValue: any) => {
	emit('argChange', props.argName, argValue)
}
const base64Change = () => {
	emit('argChange', props.argName, toRaw(base64Data.originalBase64))
}
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
// 处理上传文件
const onHandleUpload = (file: any) => {
  // 如果后端的数据没有以 data:image/jpeg;base64 则需要判断加上
  const a = new FileReader()
      a.readAsDataURL(file.raw)
      a.onload = (e) => {
        if (e.target) {
            base64Data.originalBase64 = e.target.result
        }
      }
}
</script>
<style lang="scss" scoped>
.json-editor {
  height: 400px; /* 你可以设置为适合你需要显示的行数的高度 */
  overflow-y: auto;
}
.grid-content {
  border-radius: 4px;
  min-height: 36px;
}
</style>
