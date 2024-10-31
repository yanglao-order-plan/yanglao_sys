<template>
    <el-card>
        <el-input v-if="argName === 'text'"
        v-model="argValue"
        :disabled="argConfig?.disabled ?? null"
        :placeholder="argConfig?.placeholder ?? null"
        :clearable="argConfig?.clearable ?? null"
        />
        <el-input-number v-else-if="argName === 'number'"
        v-model="argValue"
        :min="argConfig?.min ?? null"
        :max="argConfig?.max ?? null"
        :step="argConfig?.step ?? null"
        :disabled="argConfig?.disabled ?? null"
        />
        <!-- 布尔选择开关 -->
        <el-switch v-else-if="argType === 'ratio'"
        v-model="argValue"
        :disabled="argConfig?.disabled ?? null"
        />
        <el-select v-else-if="argType === 'select'"
        v-model="argValue"
        :disabled="argConfig?.disabled ?? null">  //这里就需要预处理options
            <el-option v-if="argConfig?.opinions"
                v-for="option in argConfig.opinions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
            />
        </el-select>
        <el-select v-else-if="argType === 'draw'"
        v-model="argValue"
        :disabled="argConfig?.disabled ?? null">  //这里就需要预处理options
            <el-option v-if="argConfig?.opinions"
                v-for="option in argConfig.opinions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
            />
        </el-select>
    </el-card>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
export interface ArgProps {
  argName: string
  argType: string
  argValue: any
  argConfig: Record<string, any>  //自动解析
}
const props = defineProps<ArgProps>()
</script>

<style lang="scss" scoped>
</style>
