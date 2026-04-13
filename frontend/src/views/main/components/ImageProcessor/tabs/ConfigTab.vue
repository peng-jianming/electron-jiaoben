<template>
  <div class="config-tab-container">
    <!-- 文件选择区域（与字库 Tab 一致） -->
    <el-input
      v-model="configForm.configPath"
      placeholder="请选择配置 JSON 文件"
      readonly
      class="file-input"
      size="small"
    >
      <template #prepend>
        <el-button @click="handleSelectConfigFile" :loading="configFileLoading">
          选择配置
        </el-button>
      </template>
      <template #append>
        <el-button
          @click="handleOpenConfigFile"
          :disabled="!configForm.configPath"
        >
          打开配置
        </el-button>
      </template>
    </el-input>

    <div class="cfg-workspace">
      <!-- 左侧：顶层配置项（无缩略图，仅占位图标） -->
      <aside class="cfg-sidebar">
        <div class="cfg-sidebar-header">
          <span class="cfg-sidebar-title">
            <el-icon><Grid /></el-icon>
            界面列表
          </span>
          <el-button
          type="primary"
          class="cfg-toolbar-btn cfg-toolbar-btn--primary"
          size="small"
          @click="handleNewScreen"
        >
          新建界面
        </el-button>
          <!-- <span class="cfg-badge cfg-badge--muted">{{ rootKeys.length }} 个界面</span> -->
        </div>
        <div class="cfg-sidebar-list">
          <template v-if="data && rootKeys.length">
            <div
              v-for="key in rootKeys"
              :key="key"
              class="cfg-root-item"
              :class="{ 'is-active': selectedRootKey === key }"
              @click="selectedRootKey = key"
            >
              <div class="cfg-root-icon" aria-hidden="true">
                {{ rootInitial(key) }}
              </div>
              <div class="cfg-root-info">
                <div class="cfg-root-name" :title="key">{{ key }}</div>
                <div class="cfg-root-meta">
                  {{ screenButtonCount(key) }} 按钮 · {{ screenStateCount(key) }} 状态
                </div>
              </div>
            </div>
          </template>
          <div v-else class="cfg-sidebar-empty">
            <el-icon :size="28"><FolderOpened /></el-icon>
            <p>加载配置后，此处列出顶层键</p>
          </div>
        </div>
      </aside>

      <!-- 右侧：结构化配置（对齐原型） -->
      <main class="cfg-main">
        <div v-if="data && currentScreenObj" class="cfg-visual-wrap">
          <div class="cfg-visual-scroll">
            <div class="proto-section-card">
              <div class="proto-section-title proto-section-title--between">
                <span>界面配置</span>
                <div class="proto-toolbar-row">
                  <el-button
                    type="primary"
                    size="small"
                    plain
                    @click="handleTestByPath([selectedRootKey])"
                  >
                    测试
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    plain
                    @click="handleDeleteRootScreen(selectedRootKey)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
              <div class="proto-field-group">
                <div class="proto-field-label">界面名称</div>
                <el-input
                  size="small"
                  class="proto-input"
                  :model-value="selectedRootKey"
                  readonly
                />
              </div>
              <div class="proto-field-group">
                <div class="proto-field-label">界面匹配类型</div>
                <el-select
                  v-model="screenTypeModel"
                  size="small"
                  class="proto-input"
                  placeholder="选择类型"
                >
                  <el-option label="固定区域" value="固定区域" />
                  <el-option label="图片（灰度匹配）" value="图片" />
                  <el-option label="彩图（BGR 匹配）" value="彩图" />
                  <el-option label="点阵（字库匹配）" value="点阵" />
                </el-select>
                <div class="proto-feature-naming-hint">
                  界面特征仅匹配「界面名」与「界面名_数字」（如 主界面、主界面_1）；不会纳入
                  主界面_按钮_xxx 等子配置路径名。删除配置项时仍按前缀族联动删除点阵库/图片库。
                </div>
              </div>
              <div class="proto-inline-group">
                <div class="proto-inline-field">
                  <div class="proto-field-label">相似度 (0~1)</div>
                  <el-input-number
                    v-model="screenSimilarityModel"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    :precision="2"
                    size="small"
                    class="proto-input-full"
                    controls-position="right"
                    @change="onScreenSimilarityCommit"
                  />
                </div>
                <div class="proto-inline-field proto-inline-field--grow">
                  <div class="proto-field-label">查询范围（查找区域）</div>
                  <el-input
                    v-model="screenSearchRegionModel"
                    size="small"
                    class="proto-input"
                    placeholder="例如 0,0,1920,1080，留空表示不限"
                    @blur="onScreenSearchRegionBlur"
                  />
                </div>
              </div>
              <div
                v-if="currentScreenObj && Object.prototype.hasOwnProperty.call(currentScreenObj, '误触区域')"
                class="proto-field-group"
              >
                <div class="proto-field-label">误触区域</div>
                <el-input
                  v-model="screenAvoidRegionModel"
                  size="small"
                  class="proto-input"
                  placeholder="x,y,w,h，可留空"
                  @blur="onScreenAvoidRegionBlur"
                />
              </div>
            </div>


            <div class="proto-section-card">
              <div class="proto-section-title proto-section-title--between">
                <span>特征列表</span>
                <el-button
                  type="success"
                  size="small"
                  class="proto-add-btn"
                  @click="
                    handleAddConfig({
                      path: buildJsonPath([selectedRootKey]),
                    })
                  "
                >
                  <el-icon><Plus /></el-icon>
                  制作点阵/添加图片
                </el-button>
              </div>
              <template v-if="screenFeatureItems.length">
                <div class="proto-feature-grid">
                  <div
                    v-for="item in screenFeatureItems"
                    :key="item.kind + '-' + item.name"
                    class="proto-feature-cell"
                  >
                    <div class="proto-feature-thumb-wrap">
                      <el-image
                        v-if="item.previewUrl"
                        :src="item.previewUrl"
                        fit="contain"
                        class="proto-feature-thumb"
                        :preview-src-list="[item.previewUrl]"
                        preview-teleported
                      />
                      <div
                        v-else
                        class="proto-feature-thumb proto-feature-thumb--empty"
                      >
                        无预览
                      </div>
                      <div class="proto-feature-actions">
                        <el-button
                          type="primary"
                          link
                          size="small"
                          class="proto-feature-action-btn"
                          @click="handleScreenLevelFeatureTest(item)"
                        >
                          测试
                        </el-button>
                        <el-button
                          type="danger"
                          link
                          size="small"
                          class="proto-feature-action-btn"
                          @click="handleScreenFeatureDelete(item)"
                        >
                          删除
                        </el-button>
                      </div>
                    </div>
                    <div class="proto-feature-name" :title="item.name">
                      {{ item.name }}
                    </div>
                  </div>
                </div>
              </template>
              <div v-else class="proto-empty-hint">
                <template v-if="screenFeatureMode === 'font'">
                  暂无点阵。可点击「制作点阵/添加图片」，或在点阵库中使用与界面同名、或「界面名_序号」命名。
                </template>
                <template v-else-if="screenFeatureMode === 'image'">
                  暂无图片。可点击「制作点阵/添加图片」，或在图片库中使用与界面同名、或「界面名_序号」命名。
                </template>
                <template v-else>
                  当前界面类型为「{{ currentScreenObj?.类型 ?? "-" }}」，仅 图片 / 彩图 / 点阵
                  会在此列出特征。
                </template>
              </div>
            </div>


            <!-- 滑动区域：子项为 { 起始区域, 结束区域 } -->
            <div class="proto-section-card">
              <div class="proto-section-title proto-section-title--between">
                <span>滑动区域列表</span>
                <el-button
                  type="success"
                  size="small"
                  class="proto-add-btn"
                  @click="
                    handleAddSliderArea({
                      path: buildJsonPath([selectedRootKey, '滑动区域']),
                    })
                  "
                >
                  <el-icon><Plus /></el-icon>
                  添加滑动区域
                </el-button>
              </div>
              <template v-if="sliderEntriesForScreen.length">
                <div
                  v-for="[slName, sl] in sliderEntriesForScreen"
                  :key="'sl-' + slName"
                  class="proto-button-card"
                >
                  <div class="proto-button-header">
                    <span class="proto-button-name">{{ slName }}</span>
                    <el-button
                      type="danger"
                      size="small"
                      link
                      @click="handleDeleteByPath(buildPathKeysForSlider(slName))"
                    >
                      删除
                    </el-button>
                  </div>
                  <div class="proto-inline-group">
                    <div class="proto-inline-field proto-inline-field--grow">
                      <div class="proto-field-label">起始区域</div>
                      <el-input
                        v-model="sl.起始区域"
                        size="small"
                        class="proto-input"
                        placeholder="x,y,w,h"
                        @blur="
                          onSliderEndpointBlur(
                            slName,
                            '起始区域',
                            sl.起始区域
                          )
                        "
                      />
                    </div>
                    <div class="proto-inline-field proto-inline-field--grow">
                      <div class="proto-field-label">结束区域</div>
                      <el-input
                        v-model="sl.结束区域"
                        size="small"
                        class="proto-input"
                        placeholder="x,y,w,h"
                        @blur="
                          onSliderEndpointBlur(slName, '结束区域', sl.结束区域)
                        "
                      />
                    </div>
                  </div>
                </div>
              </template>
              <div v-else class="proto-empty-hint">
                暂无滑动区域，点击「添加滑动区域」
              </div>
            </div>

            <!-- 识字区域：常见为「名称 → 区域字符串」；嵌套对象需导出 JSON 在外部编辑 -->
            <div class="proto-section-card">
              <div class="proto-section-title proto-section-title--between">
                <span>识字区域列表</span>
                <el-button
                  type="success"
                  size="small"
                  class="proto-add-btn"
                  @click="
                    handleAddSzArea({
                      path: buildJsonPath([selectedRootKey, '识字区域']),
                    })
                  "
                >
                  <el-icon><Plus /></el-icon>
                  添加识字区域
                </el-button>
              </div>
              <template v-if="szEntriesForScreen.length">
                <div
                  v-for="[zn, zv] in szEntriesForScreen"
                  :key="'sz-' + zn"
                  class="proto-button-card"
                >
                  <div class="proto-button-header">
                    <span class="proto-button-name">{{ zn }}</span>
                    <el-button
                      type="danger"
                      size="small"
                      link
                      @click="handleDeleteByPath(buildPathKeysForSz(zn))"
                    >
                      删除
                    </el-button>
                  </div>
                  <template v-if="typeof zv === 'string'">
                    <div class="proto-field-label">区域 / 内容（x,y,w,h）</div>
                    <el-input
                      :model-value="zv"
                      size="small"
                      class="proto-input"
                      placeholder="例如 270,85,155,37"
                      @update:model-value="(v) => setSzEntryString(zn, v)"
                      @blur="onSzStringBlur(zn)"
                    />
                  </template>
                  <div v-else class="proto-sz-object-hint">
                    当前为嵌套对象，请使用「导出 JSON」编辑后「导入配置」
                  </div>
                </div>
              </template>
              <div v-else class="proto-empty-hint">
                暂无识字区域，点击「添加识字区域」
              </div>
            </div>

            <div class="proto-section-card">
              <div class="proto-section-title proto-section-title--between">
                <span>状态属性列表</span>
                <el-button
                  type="success"
                  size="small"
                  class="proto-add-btn"
                  @click="handleAddItem({ path: buildJsonPath([selectedRootKey, '状态']) })"
                >
                  <el-icon><Plus /></el-icon>
                  添加状态
                </el-button>
              </div>
              <template v-if="stateEntriesForScreen.length">
                <div
                  v-for="[stName, st] in stateEntriesForScreen"
                  :key="'st-' + stName"
                  class="proto-button-card"
                >
                  <div class="proto-button-header">
                    <span class="proto-button-name">{{ stName }}</span>
                    <div class="proto-button-actions">
                      <el-button
                        type="primary"
                        size="small"
                        link
                        @click="handleTestByPath(buildPathKeysForState(stName))"
                      >
                        测试
                      </el-button>
                     
                      <el-button
                        type="danger"
                        size="small"
                        link
                        @click="handleDeleteByPath(buildPathKeysForState(stName))"
                      >
                        删除
                      </el-button>
                    </div>
                  </div>
                  <template v-if="isFixedAreaType(st?.类型)">
                    <div class="proto-field-group">
                      <div class="proto-field-label">固定点击区域</div>
                      <el-input
                        v-model="st.固定点击区域"
                        size="small"
                        class="proto-input"
                        @blur="onStateFieldBlur(stName, '固定点击区域', st.固定点击区域)"
                      />
                    </div>
                  </template>
                  <template v-else>
                    <div class="proto-field-row">
                      <span class="proto-mini-label">类型</span>
                      <span class="proto-type-tag">{{ st?.类型 ?? "-" }}</span>
                    </div>
                    <div class="proto-inline-group">
                      <div class="proto-inline-field">
                        <div class="proto-field-label">相似度</div>
                        <el-input-number
                          :model-value="Number(st?.相似度 ?? 0.9)"
                          :min="0"
                          :max="1"
                          :step="0.01"
                          :precision="2"
                          size="small"
                          class="proto-input-full"
                          controls-position="right"
                          @change="(v) => onStateSimilarityCommit(stName, v)"
                        />
                      </div>
                      <div class="proto-inline-field proto-inline-field--grow">
                        <div class="proto-field-label">查询范围</div>
                        <el-input
                          v-model="st.查找区域"
                          size="small"
                          class="proto-input"
                          @blur="onStateFieldBlur(stName, '查找区域', st.查找区域)"
                        />
                      </div>
                    </div>
                    <div class="proto-field-group">
                    <div class="proto-field-label">
                    <div>特征列表</div>
                      <el-button
                        type="primary"
                        size="small"
                        link
                        @click="handleAddConfigByPath(buildPathKeysForState(stName))"
                      >
                        制作点阵/添加图片
                      </el-button>
                    </div>
                    <template v-if="getStateFeatureItems(stName).length">
                      <div class="proto-feature-grid">
                        <div
                          v-for="item in getStateFeatureItems(stName)"
                          :key="item.kind + '-' + item.name"
                          class="proto-feature-cell"
                        >
                          <div class="proto-feature-thumb-wrap">
                            <el-image
                              v-if="item.previewUrl"
                              :src="item.previewUrl"
                              fit="contain"
                              class="proto-feature-thumb"
                              :preview-src-list="[item.previewUrl]"
                              preview-teleported
                            />
                            <div
                              v-else
                              class="proto-feature-thumb proto-feature-thumb--empty"
                            >
                              无预览
                            </div>
                            <div class="proto-feature-actions">
                              <el-button
                                type="primary"
                                link
                                size="small"
                                class="proto-feature-action-btn"
                                @click="handleNodeLevelFeatureTest(item, st)"
                              >
                                测试
                              </el-button>
                              <el-button
                                type="danger"
                                link
                                size="small"
                                class="proto-feature-action-btn"
                                @click="handleNodeFeatureDelete(item, st)"
                              >
                                删除
                              </el-button>
                            </div>
                          </div>
                          <div class="proto-feature-name" :title="item.name">
                            {{ item.name }}
                          </div>
                        </div>
                      </div>
                    </template>
                    <div v-else class="proto-empty-hint">
                      <template v-if="resolveFeatureModeByType(st?.类型) === 'font'">
                        暂无点阵，可点击上方「制作点阵/添加图片」后在此查看。
                      </template>
                      <template v-else-if="resolveFeatureModeByType(st?.类型) === 'image'">
                        暂无图片，可点击上方「制作点阵/添加图片」后在此查看。
                      </template>
                      <template v-else>
                        当前类型为「{{ st?.类型 ?? "-" }}」，仅 图片 / 彩图 / 点阵
                        会在此列出特征。
                      </template>
                    </div>
                    </div>
                  </template>
                </div>
              </template>
              <div v-else class="proto-empty-hint">暂无状态，点击「添加状态」</div>
            </div>

            <div class="proto-section-card">
              <div class="proto-section-title proto-section-title--between">
                <span>按钮属性列表</span>
                <el-button
                  type="success"
                  size="small"
                  class="proto-add-btn"
                  @click="handleAddItem({ path: buildJsonPath([selectedRootKey, '按钮']) })"
                >
                  <el-icon><Plus /></el-icon>
                  添加按钮
                </el-button>
              </div>
              <template v-if="buttonEntriesForScreen.length">
                <div
                  v-for="[btnName, btn] in buttonEntriesForScreen"
                  :key="btnName"
                  class="proto-button-card"
                >
                  <div class="proto-button-header">
                    <span class="proto-button-name">{{ btnName }}</span>
                    <div class="proto-button-actions">
                      <el-button
                        type="primary"
                        size="small"
                        link
                        @click="handleTestByPath(buildPathKeysForButton(btnName))"
                      >
                        测试
                      </el-button>
                      
                      <el-button
                        type="danger"
                        size="small"
                        link
                        @click="handleDeleteByPath(buildPathKeysForButton(btnName))"
                      >
                        删除
                      </el-button>
                    </div>
                  </div>
                  <template v-if="isFixedAreaType(btn?.类型)">
                    <div class="proto-field-group">
                      <div class="proto-field-label">固定点击区域</div>
                      <el-input
                        v-model="btn.固定点击区域"
                        size="small"
                        class="proto-input"
                        @blur="onButtonFieldBlur(btnName, '固定点击区域', btn.固定点击区域)"
                      />
                    </div>
                  </template>
                  <template v-else>
                    <div class="proto-field-row">
                      <span class="proto-mini-label">类型</span>
                      <span class="proto-type-tag">{{ btn?.类型 ?? "-" }}</span>
                    </div>
                    <div class="proto-inline-group">
                      <div class="proto-inline-field">
                        <div class="proto-field-label">相似度</div>
                        <el-input-number
                          :model-value="Number(btn?.相似度 ?? 0.9)"
                          :min="0"
                          :max="1"
                          :step="0.01"
                          :precision="2"
                          size="small"
                          class="proto-input-full"
                          controls-position="right"
                          @change="(v) => onButtonSimilarityCommit(btnName, v)"
                        />
                      </div>
                      <div class="proto-inline-field proto-inline-field--grow">
                        <div class="proto-field-label">查询范围</div>
                        <el-input
                          v-model="btn.查找区域"
                          size="small"
                          class="proto-input"
                          @blur="onButtonFieldBlur(btnName, '查找区域', btn.查找区域)"
                        />
                      </div>
                    </div>
                    <div class="proto-field-group">
                    <div class="proto-field-label"><div>特征列表</div> <el-button
                        type="primary"
                        size="small"
                        link
                        @click="handleAddConfigByPath(buildPathKeysForButton(btnName))"
                      >
                        制作点阵/添加图片
                      </el-button></div>
                    <template v-if="getButtonFeatureItems(btnName).length">
                      <div class="proto-feature-grid">
                        <div
                          v-for="item in getButtonFeatureItems(btnName)"
                          :key="item.kind + '-' + item.name"
                          class="proto-feature-cell"
                        >
                          <div class="proto-feature-thumb-wrap">
                            <el-image
                              v-if="item.previewUrl"
                              :src="item.previewUrl"
                              fit="contain"
                              class="proto-feature-thumb"
                              :preview-src-list="[item.previewUrl]"
                              preview-teleported
                            />
                            <div
                              v-else
                              class="proto-feature-thumb proto-feature-thumb--empty"
                            >
                              无预览
                            </div>
                            <div class="proto-feature-actions">
                              <el-button
                                type="primary"
                                link
                                size="small"
                                class="proto-feature-action-btn"
                                @click="handleNodeLevelFeatureTest(item, btn)"
                              >
                                测试
                              </el-button>
                              <el-button
                                type="danger"
                                link
                                size="small"
                                class="proto-feature-action-btn"
                                @click="handleNodeFeatureDelete(item, btn)"
                              >
                                删除
                              </el-button>
                            </div>
                          </div>
                          <div class="proto-feature-name" :title="item.name">
                            {{ item.name }}
                          </div>
                        </div>
                      </div>
                    </template>
                    <div v-else class="proto-empty-hint">
                      <template v-if="resolveFeatureModeByType(btn?.类型) === 'font'">
                        暂无点阵，可点击上方「制作点阵/添加图片」后在此查看。
                      </template>
                      <template v-else-if="resolveFeatureModeByType(btn?.类型) === 'image'">
                        暂无图片，可点击上方「制作点阵/添加图片」后在此查看。
                      </template>
                      <template v-else>
                        当前类型为「{{ btn?.类型 ?? "-" }}」，仅 图片 / 彩图 / 点阵
                        会在此列出特征。
                      </template>
                    </div>
                    </div>
                  </template>
                </div>
              </template>
              <div v-else class="proto-empty-hint">暂无按钮，点击「添加按钮」</div>
            </div>
          </div>
        </div>
        <div v-else-if="data" class="cfg-json-only-card">
          <div class="cfg-section-title">当前项无法结构化编辑</div>
          <p class="proto-json-only-hint">
            选中的顶层键不是对象，或结构与标准「界面」不一致。请使用「导出 JSON」在外部修改后「导入配置」，或更换为可解析的界面配置。
          </p>
        </div>
        <div v-else class="cfg-empty-state">
          <el-icon class="cfg-empty-icon"><FolderOpened /></el-icon>
          <p>请选择 JSON 配置文件</p>
          <p class="cfg-empty-sub">支持界面、按钮、状态等结构化编辑</p>
        </div>
      </main>
    </div>

    <!-- 测试弹框：按当前配置项名称（点阵名）查询所有同名点阵进行找字测试 -->
    <el-dialog
      v-model="testDialogVisible"
      title="找字测试"
      width="420px"
      destroy-on-close
      :close-on-click-modal="false"
      class="config-test-dialog"
      @closed="onTestDialogClosed"
    >
      <FontLibraryMatchDebug
        v-if="testDialogVisible"
        :current-device-id="currentDeviceId"
        :font-library-list="fontLibraryList"
        :initial-font-library-name="testFontLibraryName"
        :initial-similarity="testSimilarity"
        :initial-region="testRegion"
      />
    </el-dialog>

    <transition name="config-drawer-slide">
      <div v-if="drawer" class="config-drawer-wrapper">
        <div class="config-drawer-mask" @click="drawer = false"></div>
        <div class="config-drawer">
          <div class="config-drawer-header">
            <div class="config-drawer-title-wrap">
              <div class="config-drawer-title-main">
                <span class="config-drawer-title">添加字库配置</span>
              </div>
              <div class="config-drawer-subtitle">
                基于当前图片与圈选区域生成字库点阵配置
              </div>
            </div>
            <el-button
              class="cfg-toolbar-btn cfg-toolbar-btn--outline"
              size="small"
              @click="drawer = false"
            >
              关闭
            </el-button>
          </div>
          <div class="config-drawer-body">
            <!-- 颜色表格 -->
            <div class="color-table-wrap">
              <el-table
                :data="selectedColors"
                height="150"
                size="small"
                empty-text="请在图片上点击选取颜色"
                :header-cell-style="{
                  background: '#f8fafc',
                  color: '#64748b',
                  fontSize: '11px',
                  fontWeight: 600,
                  borderBottom: '1px solid #e2e8f0',
                }"
                :cell-style="{ fontSize: '12px', padding: '4px 0' }"
                :row-style="{ transition: 'background 0.15s' }"
              >
                <el-table-column label="HEX" width="84">
                  <template #default="scope">
                    <div
                      class="hex-cell"
                      :style="{
                        backgroundColor:
                          '#' + String(scope.row.hex || '').replace(/^#/, ''),
                        color: isLightColor(scope.row.hex) ? '#1e293b' : '#f8fafc',
                      }"
                    >
                      {{ scope.row.hex }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="偏色" min-width="120">
                  <template #default="scope">
                    <div class="slider-cell">
                      <el-slider
                        :model-value="getRowDeviation(scope.$index)"
                        :min="0"
                        :max="100"
                        :show-tooltip="true"
                        @update:model-value="(v) => setRowDeviation(scope.$index, v)"
                      />
                      <span class="slider-value">{{
                        getRowDeviation(scope.$index)
                      }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="" width="40" fixed="right">
                  <template #default="scope">
                    <el-button
                      type="danger"
                      link
                      size="small"
                      @click="handleRemoveColor(scope.$index)"
                      class="delete-btn"
                    >
                      <el-icon>
                        <Close />
                      </el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="table-footer">
                <span class="table-count">{{ selectedColors.length }} 个颜色</span>
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="handleClearAllColors"
                  :disabled="!selectedColors.length"
                  >清空</el-button
                >
              </div>
            </div>

            <!-- 二值化预览 -->
            <div class="result-section">
              <el-image
                v-if="processedImageUrl"
                :src="processedImageUrl"
                :preview-src-list="[processedImageUrl]"
                fit="contain"
                preview-teleported
                style="height: 100%; width: 100%"
              />
              <div v-else class="result-placeholder">
                <el-icon :size="20" style="opacity: 0.3; margin-bottom: 4px">
                  <Picture />
                </el-icon>
                偏色二值化预览
              </div>
            </div>

            <div class="font-config-section">
              <div class="font-row">
                <span class="font-label">是否裁剪</span>
                <div class="font-field">
                  <el-checkbox v-model="enableAutoCrop" size="small" />
                </div>
              </div>
              <div class="font-row">
                <span class="font-label">偏移点击区域</span>
                <div class="font-field">
                  <el-input
                    v-model="fontClickOffsetAreaInput"
                    placeholder="偏移点击区域 x,y,w,h（可选）"
                    size="small"
                    clearable
                  >
                    <template #append>
                      <el-button
                        :type="
                          isDrawerFontClickOffsetAreaSelectionActive
                            ? 'warning'
                            : 'primary'
                        "
                        :disabled="!hasSelectionRect"
                        size="small"
                        @click="toggleFontClickOffsetAreaSelection"
                      >
                        {{
                          isDrawerFontClickOffsetAreaSelectionActive ? "取消" : "圈选"
                        }}
                      </el-button>
                    </template>
                  </el-input>
                </div>
              </div>
            </div>
          </div>
          <div class="config-drawer-footer">
            <el-button
              type="primary"
              size="small"
              @click="handleConfirmAddConfig"
              :disabled="!processedImageUrl"
            >
              确认添加
            </el-button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed, h } from "vue";
import {
  ElMessage,
  ElMessageBox,
  ElInput,
  ElCheckbox,
  ElRadio,
  ElRadioGroup,
  ElSelect,
  ElOption,
} from "element-plus";
import {
  Close,
  Picture,
  FolderOpened,
  Grid,
  Plus,
  Delete,
} from "@element-plus/icons-vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import FontLibraryMatchDebug from "./FontLibraryMatchDebug.vue";
const props = defineProps({
  currentImage: {
    type: Object,
    default: null,
  },
  selectionRect: {
    type: Object,
    default: null,
  },
  fontLibraryList: {
    type: Array,
    default: () => [],
  },
  imageLibraryList: {
    type: Array,
    default: () => [],
  },
  currentDeviceId: {
    type: String,
    default: "",
  },
});

const testDialogVisible = ref(false);
const testFontLibraryName = ref("");
const testSimilarity = ref(undefined);
const testRegion = ref("");

const emit = defineEmits([
  "start-code-generator-selection",
  "stop-code-generator-selection",
  "add-font-library",
  "add-image-to-library",
  "delete-library-resource",
  "open-image-test",
]);

const data = ref(undefined);

/** 左侧列表：配置 JSON 顶层键（排序展示，无缩略图） */
const rootKeys = computed(() => {
  const d = data.value;
  if (d == null || typeof d !== "object" || Array.isArray(d)) return [];
  return Object.keys(d).sort();
});

const selectedRootKey = ref(null);

watch(
  rootKeys,
  (keys) => {
    if (!keys.length) {
      selectedRootKey.value = null;
      return;
    }
    if (
      selectedRootKey.value == null ||
      !keys.includes(selectedRootKey.value)
    ) {
      selectedRootKey.value = keys[0];
    }
  },
  { immediate: true }
);

const rootInitial = (key) => {
  const s = String(key || "").trim();
  return s ? s.charAt(0).toUpperCase() : "?";
};

const rootChildCount = (key) => {
  const d = data.value?.[key];
  if (d != null && typeof d === "object" && !Array.isArray(d)) {
    return Object.keys(d).length;
  }
  return 0;
};

/** 供结构化编辑 / 圈选写回使用的路径串，与 getPathKeys 互逆 */
const buildJsonPath = (keys) => {
  if (!keys || !keys.length) return "root";
  return (
    "root" +
    keys
      .map((k) => {
        const s = String(k);
        const escaped = s.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
        return `["${escaped}"]`;
      })
      .join("")
  );
};

const currentScreenObj = computed(() => {
  const k = selectedRootKey.value;
  if (!k || !data.value) return null;
  const s = data.value[k];
  if (s != null && typeof s === "object" && !Array.isArray(s)) return s;
  return null;
});

const buttonEntriesForScreen = computed(() => {
  const s = currentScreenObj.value;
  const b = s?.按钮;
  if (!b || typeof b !== "object" || Array.isArray(b)) return [];
  return Object.keys(b)
    .sort()
    .map((k) => [k, b[k]])
    .filter(
      ([, v]) => v != null && typeof v === "object" && !Array.isArray(v)
    );
});

/** 与按钮列表一致：仅展示值为「普通对象」的状态项（排除字符串坐标等） */
const stateEntriesForScreen = computed(() => {
  const s = currentScreenObj.value;
  const st = s?.状态;
  if (!st || typeof st !== "object" || Array.isArray(st)) return [];
  return Object.keys(st)
    .sort()
    .map((k) => [k, st[k]])
    .filter(
      ([, v]) => v != null && typeof v === "object" && !Array.isArray(v)
    );
});

const screenButtonCount = (screenKey) => {
  const b = data.value?.[screenKey]?.按钮;
  if (!b || typeof b !== "object" || Array.isArray(b)) return 0;
  return Object.keys(b).length;
};

const screenStateCount = (screenKey) => {
  const st = data.value?.[screenKey]?.状态;
  if (!st || typeof st !== "object" || Array.isArray(st)) return 0;
  return Object.keys(st).length;
};

const buildPathKeysForButton = (btnName, tail) => {
  const sk = selectedRootKey.value;
  const base = [sk, "按钮", btnName];
  return tail ? [...base, tail] : base;
};

const buildPathKeysForState = (stateName, tail) => {
  const sk = selectedRootKey.value;
  const base = [sk, "状态", stateName];
  return tail ? [...base, tail] : base;
};

const buildPathKeysForSlider = (sliderName) => {
  const sk = selectedRootKey.value;
  return [sk, "滑动区域", sliderName];
};

const buildPathKeysForSz = (entryName) => {
  const sk = selectedRootKey.value;
  return [sk, "识字区域", entryName];
};

/** 滑动区域子项：值为含 起始区域/结束区域 的对象 */
const sliderEntriesForScreen = computed(() => {
  const s = currentScreenObj.value?.滑动区域;
  if (!s || typeof s !== "object" || Array.isArray(s)) return [];
  return Object.keys(s)
    .sort()
    .map((k) => [k, s[k]])
    .filter(
      ([, v]) => v != null && typeof v === "object" && !Array.isArray(v)
    );
});

/** 识字区域：键值对（字符串可编辑；嵌套对象仅提示导出编辑） */
const szEntriesForScreen = computed(() => {
  const z = currentScreenObj.value?.识字区域;
  if (!z || typeof z !== "object" || Array.isArray(z)) return [];
  return Object.keys(z)
    .sort()
    .map((k) => [k, z[k]]);
});

const onSliderEndpointBlur = (sliderName, fieldKey, raw) => {
  const sl = currentScreenObj.value?.滑动区域?.[sliderName];
  if (!sl || typeof sl !== "object") return;
  const trimmed = raw == null ? "" : String(raw).trim();
  if (trimmed === "") {
    sl[fieldKey] = "";
    return;
  }
  if (!validateRegionLike(trimmed, fieldKey)) {
    sl[fieldKey] = "";
    return;
  }
  sl[fieldKey] = trimmed;
};

const setSzEntryString = (zn, v) => {
  const z = currentScreenObj.value?.识字区域;
  if (!z) return;
  z[zn] = v;
};

const onSzStringBlur = (zn) => {
  const z = currentScreenObj.value?.识字区域;
  if (!z) return;
  const raw = z[zn];
  if (typeof raw !== "string") return;
  const trimmed = raw.trim();
  if (trimmed === "") return;
  if (!validateRegionLike(trimmed, "识字区域")) {
    z[zn] = "";
  }
};

const screenSimilarityModel = computed({
  get() {
    const s = currentScreenObj.value;
    if (!s) return 0.9;
    const v = Number(s.相似度);
    return Number.isFinite(v) ? v : 0.9;
  },
  set(v) {
    const s = currentScreenObj.value;
    if (s) s.相似度 = v;
  },
});

const screenSearchRegionModel = computed({
  get() {
    const s = currentScreenObj.value;
    return s?.查找区域 != null ? String(s.查找区域) : "";
  },
  set(v) {
    const s = currentScreenObj.value;
    if (s) s.查找区域 = v;
  },
});

const screenAvoidRegionModel = computed({
  get() {
    const s = currentScreenObj.value;
    return s?.误触区域 != null ? String(s.误触区域) : "";
  },
  set(v) {
    const s = currentScreenObj.value;
    if (s) s.误触区域 = v;
  },
});

/**
 * 界面级特征命名：仅「界面名」或「界面名_纯数字」（如 主界面、主界面_1）。
 * 排除 主界面_按钮_xxx 等配置路径型名称。
 */
const featureNameBelongsToBase = (itemName, baseName) => {
  const n = (itemName || "").trim();
  const t = String(baseName || "").trim();
  if (!t || !n) return false;
  if (n === t) return true;
  const prefix = `${t}_`;
  if (!n.startsWith(prefix)) return false;
  const rest = n.slice(prefix.length);
  return /^\d+$/.test(rest);
};

const fontMatrixRowToDataUrl = (row, scale = 4) => {
  if (!row) return "";
  const w = Number(row.width);
  const h = Number(row.height);
  if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) return "";
  let pixels = row.binaryData;
  if (!pixels || !pixels.length) {
    const matrix = row.matrix;
    if (!matrix || typeof matrix !== "string") return "";
    const binaryData = [];
    for (let i = 0; i < matrix.length; i++) {
      const hexChar = matrix[i];
      const bits = parseInt(hexChar, 16).toString(2).padStart(4, "0");
      binaryData.push(...bits.split(""));
    }
    pixels = binaryData.slice(0, w * h);
  }
  if (!pixels || pixels.length < w * h) return "";
  try {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";
    canvas.width = w * scale;
    canvas.height = h * scale;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const idx = y * w + x;
        const pixel = pixels[idx];
        ctx.fillStyle = pixel === "1" || pixel === 1 ? "#000000" : "#808080";
        ctx.fillRect(x * scale, y * scale, Math.max(1, scale - 1), Math.max(1, scale - 1));
      }
    }
    return canvas.toDataURL("image/png");
  } catch {
    return "";
  }
};

