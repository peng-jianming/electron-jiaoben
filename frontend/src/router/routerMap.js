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
        component: () => import('@/views/example/hello/Index.vue')
      },
      {
        path: '/image-result',
        name: 'ImageResult',
        component: () => import('@/views/example/image-result/Index.vue')
      },
    ]
  },
]

export default constantRouterMap