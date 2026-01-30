/**
 * 基础路由
 * @type { *[] }
 */

const constantRouterMap = [
  {
    path: '/',
    name: 'Index',
    component: () => import('@/views/Index.vue'),
    children: [
     
    ]
  },
]

export default constantRouterMap