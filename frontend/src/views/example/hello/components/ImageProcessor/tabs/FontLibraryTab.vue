<template>
    <div style="display: flex; flex-direction: column; height: 590px;">
        <!-- 文件选择区域 -->
        <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 10px;">
            <el-button type="primary" size="small" @click="handleSelectFile" :loading="fileLoading">
                选择字库文件
            </el-button>
            <span v-if="selectedFileName" style="font-size: 12px; color: #909399;">
                已选择: {{ selectedFileName }}
            </span>
        </div>


        <!-- 字库列表表格 -->
        <el-table :data="fontLibraryList" height="100" border size="small" empty-text="请先选择字库文件或制作字库" style="flex: 1;">
            <el-table-column type="index" label="#" width="50" />

            <!-- 命名列（可编辑） -->
            <el-table-column label="命名" min-width="120">
                <template #default="scope">
                    <div v-if="scope.row.editing" style="display: flex; align-items: center;">
                        <el-input v-model="scope.row.name" size="small" @blur="handleNameBlur(scope.row)"
                            @keyup.enter="handleNameBlur(scope.row)" :ref="el => { if (el) scope.row.inputRef = el }" />
                    </div>
                    <div v-else @click="handleNameClick(scope.row)" style="cursor: pointer; padding: 5px;"
                        :title="scope.row.name">
                        {{ scope.row.name || '-' }}
                    </div>
                </template>
            </el-table-column>

            <!-- 偏色列 -->
            <el-table-column label="偏色" width="200">
                <template #default="scope">
                    <div v-if="scope.row.deviation" style="font-size: 11px; word-break: break-all;">
                        {{ scope.row.deviation.split('|').length > 1 ? `${scope.row.deviation.split('|').length}个偏色` :
                            scope.row.deviation }}
                    </div>
                    <span v-else>-</span>
                </template>
            </el-table-column>

            <!-- 尺寸信息列 -->
            <el-table-column label="尺寸" width="150">
                <template #default="scope">
                    <span>{{ scope.row.sizeInfo || '-' }}</span>
                </template>
            </el-table-column>

            <!-- 操作列 -->
            <el-table-column label="操作" width="150" fixed="right">
                <template #default="scope">
                    <el-button type="primary" size="small" link @click="handleShow(scope.row)">
                        展示
                    </el-button>
                    <el-button type="danger" size="small" link @click="handleDelete(scope.$index)">
                        删除
                    </el-button>
                </template>
            </el-table-column>
        </el-table>


        <!-- 点阵图展示区域 -->
        <div class="result-section">
            <el-image :src="matrixImageUrl" :preview-src-list="[matrixImageUrl]" fit="contain" preview-teleported
                style="height: 100%; width: 100%;">
                <template #placeholder>
                    <div style="display: flex;justify-content: center;align-items: center;height: 100%;width: 100%;">
                        点阵图预览
                    </div>
                </template>
            </el-image>
        </div>
    </div>

</template>

<script setup>
import { ref, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";

const props = defineProps({});

const selectedFileName = ref("");
const selectedFilePath = ref(""); // 保存当前选择的文件路径
const fontLibraryList = ref([]);
const fileLoading = ref(false);
const matrixImageUrl = ref(null); // 点阵图图片URL

// 处理选择文件按钮点击
const handleSelectFile = async () => {
    fileLoading.value = true;
    try {
        // 第一步：使用 Electron 的文件对话框选择文件
        const dialogResult = await ipc.invoke(ipcApiRoute.openFileDialog, {
            title: "选择字库文件",
            filters: [
                { name: "文本文件", extensions: ["txt"] },
                { name: "所有文件", extensions: ["*"] }
            ]
        });

        if (!dialogResult || !dialogResult.success || dialogResult.canceled || !dialogResult.filePath) {
            fileLoading.value = false;
            return; // 用户取消选择
        }

        const filePath = dialogResult.filePath;

        // 第二步：通过 IPC 读取文件内容
        const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
            filePath: filePath
        });

        if (!readResult || !readResult.success) {
            throw new Error(readResult?.message || "读取文件失败");
        }

        selectedFileName.value = readResult.fileName;
        selectedFilePath.value = filePath; // 保存文件路径
        const text = readResult.content;

        // 解析文件内容
        const parsedData = parseFontLibraryFile(text);

        if (parsedData.length === 0) {
            ElMessage.warning("文件中没有有效的字库数据");
            fileLoading.value = false;
            return;
        }

        // 添加到列表
        fontLibraryList.value = parsedData;
        ElMessage.success(`成功加载 ${parsedData.length} 个字库`);
    } catch (error) {
        console.error("选择或读取文件失败:", error);
        ElMessage.error("选择或读取文件失败: " + (error.message || "未知错误"));
    } finally {
        fileLoading.value = false;
    }
};

