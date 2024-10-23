<script setup lang="ts">
import { UploadFilled } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const emits = defineEmits(["handleUpload"])
const handleUpload = (file: File) => {
  emits("handleUpload", file) // 触发自定义事件，并将 response 作为参数传递
  return false
}
</script>
<template>
  <el-upload
    class="upload-demo"
    drag
    :on-change="handleUpload"
    multiple
    :auto-upload="false"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">将需要检测的图片拖放到此处或<em>点击上传</em></div>
    <template #tip>
      <div class="el-upload__tip">图片格式仅支持jpg/png</div>
    </template>
  </el-upload>
</template>

<style lang="scss" scoped></style>