const featureNumericSuffix = (name, baseName) => {
  const n = name || "";
  const base = baseName || "";
  const prefix = `${base}_`;
  if (!n.startsWith(prefix)) return null;
  const rest = n.slice(prefix.length);
  if (!/^\d+$/.test(rest)) return null;
  return parseInt(rest, 10);
};

const sortFeatureRowsByBase = (rows, baseName) =>
  [...rows].sort((a, b) => {
    const an = a.name || "";
    const bn = b.name || "";
    if (an === baseName && bn !== baseName) return -1;
    if (bn === baseName && an !== baseName) return 1;
    const na = featureNumericSuffix(an, baseName);
    const nb = featureNumericSuffix(bn, baseName);
    if (na != null && nb != null) return na - nb;
    return an.localeCompare(bn, "zh-CN");
  });

const ALLOWED_CONFIG_TYPES = new Set(["固定区域", "图片", "点阵", "彩图"]);
const normalizeConfigType = (t, fallback = "图片") => {
  const typeText = String(t ?? "").replace(/\s+/g, "");
  if (typeText === "字库") return "点阵";
  if (typeText === "按钮(固定区域)" || typeText === "按钮固定区域") return "固定区域";
  if (ALLOWED_CONFIG_TYPES.has(typeText)) return typeText;
  return fallback;
};

