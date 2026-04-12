# ConfigTab.vue 功能点备忘

> 供重构样式或调整「配置 ↔ 字库 / 图片库」命名关联时对照，避免遗漏行为。  
> 关联规则：**配置项在数据中的路径键用下划线拼接** `getPathKeys(node.path).join("_")`，与 `FontLibraryTab` 的「命名」、`ImageLibraryTab` 的「名称」一致；右侧面板 `ImageProcessorRightPanel.vue` 负责 `add-font-library` / `add-image-to-library` / `openTestByImageName` / `deleteByName`。

---

## 1. 布局与样式（当前）

- **整体**：`.config-tab-container` 纵向 flex、占满高度、背景 `#f0f2f5`、内边距约 12px；`cfg-*` + `proto-*` 对齐原型（工具栏 / 侧栏 / 分节卡片 / 按钮卡片）。
- **工具栏**：`cfg-toolbar` — **新建界面**、**选择配置**、**打开文件**、**导出 JSON**（`openSaveDialog` + `writeTextFile`）、**导入配置**（确认后替换内存中的 `data`）、**加载示例**；右侧「编辑后自动保存」徽章。
- **路径行**：圆角只读路径输入 `cfg-path-input`。
- **左侧**（`cfg-sidebar`）：标题 **「界面列表」**，项为 JSON 顶层键；副标题 **「N 按钮 · M 状态」**；每项可 **删除界面**（删顶层键）。
- **右侧主区**（当选中项为**对象**时）：**原型式结构化编辑**，整块在 **`.cfg-visual-scroll`** 内纵向滚动（与右栏 `min-height:0` 链配合，避免按钮/状态列表被裁切）：  
  - 「界面配置」卡片：界面名称只读、相似度、查找区域、误触区域。  
  - 「**滑动区域**」卡片：列出 `滑动区域` 下值为**对象**的项（起始/结束区域输入，规则同「区域」字段）；标题旁 **添加**。  
  - 「**识字区域**」卡片：列出 `识字区域` 子项；**字符串**值可编辑为 `x,y,w,h`；值为**对象**时仅提示通过「导出 JSON / 导入配置」在外部编辑；标题旁 **添加**。  
  - 「**状态属性列表**」「按钮属性列表」：与按钮对称（类型、相似度、查询范围、偏移+圈选、测试 / 制作点阵/添加图片 / 删除）；状态仅列出值为**对象**的项。  
  **未接**原型中的「界面特征图 / 本地上传」等图片能力（按此前约定保留后续再加）。
- **兜底**：`data` 存在但当前顶层键对应值不是对象时，显示说明卡片（`cfg-json-only-card`），引导导出/导入或更换为标准界面结构；**无**内嵌 JSON 树编辑器。
- **抽屉 / 弹窗**：点阵抽屉、`FontLibraryMatchDebug` 不变。
- **路径辅助**：`buildJsonPath(keys)` 与 `getPathKeys` 配套，供结构化区调用 `handleTest` / `handleAddConfig` / `handleDelete` / 偏移圈选。

---

## 2. 配置文件生命周期

- **选择 JSON**：系统对话框 → `readTextFile` → `JSON.parse` → `data`；路径写入 `configForm.configPath`，并 `ipc savePaths({ configPath })`。
- **打开文件**：`openFile` IPC。
- **启动**：`onMounted` → `loadConfigPathFromDB` → 有历史路径则 `loadConfigFile`。
- **自动保存**：`watch(data, deep)` → `autoSaveConfigFile`：整份 `JSON.stringify` 写回当前路径（失败仅 `console.error`，无成功提示）。

---

## 3. 新增配置结构

- **`handleAddSliderArea`**：`prompt` 名称 → `{ 起始区域: "", 结束区域: "" }`，名称唯一。
- **`handleAddSzArea`**：`prompt` 名称 → 新键值为 `''`。
- **`handleAddItem`**（`h()` + `ElMessageBox`）  
  - 在 **`按钮`** 下：类型 **固定区域 / 点阵 / 图片 / 彩图**。  
  - 在 **`状态`** 或根：类型 **点阵 / 图片 / 彩图**（无固定区域）。  
  - 必填 **配置名称**（JSON 的 key）。  
  - **根**下：完整壳子（`类型、查找区域、相似度、状态、按钮、滑动区域、识字区域、误触区域` 等）。  
  - **固定区域**：`固定点击区域`。  
  - **点阵/图片/彩图**：`查找区域、偏移点击区域、相似度`。

