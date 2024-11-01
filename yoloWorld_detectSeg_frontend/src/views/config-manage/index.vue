<template>
  <fs-crud ref="crudRef" v-bind="crudOptions" @search="onSearch" />
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { getTasksWithDetails, createTaskWithFlows, updateTaskWithDetails, deleteTask } from './api/index.ts';
import { useCrud } from '@fast-crud/fast-crud';

const crudRef = ref();
const crudOptions = reactive({
  request: {
    pageRequest: async (query) => {
      const response = await getTasksWithDetails(query);
      return {
        records: response,
        total: response.length,
      };
    },
    addRequest: async ({ form }) => {
      return await createTaskWithFlows(form);
    },
    editRequest: async ({ form }) => {
      return await updateTaskWithDetails(form.id, form);
    },
    delRequest: async ({ row }) => {
      return await deleteTask(row.id);
    },
  },
  columns: {
    id: {
      title: 'ID',
      key: 'id',
      type: 'number',
      form: { show: false },
    },
    name: {
      title: '任务名称',
      key: 'name',
      type: 'text',
      search: { show: true },
      form: {
        rules: [{ required: true, message: '请输入任务名称' }],
      },
    },
    type: {
      title: '任务类型',
      key: 'type_name',
      type: 'dict-select',
      dict: {
        url: '/config-manage/task_types', // 请求任务类型字典数据
        value: 'id',
        label: 'name',
      },
      form: {
        rules: [{ required: true, message: '请选择任务类型' }],
      },
    },
    flows: {
      title: '流程',
      key: 'flows',
      type: 'dynamic',
      form: {
        component: {
          name: 'fs-dynamic',
          fieldMap: {
            id: 'flow_id',
            name: 'flow_name',
          },
          // 配置请求动态数据，例如流程数据
          optionsRequest: async () => {
            const response = await axios.get('/config-manage/flows');
            return response.data;
          },
        },
      },
    },
  },
});

const onSearch = (query) => {
  // 可扩展的搜索功能
};
</script>