const screenTypeModel = computed({
  get() {
    const s = currentScreenObj.value;
    return normalizeConfigType(s?.类型, "图片");
  },
  set(val) {
    const s = currentScreenObj.value;
    if (s) s.类型 = normalizeConfigType(val, "图片");
  },
});

const screenFeatureMode = computed(() => {
  const t = normalizeConfigType(currentScreenObj.value?.类型, "图片");
  if (t === "点阵") return "font";
  if (t === "图片" || t === "彩图") return "image";
  return "none";
});

const resolveFeatureModeByType = (t) => {
  const normalizedType = normalizeConfigType(t, "图片");
  if (normalizedType === "点阵") return "font";
  if (normalizedType === "图片" || normalizedType === "彩图") return "image";
  return "none";
};

const isFixedAreaType = (t) => {
  return normalizeConfigType(t, "") === "固定区域";
};

const collectFeatureItemsByBase = (baseName, mode) => {
  if (!baseName || mode === "none") return [];
  if (mode === "font") {
    const list = Array.isArray(props.fontLibraryList) ? props.fontLibraryList : [];
    const matched = list.filter((row) =>
      featureNameBelongsToBase(row.name, baseName)
    );
    return sortFeatureRowsByBase(matched, baseName).map((row) => ({
      kind: "font",
      id: row.id,
      name: row.name,
      previewUrl: fontMatrixRowToDataUrl(row),
    }));
  }
  const list = Array.isArray(props.imageLibraryList) ? props.imageLibraryList : [];
  const matched = list.filter((item) =>
    featureNameBelongsToBase(item.name, baseName)
  );
  return sortFeatureRowsByBase(matched, baseName).map((item) => ({
    kind: "image",
    id: item.id,
    name: item.name,
    previewUrl: item.thumbUrl || item.fullUrl || "",
  }));
};