// 解析字库文件
// 格式：点阵&长,宽,点阵总数量&偏色&命名
const parseFontLibraryFile = (text) => {
    const lines = text.split('\n');
    const result = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue; // 跳过空行

        const parts = line.split('&');
        if (parts.length !== 4) {
            console.warn(`第 ${i + 1} 行格式不正确，已跳过: ${line}`);
            continue;
        }

        const [matrix, sizeInfo, deviation, name] = parts.map(p => p.trim());

        // 验证尺寸信息格式：长,宽,点阵总数量
        const sizeMatch = sizeInfo.match(/^(\d+),(\d+),(\d+)$/);
        if (!sizeMatch) {
            console.warn(`第 ${i + 1} 行尺寸信息格式不正确，已跳过: ${line}`);
            continue;
        }

        const [, width, height, totalCount] = sizeMatch;
        const sizeInfoFormatted = `${width}×${height} (${totalCount})`;

        // 从matrix还原binaryData用于显示
        const binaryData = [];
        for (let j = 0; j < matrix.length; j++) {
            const hexChar = matrix[j];
            const bits = parseInt(hexChar, 16).toString(2).padStart(4, '0');
            binaryData.push(...bits.split(''));
        }
        const totalPixels = parseInt(width) * parseInt(height);
        const pixels = binaryData.slice(0, totalPixels);

        result.push({
            id: Date.now() + i, // 生成唯一ID
            matrix: matrix,
            width: parseInt(width),
            height: parseInt(height),
            totalCount: parseInt(totalCount),
            sizeInfo: sizeInfoFormatted,
            deviation: deviation,
            name: name || `字库${i + 1}`,
            editing: false,
            binaryData: pixels // 保存二进制数据用于显示
        });
    }

    return result;
};

// 处理命名点击（进入编辑模式）
const handleNameClick = async (row) => {
    row.editing = true;
    await nextTick();
    // 聚焦到输入框并选中所有文本
    if (row.inputRef) {
        const inputEl = row.inputRef.$el?.querySelector('input') || row.inputRef.$el || row.inputRef;
        if (inputEl) {
            inputEl.focus();
            if (inputEl.select) {
                inputEl.select();
            }
        }
    }
};

// 处理命名失焦（退出编辑模式）
const handleNameBlur = (row) => {
    row.editing = false;
    // 如果名称为空，恢复默认值
    if (!row.name || !row.name.trim()) {
        row.name = `字库${fontLibraryList.value.indexOf(row) + 1}`;
    }
};

// 处理展示按钮
const handleShow = (row) => {
    // 更新点阵图显示
    if (row.binaryData) {
        generateMatrixImage(row.width, row.height, row.binaryData);
    } else if (row.matrix) {
        // 从matrix还原binaryData
        const binaryData = [];
        for (let i = 0; i < row.matrix.length; i++) {
            const hexChar = row.matrix[i];
            const bits = parseInt(hexChar, 16).toString(2).padStart(4, '0');
            binaryData.push(...bits.split(''));
        }
        const totalPixels = row.width * row.height;
        generateMatrixImage(row.width, row.height, binaryData.slice(0, totalPixels));
    }
};

// 生成点阵图
const generateMatrixImage = (width, height, pixels) => {
    // 创建canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // 设置canvas尺寸（每个像素放大显示）
    const scale = 10; // 每个像素放大10倍
    canvas.width = width * scale;
    canvas.height = height * scale;

    // 绘制背景
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 绘制每个像素
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = y * width + x;
            const pixel = pixels[index];

            if (pixel === '1') {
                ctx.fillStyle = '#000000';
            } else {
                ctx.fillStyle = '#808080';
            }

            // 绘制像素（带白色边框）
            ctx.fillRect(x * scale, y * scale, scale - 1, scale - 1);
        }
    }

    // 转换为图片URL
    matrixImageUrl.value = canvas.toDataURL('image/png');
};

// 处理删除按钮
const handleDelete = (index) => {
    fontLibraryList.value.splice(index, 1);
    ElMessage.success("已删除");
};

