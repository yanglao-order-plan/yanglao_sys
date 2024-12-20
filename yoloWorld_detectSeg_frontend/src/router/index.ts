import { type RouteRecordRaw, createRouter, createWebHashHistory, createWebHistory } from "vue-router"

const Layout = () => import("@/layout/index.vue")

/** 常驻路由 */
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: "/redirect",
    component: Layout,
    meta: {
      hidden: true
    },
    children: [
      {
        path: "/redirect/:path(.*)",
        component: () => import("@/views/redirect/index.vue")
      }
    ]
  },
  {
    path: "/403",
    component: () => import("@/views/error-page/403.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/404",
    component: () => import("@/views/error-page/404.vue"),
    meta: {
      hidden: true
    },
    alias: "/:pathMatch(.*)*"
  },
  {
    path: "/login",
    component: () => import("@/views/login/index.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/register",
    component: () => import("@/views/register/index.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/",
    component: Layout,
    redirect: "/dashboard",
    children: [
      {
        path: "dashboard",
        component: () => import("@/views/dashboard/index.vue"),
        name: "Dashboard",
        meta: {
          title: "首页",
          svgIcon: "dashboard",
          affix: true
        }
      }
    ]
  },
  {
    path: "/",
    component: Layout,
    // redirect: "/",
    meta: {
      title: "任务集合",
      svgIcon: "helpFilled",
      affix: true
    },
    children: [
      // 垃圾检测模块
      {
        path: "infer",
        component: () => import("@/views/infer/index.vue"),
        name: "Infer",
        meta: {
          title: "模型推理",
          svgIcon: "infer",
          affix: true
        }
      },
      {
        path: "infer_local",
        component: () => import("@/views/infer_local/index.vue"),
        name: "InferLocal",
        meta: {
          title: "模型推理（本地）",
          svgIcon: "infer",
          affix: true
        }
      },
      {
        path: "order_detection",
        component: () => import("@/views/order_detection/index.vue"),
        name: "orderDetection",
        meta: {
          title: "工单检测",
          svgIcon: "detection",
          affix: true
        }
      },
    ]
  },
  {
    path: "/link",
    component: Layout,
    // redirect: "/",
    meta: {
      title: "源码集合",
      svgIcon: "helpFilled",
      affix: true
    },
    children: [
      {
        path: "https://github.com/Graysonggg/DetectSegPlatform",
        component: () => {},
        name: "Link",
        meta: {
          title: "本项目源码",
          svgIcon: "Avatar"
        }
      },
      {
        path: "https://github.com/ultralytics/yolov5",
        component: () => {},
        name: "Link",
        meta: {
          title: "YOLOv5🚀",
          svgIcon: "link"
        }
      }
    ]
  },
  {
    path: "/menu",
    component: Layout,
    redirect: "/menu/menu1",
    name: "Menu",
    meta: {
      title: "敬请期待",
      svgIcon: "menu"
    },
    children: [
      {
        path: "menu1",
        component: () => import("@/views/menu/menu1/index.vue"),
        redirect: "/menu/menu1/menu1-1",
        name: "Menu1",
        meta: {
          title: "menu1"
        },
        children: [
          {
            path: "menu1-1",
            component: () => import("@/views/menu/menu1/menu1-1/index.vue"),
            name: "Menu1-1",
            meta: {
              title: "menu1-1"
            }
          },
          {
            path: "menu1-2",
            component: () => import("@/views/menu/menu1/menu1-2/index.vue"),
            redirect: "/menu/menu1/menu1-2/menu1-2-1",
            name: "Menu1-2",
            meta: {
              title: "menu1-2"
            },
            children: [
              {
                path: "menu1-2-1",
                component: () => import("@/views/menu/menu1/menu1-2/menu1-2-1/index.vue"),
                name: "Menu1-2-1",
                meta: {
                  title: "menu1-2-1"
                }
              },
              {
                path: "menu1-2-2",
                component: () => import("@/views/menu/menu1/menu1-2/menu1-2-2/index.vue"),
                name: "Menu1-2-2",
                meta: {
                  title: "menu1-2-2"
                }
              }
            ]
          },
          {
            path: "menu1-3",
            component: () => import("@/views/menu/menu1/menu1-3/index.vue"),
            name: "Menu1-3",
            meta: {
              title: "menu1-3"
            }
          }
        ]
      },
      {
        path: "menu2",
        component: () => import("@/views/menu/menu2/index.vue"),
        name: "Menu2",
        meta: {
          title: "menu2"
        }
      }
    ]
  }
  
]

/**
 * 动态路由
 * 用来放置有权限 (Roles 属性) 的路由
 * 必须带有 Name 属性
 */
export const asyncRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    component: Layout,
    meta: {
      roles: ["admin"],
      title: "配置管理",
      elIcon: "Grid"
    },
    children: [
      {
        path: "user-manage",
        component: () => import("@/views/manage/user/index.vue"),
        name: "UserManage",
        meta: {
          title: "用户管理",
          elIcon: "Grid"
        }
      },
      {
        path: "task-type-manage",
        component: () => import("@/views/manage/task_type/index.vue"),
        name: "TaskTypeManage",
        meta: {
          title: "任务类型管理",
          elIcon: "Grid"
        }
      },
      {
        path: "task-manage",
        component: () => import("@/views/manage/task/index.vue"),
        name: "TaskManage",
        meta: {
          title: "任务管理",
          elIcon: "Grid"
        }
      },
      {
        path: "flow-manage",
        component: () => import("@/views/manage/flow/index.vue"),
        name: "FlowManage",
        meta: {
          title: "工作流管理",
          elIcon: "Grid"
        }
      },
      {
        path: "release-manage",
        component: () => import("@/views/manage/release/index.vue"),
        name: "ReleaseManage",
        meta: {
          title: "版本管理",
          elIcon: "Grid"
        }
      },
      {
        path: "weight-manage",
        component: () => import("@/views/manage/weight/index.vue"),
        name: "WeightManage",
        meta: {
          title: "权重管理",
          elIcon: "Grid"
        }
      },
    ]
  },
  {
    path: "/permission",
    component: Layout,
    redirect: "/permission/page",
    name: "Permission",
    meta: {
      roles: ["admin"] // 可以在根路由中设置角色
      // alwaysShow: true // 将始终显示根菜单
    },
    children: [
      {
        path: "page",
        component: () => import("@/views/permission/page.vue"),
        name: "PagePermission",
        meta: {
          title: "切换权限",
          svgIcon: "lock"
        }
      }
    ]
  },
  {
    path: "/:pathMatch(.*)*", // Must put the 'ErrorPage' route at the end, 必须将 'ErrorPage' 路由放在最后
    redirect: "/404",
    name: "ErrorPage",
    meta: {
      hidden: true
    }
  }
]

const router = createRouter({
  history:
    import.meta.env.VITE_ROUTER_HISTORY === "hash"
      ? createWebHashHistory(import.meta.env.VITE_PUBLIC_PATH)
      : createWebHistory(import.meta.env.VITE_PUBLIC_PATH),
  routes: constantRoutes
})

/** 重置路由 */
export function resetRouter() {
  // 注意：所有动态路由路由必须带有 Name 属性，否则可能会不能完全重置干净
  try {
    router.getRoutes().forEach((route) => {
      const { name, meta } = route
      if (name && meta.roles?.length) {
        router.hasRoute(name) && router.removeRoute(name)
      }
    })
  } catch (error) {
    // 强制刷新浏览器也行，只是交互体验不是很好
    window.location.reload()
  }
}

export default router