const screenFeatureItems = computed(() => {
  const sk = selectedRootKey.value;
  const mode = screenFeatureMode.value;
  if (!sk) return [];
  return collectFeatureItemsByBase(sk, mode);
});

const buttonFeatureItemMap = computed(() => {
  const sk = selectedRootKey.value;
  if (!sk) return {};
  return buttonEntriesForScreen.value.reduce((acc, [btnName, btn]) => {
    const mode = resolveFeatureModeByType(btn?.类型);
    acc[btnName] = collectFeatureItemsByBase(`${sk}_按钮_${btnName}`, mode);
    return acc;
  }, {});
});

const stateFeatureItemMap = computed(() => {
  const sk = selectedRootKey.value;
  if (!sk) return {};
  return stateEntriesForScreen.value.reduce((acc, [stateName, st]) => {
    const mode = resolveFeatureModeByType(st?.类型);
    acc[stateName] = collectFeatureItemsByBase(`${sk}_状态_${stateName}`, mode);
    return acc;
  }, {});
});

const getButtonFeatureItems = (btnName) => buttonFeatureItemMap.value?.[btnName] || [];
const getStateFeatureItems = (stateName) => stateFeatureItemMap.value?.[stateName] || [];

/** 特征列表中单张测试：使用当前界面的相似度、查找区域 */
const handleScreenLevelFeatureTest = (item) => {
  const s = currentScreenObj.value;
  if (!s || !item?.name) return;
  handleNodeLevelFeatureTest(item, s);
};

const handleNodeLevelFeatureTest = (item, nodeConfig) => {
  if (!item?.name || !nodeConfig) return;
  const similarity = nodeConfig.相似度 != null ? Number(nodeConfig.相似度) : undefined;
  const region =
    nodeConfig.查找区域 != null && nodeConfig.查找区域 !== ""
      ? String(nodeConfig.查找区域).trim()
      : "";
  if (item.kind === "image") {
    emit("open-image-test", {
      name: item.name,
      similarity,
      region,
      matchMode: nodeConfig.类型 === "彩图" ? "color" : "gray",
    });
    return;
  }
  testFontLibraryName.value = item.name;
  testSimilarity.value = similarity;
  testRegion.value = region;
  testDialogVisible.value = true;
};

/** 从特征列表删除字库/图片库中对应资源（与右侧面板 delete-library-resource 一致） */
const handleScreenFeatureDelete = (item) => {
  handleNodeFeatureDelete(item, currentScreenObj.value);
};

const handleNodeFeatureDelete = (item, nodeConfig) => {
  if (!item?.name) return;
  const libLabel = item.kind === "font" ? "字库" : "图片库";
  ElMessageBox.confirm(
    `确定从${libLabel}中删除「${item.name}」？删除后需重新制作或导入才可再次使用。`,
    "删除确认",
    {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    }
  )
    .then(() => {
      if (item.kind === "font") {
        emit("delete-library-resource", {
          type: "点阵",
          name: item.name,
          exactOnly: true,
          id: item.id,
        });
        return;
      }
      const t = nodeConfig?.类型 === "彩图" ? "彩图" : "图片";
      emit("delete-library-resource", {
        type: t,
        name: item.name,
        exactOnly: true,
        id: item.id,
      });
    })
    .catch(() => {});
};

const buildDeleteLibraryPayload = ({ kind, nodeType, name, id }) => {
  if (!name) return null;
  if (kind === "font") {
    return {
      type: "点阵",
      name,
      exactOnly: true,
      id,
    };
  }
  return {
    type: nodeType === "彩图" ? "彩图" : "图片",
    name,
    exactOnly: true,
    id,
  };
};

const collectResourceDeletePayloadsByBase = (baseName, mode, nodeType) => {
  if (!baseName || mode === "none") return [];
  if (mode === "font") {
    const list = Array.isArray(props.fontLibraryList) ? props.fontLibraryList : [];
    return list
      .filter((row) => featureNameBelongsToBase(row?.name, baseName))
      .map((row) =>
        buildDeleteLibraryPayload({
          kind: "font",
          nodeType,
          name: row?.name,
          id: row?.id,
        })
      )
      .filter(Boolean);
  }
  const list = Array.isArray(props.imageLibraryList) ? props.imageLibraryList : [];
  return list
    .filter((item) => featureNameBelongsToBase(item?.name, baseName))
    .map((item) =>
      buildDeleteLibraryPayload({
        kind: "image",
        nodeType,
        name: item?.name,
        id: item?.id,
      })
    )
    .filter(Boolean);
};