// 处理清空列表
const handleClearList = () => {
    if (fontLibraryList.value.length === 0) {
        ElMessage.warning("列表已为空");
        return;
    }
    fontLibraryList.value = [];
    selectedFileName.value = "";
    selectedFilePath.value = "";
    matrixImageUrl.value = null;
    ElMessage.success("已清空列表");
};

// 保存字库到文件
const saveToFile = async (fontItem) => {
    if (!selectedFilePath.value) {
        ElMessage.warning("请先选择字库文件");
        return;
    }

    try {
        // 构建字库行：点阵&长,宽,点阵总数量&偏色&命名
        const line = `${fontItem.matrix}&${fontItem.width},${fontItem.height},${fontItem.totalCount}&${fontItem.deviation}&${fontItem.name}`;

        // 读取现有文件内容
        const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
            filePath: selectedFilePath.value
        });

        let content = '';
        if (readResult && readResult.success) {
            content = readResult.content;
            // 如果文件末尾没有换行，添加换行
            if (content && !content.endsWith('\n')) {
                content += '\n';
            }
        }

        // 追加新行
        content += line + '\n';

        // 写入文件
        const writeResult = await ipc.invoke(ipcApiRoute.writeTextFile, {
            filePath: selectedFilePath.value,
            content: content
        });

        if (!writeResult || !writeResult.success) {
            throw new Error(writeResult?.message || "保存文件失败");
        }
    } catch (error) {
        console.error("保存字库到文件失败:", error);
        ElMessage.error("保存字库到文件失败: " + (error.message || "未知错误"));
        throw error;
    }
};

// 处理从 ColorSelectionTab 添加的字库项
const addFontLibraryItem = async (fontItem) => {
    // 检查是否已选择字库文件
    if (!selectedFilePath.value) {
        ElMessage.warning("请先在字库制作标签页中选择字库文件");
        return false;
    }
    
    // 检查点阵是否已存在
    const existingItem = fontLibraryList.value.find(item => item.matrix === fontItem.matrix);
    if (existingItem) {
        ElMessage.warning(`该点阵已存在，名称为：${existingItem.name}`);
        return false;
    }
    
    try {
        // 添加到列表
        fontLibraryList.value.push(fontItem);
        
        // 生成点阵图并显示
        generateMatrixImage(fontItem.width, fontItem.height, fontItem.binaryData);
        
        // 保存到文件
        await saveToFile(fontItem);
        
        // 只有在成功保存后才显示成功消息
        ElMessage.success("字库添加成功并已保存到文件");
        return true;
    } catch (error) {
        console.error("添加字库失败:", error);
        // 如果保存失败，需要从列表中移除已添加的项
        const index = fontLibraryList.value.findIndex(item => item.id === fontItem.id);
        if (index !== -1) {
            fontLibraryList.value.splice(index, 1);
        }
        ElMessage.error("添加字库失败: " + (error.message || "未知错误"));
        return false;
    }
};

// 检查是否已选择字库文件
const hasSelectedFile = () => {
    return !!selectedFilePath.value;
};

// 暴露方法供父组件调用
defineExpose({
    addFontLibraryItem,
    hasSelectedFile
});


// 获取偏色对应的颜色（从偏色字符串中提取基准色）
const getDeviationColor = (deviationStr) => {
    if (!deviationStr || !deviationStr.includes('-')) {
        return '#ffffff';
    }
    const baseHex = deviationStr.split('-')[0];
    if (baseHex && baseHex.length === 6) {
        return `#${baseHex}`;
    }
    return '#ffffff';
};

// 判断颜色是否偏白（根据亮度计算）
const isLightColor = (hex) => {
    // 移除 # 号
    hex = hex.replace("#", "");

    // 如果是3位hex，转换为6位
    if (hex.length === 3) {
        hex = hex
            .split("")
            .map((char) => char + char)
            .join("");
    }

    // 转换为 RGB
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);

    // 计算相对亮度（W3C 标准公式）
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

    // 如果亮度大于 186（约 73%），则认为偏白，使用黑色字体
    return luminance > 186;
};
</script>

<style scoped>
.el-button+.el-button {
    margin-left: 0;
}
.result-section {
    margin-top: 5px;
    flex: 1;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    /* 深色棋盘格背景，用于显示透明区域 */
    background: #1a1a2e;
    background-image: linear-gradient(45deg, #2a2a3e 25%, transparent 25%),
      linear-gradient(-45deg, #2a2a3e 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #2a2a3e 75%),
      linear-gradient(-45deg, transparent 75%, #2a2a3e 75%);
    background-size: 16px 16px;
    background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
    color: #909399;
    font-size: 12px;
  }
  
</style>
