/**
 * 基础路由
 * @type { *[] }
 */

const constantRouterMap = [
  {
    path: '/',
    name: 'Index',
    component: () => import('@/views/main/Index.vue'),
    redirect: { name: 'ImageProcessor' },
    children: [
      {
        path: 'image-processor',
        name: 'ImageProcessor',
        component: () => import('@/views/main/components/ImageProcessor/ImageProcessorTab.vue')
      },
      {
        path: 'coloring',
        name: 'Coloring',
        component: () => import('@/views/main/components/ColoringTab/ColoringTab.vue')
      },
      {
        path: 'pathfinding',
        name: 'Pathfinding',
        component: () => import('@/views/main/components/PathfindingTab/PathfindingTab.vue')
      }
    ]
  },
  {
    path: '/screenshot-preview',
    name: 'ScreenshotPreview',
    component: () => import('@/views/screenshot-preview/Index.vue')
  },
  {
    path: '/pathfinding-map',
    name: 'PathfindingMap',
    component: () => import('@/views/pathfinding-map/Index.vue')
  },
]

export default constantRouterMap