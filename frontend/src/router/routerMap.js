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
      }
    ]
  },
  {
    path: '/screenshot-preview',
    name: 'ScreenshotPreview',
    component: () => import('@/views/screenshot-preview/Index.vue')
  },
]

export default constantRouterMap