const dedupeDeletePayloads = (payloads) => {
  const seen = new Set();
  return (payloads || []).filter((p) => {
    if (!p?.name || !p?.type) return false;
    const key = `${p.type}::${p.id ?? ""}::${p.name}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

const emitDeleteLibraryPayloads = (payloads) => {
  dedupeDeletePayloads(payloads).forEach((payload) => {
    emit("delete-library-resource", payload);
  });
};

const collectCascadeDeletePayloadsForScreen = (screenKey, screenObj) => {
  if (!screenKey || !screenObj || typeof screenObj !== "object") return [];
  const allPayloads = [];
  const screenType = screenObj?.类型;
  const screenMode = resolveFeatureModeByType(screenType);
  allPayloads.push(
    ...collectResourceDeletePayloadsByBase(screenKey, screenMode, screenType)
  );

  const buttons = screenObj?.按钮;
  if (buttons && typeof buttons === "object" && !Array.isArray(buttons)) {
    Object.entries(buttons).forEach(([btnName, btnCfg]) => {
      const mode = resolveFeatureModeByType(btnCfg?.类型);
      const baseName = `${screenKey}_按钮_${btnName}`;
      allPayloads.push(
        ...collectResourceDeletePayloadsByBase(baseName, mode, btnCfg?.类型)
      );
    });
  }

  const states = screenObj?.状态;
  if (states && typeof states === "object" && !Array.isArray(states)) {
    Object.entries(states).forEach(([stateName, stateCfg]) => {
      const mode = resolveFeatureModeByType(stateCfg?.类型);
      const baseName = `${screenKey}_状态_${stateName}`;
      allPayloads.push(
        ...collectResourceDeletePayloadsByBase(baseName, mode, stateCfg?.类型)
      );
    });
  }
  return dedupeDeletePayloads(allPayloads);
};

const collectCascadeDeletePayloadsForNode = (keys, deletingValue) => {
  if (!Array.isArray(keys) || !keys.length) return [];
  if (keys.length === 1) {
    return collectCascadeDeletePayloadsForScreen(keys[0], deletingValue);
  }
  if (!deletingValue || typeof deletingValue !== "object") return [];
  if (keys.length === 3 && keys[1] === "按钮") {
    const mode = resolveFeatureModeByType(deletingValue?.类型);
    const baseName = `${keys[0]}_按钮_${keys[2]}`;
    return dedupeDeletePayloads(
      collectResourceDeletePayloadsByBase(baseName, mode, deletingValue?.类型)
    );
  }
  if (keys.length === 3 && keys[1] === "状态") {
    const mode = resolveFeatureModeByType(deletingValue?.类型);
    const baseName = `${keys[0]}_状态_${keys[2]}`;
    return dedupeDeletePayloads(
      collectResourceDeletePayloadsByBase(baseName, mode, deletingValue?.类型)
    );
  }
  const mode = resolveFeatureModeByType(deletingValue?.类型);
  return dedupeDeletePayloads(
    collectResourceDeletePayloadsByBase(keys.join("_"), mode, deletingValue?.类型)
  );
};

const onScreenSimilarityCommit = () => {
  const s = currentScreenObj.value;
  if (!s) return;
  const num = Number(s.相似度);
  if (Number.isNaN(num) || num < 0 || num > 1) {
    ElMessage.error("相似度必须在 0 到 1 之间");
    s.相似度 = 0.9;
    return;
  }
  s.相似度 = num;
};

const validateRegionLike = (trimmed, label) => {
  if (trimmed === "") return true;
  if (!/^-?\d+,-?\d+,-?\d+,-?\d+$/.test(trimmed)) {
    ElMessage.error(`${label}格式错误，应为空或 x,y,w,h`);
    return false;
  }
  return true;
};

const onScreenSearchRegionBlur = () => {
  const s = currentScreenObj.value;
  if (!s) return;
  const trimmed = String(s.查找区域 ?? "").trim();
  if (!validateRegionLike(trimmed, "查询范围")) {
    s.查找区域 = "";
  }
};

const onScreenAvoidRegionBlur = () => {
  const s = currentScreenObj.value;
  if (!s) return;
  const trimmed = String(s.误触区域 ?? "").trim();
  if (!validateRegionLike(trimmed, "误触区域")) {
    s.误触区域 = "";
  }
};

const onButtonSimilarityCommit = (btnName, v) => {
  const s = currentScreenObj.value?.按钮?.[btnName];
  if (!s) return;
  const num = Number(v);
  if (Number.isNaN(num) || num < 0 || num > 1) {
    ElMessage.error("相似度必须在 0 到 1 之间");
    return;
  }
  s.相似度 = num;
};

const onButtonFieldBlur = (btnName, fieldKey, raw) => {
  const s = currentScreenObj.value?.按钮?.[btnName];
  if (!s) return;
  const newStr = raw == null ? "" : String(raw);
  const trimmed = newStr.trim();
  if (fieldKey === "查找区域") {
    if (!validateRegionLike(trimmed, "查询范围")) return;
    s.查找区域 = trimmed;
    return;
  }
  if (fieldKey === "偏移点击区域") {
    if (trimmed === "") {
      s.偏移点击区域 = "";
      return;
    }
    if (!validateRegionLike(trimmed, "偏移点击区域")) return;
    s.偏移点击区域 = trimmed;
  }
};

const onStateSimilarityCommit = (stateName, v) => {
  const s = currentScreenObj.value?.状态?.[stateName];
  if (!s) return;
  const num = Number(v);
  if (Number.isNaN(num) || num < 0 || num > 1) {
    ElMessage.error("相似度必须在 0 到 1 之间");
    return;
  }
  s.相似度 = num;
};

const onStateFieldBlur = (stateName, fieldKey, raw) => {
  const s = currentScreenObj.value?.状态?.[stateName];
  if (!s) return;
  const newStr = raw == null ? "" : String(raw);
  const trimmed = newStr.trim();
  if (fieldKey === "查找区域") {
    if (!validateRegionLike(trimmed, "查询范围")) return;
    s.查找区域 = trimmed;
    return;
  }
  if (fieldKey === "偏移点击区域") {
    if (trimmed === "") {
      s.偏移点击区域 = "";
      return;
    }
    if (!validateRegionLike(trimmed, "偏移点击区域")) return;
    s.偏移点击区域 = trimmed;
  }
};

const isOffsetActiveForPath = (pathStr) => {
  return (
    fontClickOffsetAreaSelectionEnabled.value &&
    offsetAreaSelectionTargetMode.value === "json" &&
    offsetAreaSelectionTargetNodePath.value === pathStr
  );
};

const handleTestByPath = (pathKeys) => {
  handleTest({ path: buildJsonPath(pathKeys) });
};

const handleAddConfigByPath = (pathKeys) => {
  const node = { path: buildJsonPath(pathKeys) };
  handleAddConfig(node);
};

const handleDeleteByPath = (pathKeys) => {
  handleDelete({ path: buildJsonPath(pathKeys) });
};

const ensureScreenShape = (k) => {
  const s = data.value?.[k];
  if (!k || !s || typeof s !== "object" || Array.isArray(s)) return;
  s.类型 = normalizeConfigType(s.类型, "图片");
  if (!s.按钮 || typeof s.按钮 !== "object" || Array.isArray(s.按钮)) s.按钮 = {};
  if (!s.状态 || typeof s.状态 !== "object" || Array.isArray(s.状态)) s.状态 = {};
  if (!s.滑动区域 || typeof s.滑动区域 !== "object" || Array.isArray(s.滑动区域))
    s.滑动区域 = {};
  if (!s.识字区域 || typeof s.识字区域 !== "object" || Array.isArray(s.识字区域))
    s.识字区域 = {};
  Object.values(s.按钮).forEach((btn) => {
    if (btn && typeof btn === "object" && !Array.isArray(btn)) {
      btn.类型 = normalizeConfigType(btn.类型, "图片");
    }
  });
  Object.values(s.状态).forEach((st) => {
    if (st && typeof st === "object" && !Array.isArray(st)) {
      st.类型 = normalizeConfigType(st.类型, "图片");
    }
  });
};

watch(selectedRootKey, (k) => {
  if (k) ensureScreenShape(k);
});

const handleNewScreen = () => {
  if (!data.value || typeof data.value !== "object" || Array.isArray(data.value)) {
    data.value = {};
  }
  ElMessageBox.prompt("", "新建界面", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPlaceholder: "请输入界面名称",
  })
    .then(({ value }) => {
      const key = (value || "").trim();
      if (!key) {
        ElMessage.error("界面名称不能为空");
        return;
      }
      if (Object.prototype.hasOwnProperty.call(data.value, key)) {
        ElMessage.error("名称已存在");
        return;
      }
      data.value[key] = {
        类型: "图片",
        查找区域: "",
        相似度: 0.9,
        状态: {},
        按钮: {},
        滑动区域: {},
        识字区域: {},
        误触区域: "",
      };
      selectedRootKey.value = key;
      ElMessage.success("已添加界面");
    })
    .catch(() => {});
};

const handleDeleteRootScreen = (key) => {
  if (!data.value || !key) return;
  ElMessageBox.confirm(`确定删除界面「${key}」及其下所有配置？`, "删除确认", {
    type: "warning",
    confirmButtonText: "删除",
    cancelButtonText: "取消",
  })
    .then(() => {
      const screenObj = data.value?.[key];
      const payloads = collectCascadeDeletePayloadsForScreen(key, screenObj);
      delete data.value[key];
      emitDeleteLibraryPayloads(payloads);
      ElMessage.success(
        payloads.length ? `已删除，并清理 ${payloads.length} 个关联资源` : "已删除"
      );
      const remaining = Object.keys(data.value || {}).sort();
      selectedRootKey.value = remaining.length ? remaining[0] : null;
    })
    .catch(() => {});
};

watch(
  data,
  (newVal) => {
    autoSaveConfigFile();
  },
  { deep: true }
);

const configForm = ref({
  configPath: "",
});
const selectedConfigPath = ref("");
const configFileLoading = ref(false);

// 自动保存当前配置到文件（无提示）
const autoSaveConfigFile = async () => {
  if (!configForm.value.configPath) {
    return;
  }

  try {
    const content = JSON.stringify(data.value, null, 2);
    await ipc.invoke(ipcApiRoute.writeTextFile, {
      filePath: configForm.value.configPath,
      content,
    });
  } catch (error) {
    console.error("自动保存配置文件失败:", error);
  }
};

// 选择配置 JSON 文件并加载到 data.value
const handleSelectConfigFile = async () => {
  configFileLoading.value = true;
  try {
    const dialogResult = await ipc.invoke(ipcApiRoute.openFileDialog, {
      title: "选择配置 JSON 文件",
      defaultPath: configForm.value.configPath || "",
      filters: [
        { name: "JSON 文件", extensions: ["json"] },
        { name: "所有文件", extensions: ["*"] },
      ],
    });

    if (
      !dialogResult ||
      !dialogResult.success ||
      dialogResult.canceled ||
      !dialogResult.filePath
    ) {
      return;
    }

    const filePath = dialogResult.filePath;
    const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
      filePath,
    });

    if (!readResult || !readResult.success) {
      throw new Error(readResult?.message || "读取文件失败");
    }

    let parsed;
    try {
      parsed = JSON.parse(readResult.content || "{}");
    } catch (e) {
      ElMessage.error("配置文件不是有效的 JSON");
      return;
    }

    data.value = parsed;
    configForm.value.configPath = filePath;
    selectedConfigPath.value = filePath;
    await saveConfigPathToDB();
    ElMessage.success("配置已加载");
  } catch (error) {
    console.error("选择或读取配置文件失败:", error);
    ElMessage.error("选择或读取配置文件失败: " + (error.message || "未知错误"));
  } finally {
    configFileLoading.value = false;
  }
};

// 打开当前配置文件
const handleOpenConfigFile = async () => {
  if (!configForm.value.configPath) {
    ElMessage.warning("请先选择配置 JSON 文件");
    return;
  }

  try {
    const result = await ipc.invoke(ipcApiRoute.openFile, {
      filePath: configForm.value.configPath,
    });

    if (!result || !result.success) {
      throw new Error(result?.message || "打开文件失败");
    }

    ElMessage.success("文件已打开");
  } catch (error) {
    console.error("打开配置文件失败:", error);
    ElMessage.error("打开配置文件失败: " + (error.message || "未知错误"));
  }
};

// 保存配置文件路径到数据库（复用全局的 configPath 字段）
const saveConfigPathToDB = async () => {
  try {
    await ipc.invoke(ipcApiRoute.savePaths, {
      configPath: configForm.value.configPath,
    });
  } catch (error) {
    console.error("保存配置路径失败:", error);
  }
};

// 从数据库加载配置文件路径并自动读取
const loadConfigPathFromDB = async () => {
  try {
    const result = await ipc.invoke(ipcApiRoute.getPaths);
    if (result && result.success && result.data && result.data.configPath) {
      configForm.value.configPath = result.data.configPath;
      selectedConfigPath.value = result.data.configPath;
      await loadConfigFile(result.data.configPath);
    }
  } catch (error) {
    console.error("加载配置路径失败:", error);
  }
};

// 读取指定配置文件到 data.value
const loadConfigFile = async (filePath) => {
  if (!filePath) return;

  try {
    const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
      filePath,
    });

    if (!readResult || !readResult.success) {
      return;
    }

    try {
      const parsed = JSON.parse(readResult.content || "{}");
      data.value = parsed;
    } catch (e) {
      console.error("解析配置 JSON 失败:", e);
    }
  } catch (error) {
    console.error("加载配置文件失败:", error);
  }
};

// data 变化时 key 变化，强制 Cascader 重新挂载，使 level 1 选项随 data 更新
const cascaderOptionsKey = computed(() =>
  JSON.stringify(Object.keys(data.value || {}).sort())
);


const drawer = ref(false);
const currentNode = ref(null);

const selectedCascader = ref([]);
const selectedName = ref("");

// data 变化时清空级联选择，避免选中项与当前选项不一致
watch(cascaderOptionsKey, () => {
  selectedCascader.value = [];
});

// ========== 独立的颜色管理 ==========
const selectedColors = ref([]); // 自己维护的颜色列表 [{ hex: 'D61E24' }, ...]
const rowDeviations = ref([]); // 每行偏色值 0–100

const processedImageUrl = ref(null);
const enableAutoCrop = ref(true);
const fontClickOffsetAreaInput = ref("");

// 偏移点击区域圈选状态
const fontClickOffsetAreaSelectionEnabled = ref(false);

// 偏移点击区域圈选目标：
// - drawer：写回 `fontClickOffsetAreaInput`（抽屉里添加点阵）
// - json：按 `node.path` 写回配置里对应「偏移点击区域」字段
const offsetAreaSelectionTargetMode = ref("drawer"); // "drawer" | "json"
const offsetAreaSelectionTargetNodePath = ref("");

const isDrawerFontClickOffsetAreaSelectionActive = computed(() => {
  return (
    fontClickOffsetAreaSelectionEnabled.value &&
    offsetAreaSelectionTargetMode.value === "drawer"
  );
});

// 是否存在左侧圈选范围（用于偏移点击区域的基准）
const hasSelectionRect = computed(() => {
  return props.selectionRect && props.selectionRect.w && props.selectionRect.h;
});


// 供外部（图片点击）调用的添加颜色方法
const addColor = (colorInfo) => {
  if (!colorInfo || !colorInfo.hex) return;
  const hex = colorInfo.hex.replace(/^#/, "").toUpperCase();
  // 检查是否已存在相同颜色
  if (selectedColors.value.some((c) => c.hex === hex)) {
    ElMessage.warning("已存在相同颜色");
    return;
  }
  selectedColors.value.push({ hex });
  rowDeviations.value.push(0);
  // 重新计算二值化
  if (props.currentImage?.url) runBinarizationFromTable();
};

// 删除颜色
const handleRemoveColor = (index) => {
  selectedColors.value.splice(index, 1);
  rowDeviations.value.splice(index, 1);
  if (selectedColors.value.length > 0 && props.currentImage?.url) {
    runBinarizationFromTable();
  } else {
    processedImageUrl.value = null;
  }
};

// 清空所有颜色
const handleClearAllColors = () => {
  selectedColors.value = [];
  rowDeviations.value = [];
  processedImageUrl.value = null;
  ElMessage.success("已清空全部颜色");
};

const handleAddSliderArea = (node) => {
  currentNode.value = getCurrentNode(node);
  
  ElMessageBox.prompt("", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPlaceholder: "请输入滑动区域名称",
  }).then(({ value }) => {
    if (!value || !value.trim()) {
      ElMessage.error("滑动区域名称不能为空");
      return;
    }
    if (Object.prototype.hasOwnProperty.call(currentNode.value, value.trim())) {
      ElMessage.error("名称已存在");
      return;
    }
    currentNode.value[value.trim()] = {
      起始区域: "",
      结束区域: "",
    };
  });
};

// 添加识字区域
const handleAddSzArea = (node) => {
  currentNode.value = getCurrentNode(node);
  ElMessageBox.prompt("", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPlaceholder: "请输入识字区域名称",
  }).then(({ value }) => {
    if (!value || !value.trim()) {
      ElMessage.error("识字区域名称不能为空");
      return;
    }
    if (Object.prototype.hasOwnProperty.call(currentNode.value, value.trim())) {
      ElMessage.error("名称已存在");
      return;
    }
    currentNode.value[value.trim()] = ''
  });
};
const handleAddItem = (node) => {
  let itemNode = {};
  if (node.path == "root") {
    itemNode = data.value;
  } else {
    currentNode.value = getCurrentNode(node);
    itemNode = currentNode.value;
    
  }
  // 类型（仅按钮需要）：固定区域 / 点阵 / 图片 / 彩图（BGR 平方差匹配，对底色差异敏感）
  const type = ref("图片");
  // 名字
  const name = ref("");

  const content = () =>
    h(
      "div",
      {
        style: "display:flex;flex-direction:column;gap:12px;",
      },
      [
        node.key === "按钮"
          ? h(
              "div",
              {
                style: "display:flex;align-items:center;gap:8px;",
              },
              [
                h(
                  "span",
                  {
                    style: "width:80px;text-align:right;",
                  },
                  "类型："
                ),
                h(
                  ElRadioGroup,
                  {
                    modelValue: type.value,
                    "onUpdate:modelValue": (val) => {
                      type.value = val;
                    },
                  },
                  () => [
                    h(
                      ElRadio,
                      { label: "固定区域" },
                      () => "固定区域"
                    ),
                    h(
                      ElRadio,
                      { label: "点阵" },
                      () => "点阵"
                    ),
                    h(
                      ElRadio,
                      { label: "图片" },
                      () => "图片"
                    ),
                    h(
                      ElRadio,
                      { label: "彩图" },
                      () => "彩图"
                    ),
                  ]
                ),
              ]
            )
          : h(
              "div",
              {
                style: "display:flex;align-items:center;gap:8px;",
              },
              [
                h(
                  "span",
                  {
                    style: "width:80px;text-align:right;",
                  },
                  "类型："
                ),
                h(
                  ElRadioGroup,
                  {
                    modelValue: type.value,
                    "onUpdate:modelValue": (val) => {
                      type.value = val;
                    },
                  },
                  () => [
                    h(
                      ElRadio,
                      { label: "点阵" },
                      () => "点阵"
                    ),
                    h(
                      ElRadio,
                      { label: "图片" },
                      () => "图片"
                    ),
                    h(
                      ElRadio,
                      { label: "彩图" },
                      () => "彩图"
                    ),
                  ]
                ),
              ]
            ),
        h(
          "div",
          {
            style: "display:flex;align-items:center;gap:8px;",
          },
          [
            h(
              "span",
              {
                style: "width:80px;text-align:right;flex-shrink:0;",
              },
              "配置名称："
            ),
            h(ElInput, {
              modelValue: name.value,
              "onUpdate:modelValue": (val) => {
                name.value = val;
              },
              placeholder: "请输入名称",
            }),
          ]
        ),
      ]
    );

  ElMessageBox({
    title: "添加配置项",
    message: content,
    showCancelButton: true,
    confirmButtonText: "确定",
    cancelButtonText: "取消",
  })
    .then(() => {
      const key = name.value.trim();
      if (!key) {
        ElMessage.error("名称不能为空");
        return;
      }
      if (Object.prototype.hasOwnProperty.call(itemNode, key)) {
        ElMessage.error("名称已存在");
        return;
      }

      if (node.path == "root") {
          itemNode[key] = {
            类型: type.value,
            查找区域: "",
            相似度: 0.9,
            状态: {},
            按钮: {},
            滑动区域: {},
            识字区域: {},
            误触区域: ""
          };
        } else if (type.value === "固定区域") {
          itemNode[key] = {
            类型: type.value,
            固定点击区域: ""
          };
        } else {
          itemNode[key] = {
            类型: type.value,
            查找区域: "",
            偏移点击区域: "",
            相似度: 0.9,
          };
        }
    })
    .catch(() => {});
};

// 获取当前节点（按路径深度遍历，避免层数写死）
const getCurrentNode = (node) => {
  if (!node?.path) return undefined;
  const keys = getPathKeys(node.path);
  let t = data.value;
  for (const k of keys) {
    t = t?.[k];
  }
  return t;
};
const currentName = ref("");
// ========== 节点操作 ==========
const handleAddConfig = (node) => {
  currentNode.value = getCurrentNode(node);
  const keys = getPathKeys(node.path);
  currentName.value = keys.join("_");
  if (!currentNode.value || typeof currentNode.value !== "object") {
    ElMessage.warning("无法定位当前配置节点");
    return;
  }
  const typ = currentNode.value.类型;
  if (typ === "图片" || typ === "彩图") {
    // 图片 / 彩图：将当前图片或圈选区域添加到图片库（由右侧面板统一处理）
    if (!props.currentImage || !props.currentImage.url) {
      ElMessage.warning("当前没有图片，无法添加到图片库");
      return;
    }
    emit("add-image-to-library", {
      name: currentName.value,
      selectionRect: props.selectionRect || null,
      currentImageUrl: props.currentImage.url,
    });
    return;
  }
  if (typ === "点阵") {
    fontClickOffsetAreaInput.value = "";
    // 重置 drawer 状态（保留已有的颜色列表，方便连续操作）
    enableAutoCrop.value = true;
    drawer.value = true;
  }
};

// 切换偏移点击区域圈选模式
const toggleFontClickOffsetAreaSelection = () => {
  if (!hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }

  // 当前选择目标就是抽屉输入框：取消
  if (isDrawerFontClickOffsetAreaSelectionActive.value) {
    fontClickOffsetAreaSelectionEnabled.value = false;
    offsetAreaSelectionTargetMode.value = "drawer";
    offsetAreaSelectionTargetNodePath.value = "";
    emit("stop-code-generator-selection");
    ElMessage.info("已取消圈选模式");
  } else {
    // 若已开启但目标在配置字段：切换为抽屉目标（继续圈选）
    if (fontClickOffsetAreaSelectionEnabled.value) {
      offsetAreaSelectionTargetMode.value = "drawer";
      offsetAreaSelectionTargetNodePath.value = "";
      ElMessage.info("已切换偏移点击区域圈选目标");
      return;
    }

    // 未开启：开始圈选
    fontClickOffsetAreaSelectionEnabled.value = true;
    offsetAreaSelectionTargetMode.value = "drawer";
    offsetAreaSelectionTargetNodePath.value = "";
    // 使用单独的类型标识，区分与颜色 Tab 的偏移点击区域
    emit("start-code-generator-selection", "configFontClickOffsetArea");
    ElMessage.info("请在图片上圈选偏移点击区域");
  }
};

// 结构化表单中「偏移点击区域」旁圈选：写回对应配置路径
const toggleFontClickOffsetAreaSelectionForNode = (node) => {
  if (!hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }
  if (!node?.path) return;

  const targetIsActive =
    fontClickOffsetAreaSelectionEnabled.value &&
    offsetAreaSelectionTargetMode.value === "json" &&
    offsetAreaSelectionTargetNodePath.value === node.path;

  // 已开启且点击当前节点：取消
  if (targetIsActive) {
    fontClickOffsetAreaSelectionEnabled.value = false;
    offsetAreaSelectionTargetMode.value = "drawer";
    offsetAreaSelectionTargetNodePath.value = "";
    emit("stop-code-generator-selection");
    ElMessage.info("已取消圈选模式");
    return;
  }

  // 若已开启但目标不是当前节点：切换目标（继续圈选）
  if (fontClickOffsetAreaSelectionEnabled.value) {
    offsetAreaSelectionTargetMode.value = "json";
    offsetAreaSelectionTargetNodePath.value = node.path;
    ElMessage.info("已切换偏移点击区域圈选目标");
    return;
  }

  // 未开启：开始圈选
  fontClickOffsetAreaSelectionEnabled.value = true;
  offsetAreaSelectionTargetMode.value = "json";
  offsetAreaSelectionTargetNodePath.value = node.path;
  emit("start-code-generator-selection", "configFontClickOffsetArea");
  ElMessage.info("请在图片上圈选偏移点击区域");
};

// ========== 偏色管理 ==========
const getRowDeviation = (index) => rowDeviations.value[index] ?? 0;
const setRowDeviation = (index, value) => {
  const arr = [...rowDeviations.value];
  arr[index] = Math.max(0, Math.min(100, value));
  rowDeviations.value = arr;
  runBinarizationFromTable();
};

// ========== 工具函数 ==========
const isLightColor = (hex) => {
  hex = String(hex).replace("#", "");
  if (hex.length === 3)
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 186;
};

const hexToRgb = (hex) => {
  hex = hex.replace("#", "");
  if (hex.length === 3)
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  return {
    r: parseInt(hex.substring(0, 2), 16),
    g: parseInt(hex.substring(2, 4), 16),
    b: parseInt(hex.substring(4, 6), 16),
  };
};

const numToHex = (num) => {
  const hex = Math.max(0, Math.min(255, Math.floor(num)))
    .toString(16)
    .toUpperCase();
  return hex.length === 1 ? "0" + hex : hex;
};

// ========== 偏色计算 ==========
const buildDeviationListFromTable = () => {
  const list = [];
  for (let i = 0; i < selectedColors.value.length; i++) {
    const d = rowDeviations.value[i] ?? 0;
    const baseRgb = hexToRgb(selectedColors.value[i].hex);
    const baseHex = numToHex(baseRgb.r) + numToHex(baseRgb.g) + numToHex(baseRgb.b);
    const deviationHex = numToHex(d) + numToHex(d) + numToHex(d);
    list.push(`${baseHex}-${deviationHex}`);
  }
  return list;
};

const parseDeviation = (deviationStr) => {
  const [baseHex, deviationHex] = deviationStr.split("-");
  if (!baseHex || !deviationHex || baseHex.length !== 6 || deviationHex.length !== 6)
    return null;
  return {
    base: {
      r: parseInt(baseHex.substring(0, 2), 16),
      g: parseInt(baseHex.substring(2, 4), 16),
      b: parseInt(baseHex.substring(4, 6), 16),
    },
    deviation: {
      r: parseInt(deviationHex.substring(0, 2), 16),
      g: parseInt(deviationHex.substring(2, 4), 16),
      b: parseInt(deviationHex.substring(4, 6), 16),
    },
  };
};

const isColorInDeviationRange = (r, g, b, deviationData) => {
  const { base, deviation } = deviationData;
  return (
    r >= Math.max(0, base.r - deviation.r) &&
    r <= Math.min(255, base.r + deviation.r) &&
    g >= Math.max(0, base.g - deviation.g) &&
    g <= Math.min(255, base.g + deviation.g) &&
    b >= Math.max(0, base.b - deviation.b) &&
    b <= Math.min(255, base.b + deviation.b)
  );
};

// ========== 二值化处理 ==========
const runBinarizationFromTable = () => {
  if (!props.currentImage?.url) return;
  const deviationList = buildDeviationListFromTable();
  if (deviationList.length === 0) return;
  const deviationDataList = deviationList.map(parseDeviation).filter(Boolean);
  if (deviationDataList.length === 0) return;

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      let startX = 0,
        startY = 0,
        width = img.width,
        height = img.height;
      if (props.selectionRect?.w > 0 && props.selectionRect?.h > 0) {
        startX = Math.max(0, Math.min(props.selectionRect.x, img.width - 1));
        startY = Math.max(0, Math.min(props.selectionRect.y, img.height - 1));
        width = Math.min(props.selectionRect.w, img.width - startX);
        height = Math.min(props.selectionRect.h, img.height - startY);
      }
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);
      const imageData = ctx.getImageData(0, 0, width, height);
      const pixelData = imageData.data;

      for (let i = 0; i < pixelData.length; i += 4) {
        const r = pixelData[i],
          g = pixelData[i + 1],
          b = pixelData[i + 2];
        let inRange = false;
        for (const dd of deviationDataList) {
          if (isColorInDeviationRange(r, g, b, dd)) {
            inRange = true;
            break;
          }
        }
        pixelData[i] = pixelData[i + 1] = pixelData[i + 2] = inRange ? 255 : 0;
        pixelData[i + 3] = 255;
      }
      ctx.putImageData(imageData, 0, 0);
      processedImageUrl.value = canvas.toDataURL("image/png");
    } catch (e) {
      console.error("二值化出错:", e);
    }
  };
  img.src = props.currentImage.url;
};

// ========== 确认添加配置 ==========
const handleConfirmAddConfig = async () => {
  if (!processedImageUrl.value) {
    ElMessage.warning("请先生成点阵");
    return;
  }

  const deviationList = buildDeviationListFromTable();
  if (!deviationList.length) {
    ElMessage.warning("请先添加颜色");
    return;
  }

  try {
    const img = new Image();
    img.crossOrigin = "anonymous";

    await new Promise((resolve, reject) => {
      img.onload = async () => {
        try {
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);

          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          const pixelData = imageData.data;

          // 找到白色像素的最小边界框
          let minX = img.width,
            minY = img.height,
            maxX = 0,
            maxY = 0;
          let whitePixelCount = 0;

          for (let y = 0; y < img.height; y++) {
            for (let x = 0; x < img.width; x++) {
              const idx = (y * img.width + x) * 4;
              if (
                pixelData[idx] > 200 &&
                pixelData[idx + 1] > 200 &&
                pixelData[idx + 2] > 200
              ) {
                whitePixelCount++;
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
              }
            }
          }

          if (whitePixelCount === 0) {
            ElMessage.warning("二值化图片中没有白色像素");
            reject(new Error("没有白色像素"));
            return;
          }

          // 根据是否裁剪决定范围
          let cropMinX, cropMinY, cropMaxX, cropMaxY;
          if (enableAutoCrop.value) {
            cropMinX = minX;
            cropMinY = minY;
            cropMaxX = maxX;
            cropMaxY = maxY;
          } else {
            cropMinX = 0;
            cropMinY = 0;
            cropMaxX = img.width - 1;
            cropMaxY = img.height - 1;
          }

          const width = cropMaxX - cropMinX + 1;
          const height = cropMaxY - cropMinY + 1;

          // 提取二值数据
          const binaryData = [];
          for (let y = cropMinY; y <= cropMaxY; y++) {
            for (let x = cropMinX; x <= cropMaxX; x++) {
              const idx = (y * img.width + x) * 4;
              const isWhite =
                pixelData[idx] > 200 &&
                pixelData[idx + 1] > 200 &&
                pixelData[idx + 2] > 200;
              binaryData.push(isWhite ? "1" : "0");
            }
          }

          // 转为十六进制点阵字符串
          let matrixHex = "";
          for (let i = 0; i < binaryData.length; i += 4) {
            const bits = binaryData.slice(i, i + 4).join("");
            const paddedBits = bits.padEnd(4, "0");
            matrixHex += parseInt(paddedBits, 2).toString(16).toUpperCase();
          }

          // 偏色列表以 "|" 组合
          const deviationStr = deviationList.join("|");
          // 点阵 = hex&width,height,count
          const matrixStr = `${matrixHex}&${width},${height},${whitePixelCount}`;
          
          // 处理偏移点击区域，格式为 x,y,w,h，若未填写则默认 0,0,0,0
          let clickOffsetArea = "0,0,0,0";
          if (fontClickOffsetAreaInput.value && fontClickOffsetAreaInput.value.trim()) {
            const raw = fontClickOffsetAreaInput.value.trim();
            const parts = raw.split(",").map((s) => s.trim());
            if (
              parts.length !== 4 ||
              parts.some((p) => p === "" || Number.isNaN(parseInt(p, 10)))
            ) {
              ElMessage.warning("偏移点击区域格式不正确，应为：x,y,w,h");
              reject(new Error("偏移点击区域格式不正确"));
              return;
            }
            const [x, y, w, h] = parts.map((p) => parseInt(p, 10));
            if (w < 0 || h < 0) {
              ElMessage.warning("偏移点击区域宽高必须为非负整数");
              reject(new Error("偏移点击区域宽高必须为非负整数"));
              return;
            }
            clickOffsetArea = `${x},${y},${w},${h}`;
          }

          // 使用 currentName 作为字库名称
          const name = (currentName.value || "").trim();

          if (name) {
            const fontItem = {
              id: Date.now(),
              matrix: matrixHex,
              width,
              height,
              totalCount: whitePixelCount,
              sizeInfo: `${width}×${height} (${whitePixelCount})`,
              deviation: deviationStr,
              name,
              clickOffsetArea,
              editing: false,
              binaryData,
            };

            const addPromise = new Promise((resolveAdd) => {
              emit("add-font-library", fontItem, resolveAdd);
            });

            await addPromise;
          } else {
            ElMessage.warning("点阵名称为空，未加入字库，仅更新配置");
          }

          // ElMessage.success(`配置 添加成功`);
          drawer.value = false;
          resolve();
        } catch (error) {
          console.error("处理点阵时出错:", error);
          reject(error);
        }
      };
      img.onerror = () => reject(new Error("加载图片失败"));
      img.src = processedImageUrl.value;
    });
  } catch (error) {
    console.error("添加配置失败:", error);
    ElMessage.error("添加配置失败: " + (error.message || "未知错误"));
  }
};

// 通过圈选结果设置偏移点击区域（由父组件调用）
const setFontClickOffsetAreaFromSelection = (rect) => {
  if (!rect || !rect.w || !rect.h) {
    return;
  }

  // 偏移点击区域需要基于左侧圈选范围计算偏移值
  if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
    ElMessage.warning("请先在左侧进行圈选，然后再圈选偏移点击区域");
    // 不取消圈选模式，让用户可以继续操作
    return;
  }

  // 计算偏移值：偏移点击区域的坐标 - 左侧圈选范围的坐标
  const offsetX = rect.x - props.selectionRect.x;
  const offsetY = rect.y - props.selectionRect.y;
  const areaStr = `${offsetX},${offsetY},${rect.w},${rect.h}`;

  if (offsetAreaSelectionTargetMode.value === "drawer") {
    fontClickOffsetAreaInput.value = areaStr;
  } else {
    const keys = getPathKeys(offsetAreaSelectionTargetNodePath.value);
    if (!keys.length) {
      ElMessage.warning("无法定位偏移点击区域节点，已生成偏移值但未写回");
    } else {
      let target = data.value;
      for (let i = 0; i < keys.length - 1; i++) {
        target = target?.[keys[i]];
      }
      const lastKey = keys[keys.length - 1];
      if (target && Object.prototype.hasOwnProperty.call(target, lastKey)) {
        target[lastKey] = areaStr;
      } else {
        // 兜底：尝试写入
        try {
          target[lastKey] = areaStr;
        } catch (e) {
          ElMessage.warning("无法写回偏移点击区域节点值");
        }
      }
    }
  }
  ElMessage.success("已获取偏移点击区域范围（已计算偏移值）");

  // 自动取消圈选模式
  fontClickOffsetAreaSelectionEnabled.value = false;
  emit("stop-code-generator-selection");
  offsetAreaSelectionTargetMode.value = "drawer";
  offsetAreaSelectionTargetNodePath.value = "";
};

/** 从 node.path 解析出键路径，如 "主界面"."按钮"."某名称" -> ['主界面','按钮','某名称'] */
// root.abc["123"].ddd.ccc['nihao'], ['abc', '123', 'ddd', 'ccc', 'nihao']
const getPathKeys = (path) => {
  if (!path || typeof path !== "string") return [];
  // 支持点语法与括号(单引号/双引号)
  const keys = path
    .replace(/\[(["'`])([^\1]+?)\1\]/g, '.$2') // 把[...](单双引号)转为.内容
    .split('.')
    .map(s => s.trim().replace(/^["'`]|["'`]$/g, '')) // 移除两端引号
    .filter(s => s.length > 0 && s !== '');

  // 如果第一个是root则丢掉
  return keys[0] === 'root' ? keys.slice(1) : keys;
};

/** 点击测试：点阵则弹出找字测试弹框；图片则用图片库中同名图片打开模板匹配测试 */
const handleTest = (node) => {
  if (!node?.path) return;

  const path = getPathKeys(node.path);
  let configItem = data.value;
  for (const key of path) {
    configItem = configItem?.[key];
  }

  const name = path.join("_");
  const similarity =
    configItem?.相似度 != null ? Number(configItem.相似度) : undefined;
  const region =
    configItem?.查找区域 != null && configItem.查找区域 !== ""
      ? String(configItem.查找区域).trim()
      : "";

  if (configItem?.类型 === "图片" || configItem?.类型 === "彩图") {
    emit("open-image-test", {
      name,
      similarity,
      region,
      matchMode: configItem.类型 === "彩图" ? "color" : "gray",
    });
    return;
  }

  testFontLibraryName.value = name;
  testSimilarity.value = similarity;
  testRegion.value = region;
  testDialogVisible.value = true;
};

/** 测试弹框关闭时清空初始值 */
const onTestDialogClosed = () => {
  testFontLibraryName.value = "";
  testSimilarity.value = undefined;
  testRegion.value = "";
};

/** 删除节点对应的配置项 */
const handleDelete = (node) => {
  if (!node?.path) return;
  const keys = getPathKeys(node.path);
  if (!keys.length) {
    ElMessage.warning("无法解析节点路径");
    return;
  }
  const keyToDelete = keys[keys.length - 1];
  let parent = data.value;
  for (let i = 0; i < keys.length - 1; i++) {
    parent = parent?.[keys[i]];
  }
  if (parent == null || !Object.prototype.hasOwnProperty.call(parent, keyToDelete)) {
    ElMessage.warning("项不存在或无法删除");
    return;
  }
  const deletingValue = parent[keyToDelete];
  const payloads = collectCascadeDeletePayloadsForNode(keys, deletingValue);

  ElMessageBox.confirm(`确定要删除「${keyToDelete}」吗？`, "删除确认", {
    confirmButtonText: "删除",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(() => {
      delete parent[keyToDelete];
      emitDeleteLibraryPayloads(payloads);
      ElMessage.success(
        payloads.length ? `已删除，并清理 ${payloads.length} 个关联资源` : "已删除"
      );
    })
    .catch(() => {});
};


onMounted(() => {
  loadConfigPathFromDB();
});

// 暴露给父组件的方法与状态
defineExpose({
  addColor,
  setFontClickOffsetAreaFromSelection,
  /** 是否正在显示「添加字库配置」抽屉，用于在未开启圈选时也允许点击图片选色 */
  isDrawerOpen: () => drawer.value,
});
</script>

<style scoped>
.config-tab-container {
  position: relative;
  overflow: hidden;
  /* 作为 el-tab-pane 的 flex 子项时须参与收缩，否则 height:100% 无参照且侧栏/主区无法内部滚动 */
  flex: 1;
  min-height: 0;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 14px;
  background: #f0f2f5;
  font-size: 13px;
  color: #1e293b;
}

/* —— 侧栏等仍使用的圆角按钮 —— */
.file-input {
  margin-bottom: 6px;
  flex-shrink: 0;
}

.cfg-toolbar-btn {
  border-radius: 40px !important;
  font-weight: 500;
  padding: 8px 16px !important;
}

.cfg-toolbar-btn--primary {
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.35);
}

.cfg-toolbar-btn--outline {
  background: #fff !important;
  border: 1px solid #cbd5e1 !important;
  color: #1e293b !important;
}

.cfg-toolbar-btn--outline:hover {
  background: #f8fafc !important;
  border-color: #94a3b8 !important;
}

.cfg-btn-icon {
  margin-right: 2px;
  vertical-align: middle;
}

.cfg-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 30px;
  font-size: 12px;
  color: #475569;
  background: #e2e8f0;
}

.cfg-badge--muted {
  background: #f1f5f9;
  color: #64748b;
}

/* —— 主工作区：侧栏 + 编辑 —— */
.cfg-workspace {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  gap: 16px;
  flex-wrap: nowrap;
  align-items: stretch;
}

.cfg-sidebar {
  flex: 1;
  min-width: 240px;
  max-width: 320px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  align-self: stretch;
}

.cfg-sidebar-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 16px 18px;
  border-bottom: 1px solid #e9eef3;
  font-weight: 600;
  font-size: 15px;
}

.cfg-sidebar-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.cfg-sidebar-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 0 12px;
}

