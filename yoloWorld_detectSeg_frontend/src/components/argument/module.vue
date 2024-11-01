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
              @on-update="argChange"
        />
        <JsonEditorVue v-else-if="props.argType === 'json'"
            class="json-editor" 
            :modelValue="argValue" 
            :currentMode="props.argConfig?.disabled? 'view':'code'"
        />
    </el-card>
</template>

<script lang="ts" setup>
import {ref} from 'vue'
import Annotation from './annotation.vue'
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
// 向外部暴露的事件接口
const emit = defineEmits([
	'argChange', 
])
// 提醒父组件数据改变
const argChange = (argValue: any) => {
	emit('argChange', props.argName, argValue)
}
// const getCurrentAnnotations = (taggingResults: any) => {
//     argValue.value = taggingResults
// }

</script>
<style lang="scss" scoped>
.json-editor {
  height: 400px; /* 你可以设置为适合你需要显示的行数的高度 */
  overflow-y: auto;
}
</style>
