import Print from 'vue-print-nb'
import VDistpicker from 'v-distpicker'
import * as Utils from '../utils'

export default async ({ app, router, store, Vue }) => {
  Vue.component('v-distpicker', VDistpicker)
  Vue.use(Print)
  Vue.mixin({
    methods: {
      ...Utils
    }
  })

  console.log('Welcome To GreaterWMS')
  console.log('Home Page ------ https://www.56yhz.com/')
  console.log('Demo Page ------ https://production.56yhz.com/')
  console.log('Gitee Page ------ https://gitee.com/Singosgu/GreaterWMS')
  console.log('GitHub Page ------ https://github.com/Singosgu/GreaterWMS')
}