.cfg-root-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 4px 10px;
  padding: 12px 14px;
  border-radius: 16px;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  background: #fefefe;
  border: 1px solid transparent;
}

.cfg-root-item:hover {
  background: #f8fafc;
}

.cfg-root-item.is-active {
  background: #eef2ff;
  border-color: rgba(59, 130, 246, 0.25);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border-left: 4px solid #3b82f6;
  padding-left: 11px;
}

.cfg-root-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  color: #3b82f6;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.cfg-root-info {
  flex: 1;
  min-width: 0;
}

.cfg-root-name {
  font-weight: 600;
  font-size: 13px;
  word-break: break-word;
  color: #0f172a;
}

.cfg-root-meta {
  margin-top: 4px;
  font-size: 11px;
  color: #64748b;
}

.cfg-sidebar-empty {
  padding: 40px 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

.cfg-sidebar-empty p {
  margin: 10px 0 0;
}

.cfg-main {
  flex: 3;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cfg-section-card {
  background: #f9fafb;
  border-radius: 20px;
  padding: 18px 20px;
  border: 1px solid #edf2f7;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.cfg-section-title {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 14px;
  padding-left: 12px;
  border-left: 4px solid #3b82f6;
}

.cfg-section-hint {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}

.cfg-empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 24px;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
  color: #94a3b8;
}

.cfg-empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.45;
}

