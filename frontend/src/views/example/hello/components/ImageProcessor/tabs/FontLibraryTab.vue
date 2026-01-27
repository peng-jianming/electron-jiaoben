<template>
    <div style="display: flex; flex-direction: column; height: 590px;">
        <!-- 文件选择区域 -->
        <el-input v-model="formData.fontLibraryPath" placeholder="请选择字库文件" readonly style="margin-bottom: 5px;"
            size="small">
            <template #prepend>
                <el-button @click="handleSelectFile" :loading="fileLoading">选择字库</el-button>
            </template>
            <template #append>
                <el-button @click="handleOpenFile" :disabled="!formData.fontLibraryPath">打开字库</el-button>
            </template>
        </el-input>

        <!-- 字库列表表格 -->
        <el-table :data="fontLibraryList" height="100" border size="small" empty-text="请先选择字库文件或制作字库" style="flex: 1;">
            <el-table-column type="index" label="#" width="40" />

            <!-- 命名列（可编辑） -->
            <el-table-column label="命名">
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

            <!-- 尺寸信息列 -->
            <el-table-column label="尺寸">
                <template #default="scope">
                    <span>{{ scope.row.sizeInfo || '-' }}</span>
                </template>
            </el-table-column>

            <!-- 操作列 -->
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button type="primary" size="small" link @click="handleShow(scope.row)">
                        展示
                    </el-button>
                    <el-button type="primary" size="small" link @click="handleCopyDeviation(scope.row)">
                        复制偏色
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
import { ref, nextTick, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";

const props = defineProps({});

const formData = ref({
    fontLibraryPath: "", // 字库文件路径
});

const selectedFilePath = ref(""); // 保存当前选择的文件路径（用于内部逻辑）
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
            defaultPath: formData.value.fontLibraryPath || "",
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

        formData.value.fontLibraryPath = filePath; // 保存文件路径到表单
        selectedFilePath.value = filePath; // 保存文件路径（用于内部逻辑）
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
        
        // 保存路径配置到数据库
        await saveFontLibraryPathToDB();
    } catch (error) {
        console.error("选择或读取文件失败:", error);
        ElMessage.error("选择或读取文件失败: " + (error.message || "未知错误"));
    } finally {
        fileLoading.value = false;
    }
};

// 解析字库文件
// 新格式：点阵&长,宽,点阵总数量&偏色&命名&偏移点击区域
// 兼容旧格式：点阵&长,宽,点阵总数量&偏色&命名（偏移点击区域默认为 0,0,0,0）
const parseFontLibraryFile = (text) => {
    const lines = text.split('\n');
    const result = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue; // 跳过空行

        const parts = line.split('&');
        if (parts.length < 4 || parts.length > 5) {
            console.warn(`第 ${i + 1} 行格式不正确，已跳过: ${line}`);
            continue;
        }

        const [matrix, sizeInfo, deviation, name, offsetStr] = parts.map(p => p.trim());

        // 验证尺寸信息格式：长,宽,点阵总数量
        const sizeMatch = sizeInfo.match(/^(\d+),(\d+),(\d+)$/);
        if (!sizeMatch) {
            console.warn(`第 ${i + 1} 行尺寸信息格式不正确，已跳过: ${line}`);
            continue;
        }

        const [, width, height, totalCount] = sizeMatch;
        const sizeInfoFormatted = `${width}×${height} (${totalCount})`;

        // 偏移点击区域，旧格式没有该字段时默认 0,0,0,0
        const clickOffsetArea = (parts.length === 5 && offsetStr) ? offsetStr : "0,0,0,0";

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
            clickOffsetArea,
            binaryData: pixels // 保存二进制数据用于显示
        });
    }

    return result;
};