---

## 4. 「制作点阵 / 添加图片」`handleAddConfig`（命名关联核心）

- `currentName = getPathKeys(node.path).join("_")` → 字库 / 图片库 **同名关联键**。
- **`类型` 为 图片 / 彩图**：需 `currentImage.url`；`emit("add-image-to-library", { name: currentName, selectionRect, currentImageUrl })`（裁图与写 npz 在右侧面板）。
- **`类型` 为 点阵**：打开抽屉；**保留**已有颜色列表（连续制作）。

---

## 5. 抽屉：点阵制作

- **颜色**：`selectedColors` + `rowDeviations`；父组件可调暴露方法 **`addColor`**。
- **二值化预览**：`runBinarizationFromTable` — 当前图 + **左侧选区**裁切，偏色范围二值化 → `processedImageUrl`。
- **是否裁剪** `enableAutoCrop`：确认时是否对白像素做最小外接矩形。
- **偏移点击区域**：手输或圈选（第 6 节）。
- **`handleConfirmAddConfig`**：生成点阵 hex、尺寸、偏色串、可选 `clickOffsetArea`；`emit("add-font-library", fontItem, resolveCallback)`，`fontItem.name` = `currentName`。  
  - 若 **`currentName` 为空**：提示未加入字库，仍关抽屉（JSON 配置项仍存在）。

---

## 6. 偏移点击区域圈选

- 依赖 **`selectionRect`**（左侧主圈选）。
- 写回目标：**抽屉输入框** 或 **结构化表单中某路径对应的「偏移点击区域」字段**（`offsetAreaSelectionTargetNodePath` + `offsetAreaSelectionTargetMode === "json"`）。
- `emit("start-code-generator-selection", "configFontClickOffsetArea")` / `stop-code-generator-selection`。
- 父组件圈选完成后调用 **`setFontClickOffsetAreaFromSelection(rect)`**：相对主选区计算 `x,y,w,h`。

---

## 7. 测试 `handleTest`

- `name = getPathKeys(node.path).join("_")`；读取该项 `相似度`、`查找区域`。
- **图片 / 彩图**：`emit("open-image-test", { name, similarity, region, matchMode })`（彩图 `matchMode: "color"`，否则灰度）。
- **点阵等走字库**：打开 `FontLibraryMatchDebug`，传入 `initial-font-library-name` 等与 `name` 一致。

---

## 8. 删除 `handleDelete`

- 解析父对象与 key，`confirm` 后删除。
- 若 **`类型` 为 图片 / 彩图 / 点阵**：二次确认是否删资源；`emit("delete-library-resource", { type, name })`，**`name` = 全路径 `keys.join("_")`**。

---

## 9. `defineExpose`

- `addColor`  
- `setFontClickOffsetAreaFromSelection`  
- `isDrawerOpen`（父组件判断是否在点阵抽屉，例如点图取色是否记入本 Tab）

---

## 10. Props / Emits

- **Props**：`currentImage`、`selectionRect`、`fontLibraryList`、`currentDeviceId`。
- **Emits**：`start-code-generator-selection`、`stop-code-generator-selection`、`add-font-library`、`add-image-to-library`、`delete-library-resource`、`open-image-test`。

---

## 11. 脚本中暂未接模板的部分

- `cascaderOptionsKey`、`cascaderProps`、`selectedCascader`、`selectedName`：当前 **template 未使用**，可能是历史级联残留；重构时可删除或接上 UI。

## 12. 侧栏与结构化编辑

- `rootKeys` / `selectedRootKey`：同前；选中界面时 `watch` 会 **补全** `按钮、状态、滑动区域、识字区域` 的空对象，避免「添加按钮」时父级不存在。
- 结构化区直接编辑 **同一份 `data`**；命名关联规则不变（路径 `_` 拼接）。滑动/识字在结构化区的增删与 `handleAddSliderArea` / `handleAddSzArea`、`handleDeleteByPath` 一致。

---

## 13. 相关文件

- 组件：`frontend/src/views/main/components/ImageProcessor/tabs/ConfigTab.vue`
- 右侧面板：`frontend/src/views/main/components/ImageProcessor/panels/ImageProcessorRightPanel.vue`
- 字库 Tab：`FontLibraryTab.vue`（`addFontLibraryItem`、`deleteByName`）
- 图片库 Tab：`ImageLibraryTab.vue`（`openTestByImageName`、`deleteByName`、npz 路径）
