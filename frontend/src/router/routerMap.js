/**
 * 基础路由
 * @type { *[] }
 */

const constantRouterMap = [
  {
    path: '/',
    name: 'Example',
    redirect: { name: 'ExampleHelloIndex' },
    children: [
      {
        path: '/example',
        name: 'ExampleHelloIndex',
        component: () => import('@/views/example/hello/Index.vue'),
        redirect: { name: 'ImageProcessor' },
        children: [
          {
            path: 'image-processor',
            name: 'ImageProcessor',
            component: () => import('@/views/example/hello/components/ImageProcessor/ImageProcessorTab.vue')
          },
          {
            path: 'coloring',
            name: 'Coloring',
            component: () => import('@/views/example/hello/components/ColoringTab/ColoringTab.vue')
          },
          {
            path: 'pathfinding',
            name: 'Pathfinding',
            component: () => import('@/views/example/hello/components/PathfindingTab/PathfindingTab.vue')
          }
        ]
      },
      {
        path: '/image-result',
        name: 'ImageResult',
        component: () => import('@/views/example/image-result/Index.vue')
      },
      {
        path: '/screenshot-preview',
        name: 'ScreenshotPreview',
        component: () => import('@/views/example/screenshot-preview/Index.vue')
      },
      {
        path: '/pathfinding-map',
        name: 'PathfindingMap',
        component: () => import('@/views/example/pathfinding-map/Index.vue')
      },
    ]
  },
]

export default constantRouterMap