// 处理命名点击（进入编辑模式）
const handleNameClick = async (row) => {
    // 保存原始名称，用于后续判断是否修改
    if (!row.originalName) {
        row.originalName = row.name;
    }
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

// 更新文件中的名称
const updateNameInFile = async (row, oldName) => {
    if (!selectedFilePath.value) {
        return; // 如果没有选择文件，不需要保存
    }

    try {
        // 读取文件内容
        const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
            filePath: selectedFilePath.value
        });

        if (!readResult || !readResult.success) {
            throw new Error(readResult?.message || "读取文件失败");
        }

        let content = readResult.content;
        const lines = content.split('\n');

        // 构建要匹配的条件（使用点阵、尺寸、偏色来匹配，因为名称可能已经改变）
        // 新格式：点阵&长,宽,点阵总数量&偏色&命名&偏移点击区域
        // 兼容旧格式：点阵&长,宽,点阵总数量&偏色&命名
        const targetMatrix = row.matrix;
        const targetSizeInfo = `${row.width},${row.height},${row.totalCount}`;
        const targetDeviation = row.deviation;
        const targetClickOffsetArea = row.clickOffsetArea || "0,0,0,0";
        
        // 查找并更新匹配的行
        const updatedLines = lines.map(line => {
            const trimmedLine = line.trim();
            if (!trimmedLine) {
                return line; // 保留空行
            }

            // 解析行内容
            const parts = trimmedLine.split('&');
            if (parts.length < 4 || parts.length > 5) {
                return line; // 格式不正确的行，保持不变
            }

            const [matrix, sizeInfo, deviation, name, offsetStr] = parts.map(p => p.trim());
            
            // 精确匹配点阵、尺寸、偏色
            if (matrix === targetMatrix && 
                sizeInfo === targetSizeInfo && 
                deviation === targetDeviation) {
                // 构建新行，使用新的名称，并写入偏移点击区域（无则默认 0,0,0,0）
                const newClickOffsetArea = targetClickOffsetArea || "0,0,0,0";
                return `${row.matrix}&${row.width},${row.height},${row.totalCount}&${row.deviation}&${row.name}&${newClickOffsetArea}`;
            }
            
            return line;
        });

        // 重新组合内容
        content = updatedLines.join('\n');

        // 如果文件末尾没有换行且还有内容，添加换行
        if (content && !content.endsWith('\n') && updatedLines.length > 0) {
            content += '\n';
        }

        // 写入文件
        const writeResult = await ipc.invoke(ipcApiRoute.writeTextFile, {
            filePath: selectedFilePath.value,
            content: content
        });

        if (!writeResult || !writeResult.success) {
            throw new Error(writeResult?.message || "保存文件失败");
        }
    } catch (error) {
        console.error("更新字库名称失败:", error);
        ElMessage.error("更新字库名称失败: " + (error.message || "未知错误"));
        throw error;
    }
};

// 处理命名失焦（退出编辑模式）
const handleNameBlur = async (row) => {
    row.editing = false;
    
    // 如果名称为空，恢复默认值
    if (!row.name || !row.name.trim()) {
        row.name = `字库${fontLibraryList.value.indexOf(row) + 1}`;
    }

    // 如果名称发生了变化，保存到文件
    const oldName = row.originalName || row.name;
    if (row.name !== oldName && selectedFilePath.value) {
        try {
            await updateNameInFile(row, oldName);
            // 更新成功后，清除原始名称标记
            row.originalName = null;
            ElMessage.success("名称已保存");
        } catch (error) {
            // 如果保存失败，恢复原始名称
            row.name = oldName;
            row.originalName = null;
        }
    } else {
        // 如果没有变化，清除原始名称标记
        row.originalName = null;
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

// 处理打开字库文件
const handleOpenFile = async () => {
    if (!formData.value.fontLibraryPath) {
        ElMessage.warning("请先选择字库文件");
        return;
    }

    try {
        const result = await ipc.invoke(ipcApiRoute.openFile, {
            filePath: formData.value.fontLibraryPath
        });

        if (!result || !result.success) {
            throw new Error(result?.message || "打开文件失败");
        }

        ElMessage.success("文件已打开");
    } catch (error) {
        console.error("打开文件失败:", error);
        ElMessage.error("打开文件失败: " + (error.message || "未知错误"));
    }
};

// 处理复制偏色
const handleCopyDeviation = async (row) => {
    if (!row.deviation) {
        ElMessage.warning("该字库没有偏色信息");
        return;
    }

    try {
        // 使用 Clipboard API 复制到剪贴板
        await navigator.clipboard.writeText(row.deviation);
        ElMessage.success("偏色已复制到剪贴板");
    } catch (error) {
        console.error("复制失败:", error);
        // 如果 Clipboard API 不可用，使用备用方法
        try {
            const textArea = document.createElement('textarea');
            textArea.value = row.deviation;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            ElMessage.success("偏色已复制到剪贴板");
        } catch (fallbackError) {
            ElMessage.error("复制失败: " + (fallbackError.message || "未知错误"));
        }
    }
};

// 处理删除按钮
const handleDelete = async (index) => {
    const itemToDelete = fontLibraryList.value[index];
    if (!itemToDelete) {
        return;
    }

    // 如果已选择文件，需要从文件中删除对应的行
    if (selectedFilePath.value) {
        try {
            // 读取文件内容
            const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
                filePath: selectedFilePath.value
            });

            if (readResult && readResult.success) {
                let content = readResult.content;
                const lines = content.split('\n');

                // 过滤掉要删除的行（精确匹配字段，而不是整行字符串）
                // 新格式：点阵&长,宽,点阵总数量&偏色&命名&偏移点击区域
                // 兼容旧格式：点阵&长,宽,点阵总数量&偏色&命名
                const filteredLines = lines.filter(line => {
                    const trimmedLine = line.trim();
                    if (!trimmedLine) {
                        return true;
                    }

                    const parts = trimmedLine.split('&');
                    if (parts.length < 4 || parts.length > 5) {
                        return true;
                    }

                    const [matrix, sizeInfo, deviation, name, offsetStr] = parts.map(p => p.trim());
                    const sizeInfoExpected = `${itemToDelete.width},${itemToDelete.height},${itemToDelete.totalCount}`;
                    const clickOffsetAreaExpected = itemToDelete.clickOffsetArea || "0,0,0,0";

                    const isMatchBase =
                        matrix === itemToDelete.matrix &&
                        sizeInfo === sizeInfoExpected &&
                        deviation === itemToDelete.deviation &&
                        name === itemToDelete.name;

                    if (!isMatchBase) {
                        return true;
                    }

                    // 如果文件中没有偏移点击区域字段（旧格式），也认为匹配
                    if (parts.length === 4) {
                        return false;
                    }

                    // 有第 5 个字段时，要求偏移点击区域也一致
                    const fileOffset = offsetStr || "0,0,0,0";
                    return fileOffset !== clickOffsetAreaExpected;
                });

                // 重新组合内容
                content = filteredLines.join('\n');

                // 如果文件末尾没有换行且还有内容，添加换行
                if (content && !content.endsWith('\n') && filteredLines.length > 0) {
                    content += '\n';
                }

                // 写入文件
                const writeResult = await ipc.invoke(ipcApiRoute.writeTextFile, {
                    filePath: selectedFilePath.value,
                    content: content
                });

                if (!writeResult || !writeResult.success) {
                    throw new Error(writeResult?.message || "删除文件内容失败");
                }
            }
        } catch (error) {
            console.error("从文件中删除字库失败:", error);
            ElMessage.error("从文件中删除字库失败: " + (error.message || "未知错误"));
            return;
        }
    }

    // 从列表中删除
    fontLibraryList.value.splice(index, 1);

    // 如果删除的是当前展示的点阵图，清空展示
    if (matrixImageUrl.value && itemToDelete.matrix) {
        // 可以在这里添加逻辑来判断是否是当前展示的项
        // 暂时先不清空，让用户手动点击展示其他项
    }

    ElMessage.success("已删除");
};