.cfg-empty-state p {
  margin: 0;
  font-size: 15px;
}

.cfg-empty-sub {
  margin-top: 8px !important;
  font-size: 12px !important;
  color: #cbd5e1;
}

.config-drawer-wrapper {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  z-index: 20;
}

.config-drawer-mask {
  flex: 1;
  background: rgba(15, 23, 42, 0.32);
  backdrop-filter: blur(2px);
}

.config-drawer {
  position: relative;
  height: 100%;
  width: 380px;
  max-width: min(380px, 100%);
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  z-index: 1;
  border-left: 1px solid #e2e8f0;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25);
  border-radius: 20px 0 0 20px;
}

.config-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px;
  flex-shrink: 0;
  border-bottom: 1px solid #e2e8f0;
  background: radial-gradient(circle at top left, #e0f2fe 0, #f8fafc 45%, #ffffff 100%);
}

.config-drawer-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.config-drawer-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.config-drawer-title-main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.config-drawer-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #0369a1;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.25);
}

.config-drawer-subtitle {
  font-size: 11px;
  color: #64748b;
}

.config-drawer-body {
  flex: 1;
  padding: 12px 14px;
  overflow: auto;
  font-size: 13px;
  color: #475569;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.config-drawer-footer {
  flex-shrink: 0;
  padding: 12px 16px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

/* 颜色表格 */
.color-table-wrap {
  flex-shrink: 0;
}

.color-table-wrap :deep(.el-table) {
  --el-table-border-color: #e8ecf1;
}

.color-table-wrap :deep(.el-table td.el-table__cell),
.color-table-wrap :deep(.el-table th.el-table__cell) {
  border-right: none;
}

.color-table-wrap :deep(.el-table--border::after),
.color-table-wrap :deep(.el-table--border::before) {
  display: none;
}

.color-table-wrap :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.table-footer {
  padding: 3px 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  background: #fafbfc;
}

.table-count {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

.hex-cell {
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.slider-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
}

.slider-cell :deep(.el-slider) {
  flex: 1;
}

.slider-value {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 10px;
  color: #94a3b8;
  min-width: 20px;
  text-align: right;
}

.delete-btn {
  padding: 2px !important;
}

/* 二值化预览区域 */
.result-section {
  flex: 1;
  min-height: 80px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  background: #0f172a;
  background-image: linear-gradient(45deg, #1e293b 25%, transparent 25%),
    linear-gradient(-45deg, #1e293b 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1e293b 75%),
    linear-gradient(-45deg, transparent 75%, #1e293b 75%);
  background-size: 12px 12px;
  background-position: 0 0, 0 6px, 6px -6px, -6px 0px;
}

.result-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  color: #475569;
  font-size: 11px;
  letter-spacing: 0.3px;
  padding: 20px 0;
}

/* 字库配置区 */
.font-config-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 0 4px;
  margin-top: 4px;
  border-top: 1px solid #e2e8f0;
}

.font-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.font-label {
  width: 80px;
  font-size: 12px;
  color: #64748b;
  text-align: right;
  flex-shrink: 0;
}

.font-field {
  flex: 1;
}

/* 过渡动画 */
.config-drawer-slide-enter-from,
.config-drawer-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.config-drawer-slide-enter-active,
.config-drawer-slide-leave-active {
  transition: all 0.25s ease;
}

/* —— 原型式结构化编辑区 —— */
.cfg-visual-wrap {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cfg-visual-scroll {
  flex: 1 1 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px;
}

.proto-section-card {
  background: #f9fafb;
  border-radius: 20px;
  padding: 18px 20px;
  border: 1px solid #edf2f7;
}

.proto-section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 14px;
  padding-left: 12px;
  border-left: 4px solid #3b82f6;
  color: #0f172a;
}

.proto-section-title--between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.proto-add-btn {
  border-radius: 40px !important;
}

.proto-field-group {
  margin-bottom: 14px;
}

.proto-field-label {
  font-weight: 500;
  font-size: 12px;
  margin-bottom: 6px;
  color: #334155;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.proto-input,
.proto-input-full {
  width: 100%;
}

.proto-inline-group {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.proto-inline-field {
  flex: 1;
  min-width: 120px;
}

.proto-inline-field--grow {
  flex: 2;
  min-width: 200px;
}

.proto-toolbar-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.proto-button-card {
  background: #fff;
  border-radius: 16px;
  padding: 14px 16px;
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.proto-button-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.proto-button-name {
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
}

.proto-button-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.proto-field-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.proto-mini-label {
  font-size: 12px;
  color: #64748b;
  width: 40px;
}

.proto-type-tag {
  font-size: 12px;
  color: #0369a1;
  background: #e0f2fe;
  padding: 2px 10px;
  border-radius: 20px;
}

.proto-empty-hint {
  text-align: center;
  padding: 20px;
  color: #94a3b8;
  font-size: 13px;
}

.proto-feature-naming-hint {
  margin-top: 6px;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.45;
}

.proto-feature-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.proto-feature-cell {
  width: 104px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.proto-feature-thumb-wrap {
  position: relative;
}

.proto-feature-thumb {
  width: 88px;
  height: 88px;
  border-radius: 8px;
  background: #f1f5f9;
  display: block;
}

.proto-feature-thumb--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #94a3b8;
}

.proto-feature-actions {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  background: linear-gradient(
    to top,
    rgba(255, 255, 255, 0.96),
    rgba(255, 255, 255, 0.75),
    transparent
  );
  border-radius: 0 0 8px 8px;
}

.proto-feature-action-btn {
  padding: 0 2px !important;
  min-height: auto !important;
  height: auto !important;
  font-size: 11px !important;
}

.proto-feature-name {
  margin-top: 6px;
  font-size: 11px;
  color: #475569;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.proto-sz-object-hint {
  font-size: 12px;
  color: #64748b;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px dashed #cbd5e1;
}

.cfg-json-only-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  padding: 16px 18px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
}

.proto-json-only-hint {
  font-size: 12px;
  color: #64748b;
  margin: 0 0 12px;
}

.cfg-root-delete {
  flex-shrink: 0;
  margin-left: 4px;
}
</style>