// 处理清空列表
const handleClearList = () => {
    if (fontLibraryList.value.length === 0) {
        ElMessage.warning("列表已为空");
        return;
    }
    fontLibraryList.value = [];
    formData.value.fontLibraryPath = "";
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
        // 构建字库行：点阵&长,宽,点阵总数量&偏色&命名&偏移点击区域
        const clickOffsetArea = fontItem.clickOffsetArea || "0,0,0,0";
        const line = `${fontItem.matrix}&${fontItem.width},${fontItem.height},${fontItem.totalCount}&${fontItem.deviation}&${fontItem.name}&${clickOffsetArea}`;

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

// 获取字库列表
const getFontLibraryList = () => {
    return fontLibraryList.value;
};

// 保存字库路径配置到数据库
const saveFontLibraryPathToDB = async () => {
    try {
        await ipc.invoke(ipcApiRoute.savePaths, {
            fontLibraryPath: formData.value.fontLibraryPath,
        });
    } catch (error) {
        console.error("保存字库路径配置失败:", error);
        // 不显示错误提示，避免干扰用户操作
    }
};

// 从数据库加载字库路径配置
const loadFontLibraryPathFromDB = async () => {
    try {
        const result = await ipc.invoke(ipcApiRoute.getPaths);
        if (result && result.success && result.data) {
            if (result.data.fontLibraryPath) {
                formData.value.fontLibraryPath = result.data.fontLibraryPath;
                selectedFilePath.value = result.data.fontLibraryPath;
                
                // 自动加载字库文件内容
                await loadFontLibraryFile(result.data.fontLibraryPath);
            }
        }
    } catch (error) {
        console.error("加载字库路径配置失败:", error);
        // 不显示错误提示，避免干扰用户操作
    }
};

// 加载字库文件内容
const loadFontLibraryFile = async (filePath) => {
    if (!filePath) {
        return;
    }

    try {
        fileLoading.value = true;
        
        // 读取文件内容
        const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
            filePath: filePath
        });

        if (!readResult || !readResult.success) {
            // 文件可能不存在或已被删除，清空路径
            formData.value.fontLibraryPath = "";
            selectedFilePath.value = "";
            return;
        }

        const text = readResult.content;

        // 解析文件内容
        const parsedData = parseFontLibraryFile(text);

        if (parsedData.length === 0) {
            // 文件为空或格式不正确，不清空路径，只清空列表
            fontLibraryList.value = [];
            return;
        }

        // 添加到列表
        fontLibraryList.value = parsedData;
    } catch (error) {
        console.error("加载字库文件失败:", error);
        // 加载失败时不清空路径，让用户可以手动重新选择
    } finally {
        fileLoading.value = false;
    }
};

// 暴露方法供父组件调用
defineExpose({
    addFontLibraryItem,
    hasSelectedFile,
    getFontLibraryList
});

// 组件挂载时加载保存的字库路径
onMounted(() => {
    loadFontLibraryPathFromDB();
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
