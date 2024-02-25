<template>
  <q-list bordered padding>
    <q-item>
      <q-item-section>
        <q-item-label overline>{{ $t('order.picking_detail') }}</q-item-label>
        <q-item-label caption>{{ $t('notice.mobile_dn.notice11') }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator spaced/>
    <template v-for="(item, index) in tablelist" :key="index">
      <q-item>
        <q-item-section>
          <q-item-label>{{ item.dn_code }}</q-item-label>
          <q-item-label caption lines="2">
            {{ $t('goods.view_goodslist.goods_code') }}: {{ item.goods_code }}
          </q-item-label>
        </q-item-section>
        <q-item-section side top>
          <q-item-label caption>{{ $t('notice.mobile_dn.notice14') }}{{ item.bin_name }}</q-item-label>
          <q-item-label caption>{{ $t('notice.mobile_dn.notice15') }}{{ item.pick_qty }}</q-item-label>
          <q-item-label caption>{{ $t('order.current_pick') }}{{ item.current_scanned_qty }}</q-item-label>
        </q-item-section>
      </q-item>
      <q-separator v-show="index + 1 !== tablelist.length" spaced inset="item" />
    </template>
  </q-list>
</template>

<script>
import { computed, defineComponent, onMounted, ref, watch } from 'vue'
import { useStore } from "vuex";
import { useQuasar } from "quasar";
import axios from 'axios';
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";

export default defineComponent({
  name: 'PickingOrderDetail',
  data () {
    return {
    }
  },
  setup () {
    const $store = useStore()
    const $router = useRouter()
    const $q = useQuasar()
    const requestauth = ref(0)
    const submitdata = ref({})
    const dninfo = ref({})
    const currentScannedQty = ref({})
    const { t } = useI18n()
    const fab1 = computed({
      get: () => $store.state.fabchange.fab1,
    })
    const fab2 = computed({
      get: () => $store.state.fabchange.fab2,
    })
    const fab3 = computed({
      get: () => $store.state.fabchange.fab3,
    })
    const fab4 = computed({
      get: () => $store.state.fabchange.fab4,
    })
    const screenscroll = computed({
      get: () => $store.state.screenchange.screenscroll,
    })
    const oldlink = computed({
      get: () => $store.state.linkchange.oldlink,
      set: val => {
        $store.commit('linkchange/OldLinkChanged', val)
      }
    })
    const newlink = computed({
      get: () => $store.state.linkchange.newlink,
      set: val => {
        $store.commit('linkchange/NewLinkChanged', val)
      }
    })
    const authin = computed({
      get: () => $store.state.loginauth.authin,
    })
    const login_name = computed({
      get: () => $store.state.loginauth.login_name,
    })
    const operator = computed({
      get: () => $store.state.loginauth.operator,
    })
    const access_token = computed({
      get: () => $store.state.loginauth.access_token,
    })
    const openid = computed({
      get: () => $store.state.settings.openid,
    })
    const lang = computed({
      get: () => $store.state.langchange.lang,
    })
    const baseurl = computed({
      get: () => $store.state.settings.server,
    })
    const scandata = computed({
      get: () => $store.state.scanchanged.scandata,
      set: val => {
        $store.commit('scanchanged/ScanChanged', val)
      }
    })
    const datadetail = computed({
      get: () => $store.state.scanchanged.datadetail,
      set: val => {
        $store.commit('scanchanged/ScanDataChanged', val)
      }
    })
    const asndata = computed({
      get: () => $store.state.scanchanged.asndata,
      set: val => {
        $store.commit('scanchanged/ASNDataChanged', val)
      }
    })
    const dndata = computed({
      get: () => $store.state.scanchanged.dndata,
      set: val => {
        $store.commit('scanchanged/DNDataChanged', val)
      }
    })
    const bindata = computed({
      get: () => $store.state.scanchanged.bindata,
      set: val => {
        $store.commit('scanchanged/BinDataChanged', val)
      }
    })
    const tablelist = computed({
      get: () => $store.state.scanchanged.tablelist,
      set: val => {
        $store.commit('scanchanged/TableDataChanged', val)
      }
    })
    const scanmode = computed({
      get: () => $store.state.scanchanged.scanmode,
      set: val => {
        $store.commit('scanchanged/ScanModeChanged', val)
      }
    })
    const bar_scanned = computed({
      get: () => $store.state.scanchanged.bar_scanned,
    })
    const apiurl = computed({
      get: () => $store.state.scanchanged.apiurl,
      set: val => {
        $store.commit('scanchanged/ApiUrlChanged', val)
      }
    })
    const apiurlnext = computed({
      get: () => $store.state.scanchanged.apiurlnext,
      set: val => {
        $store.commit('scanchanged/ApiUrlNextChanged', val)
      }
    })
    const apiurlprevious = computed({
      get: () => $store.state.scanchanged.apiurlprevious,
      set: val => {
        $store.commit('scanchanged/ApiUrlPreviousChanged', val)
      }
    })

    function sslCheck (e) {
      if (e !== null) {
        var baseurlCheck = baseurl.value.split(':')
        var urlCheck = e.split(':')
        if (urlCheck.length === 2)
          if (baseurlCheck[0] !== urlCheck[0]) {
            return baseurlCheck[0] + ':' + urlCheck[1]
          } else {
            return e
          }
        else if (urlCheck.length === 3) {
          if (baseurlCheck[0] !== urlCheck[0]) {
            return baseurlCheck[0] + ':' + urlCheck[1] + ':' + urlCheck[2]
          } else {
            return e
          }
        }
      } else {
        return null
      }
    }

    function InitData (e) {
      tablelist.value = []
      apiurl.value = `${baseurl.value}/dn/pickinglistfilter/?pick_qty__gt=0&picking_status=0`
      getTableData(e)
    }

    function getTableData (e) {
      axios.get(apiurl.value + e,
        {
          headers: {
            "Content-Type": 'application/json, charset="utf-8"',
            "token" : openid.value,
            "language" : lang.value,
            "operator" : operator.value,
            "Authorization": `Bearer ${access_token.value}`,
          }
        }).then(res => {
          if (!res.data.detail) {
            var tablepush = []
            tablelist.value.forEach(i => {
              tablepush.push(i)
            })
            res.data.results.forEach(item => {
              tablepush.push(item)
            })
            tablelist.value = tablepush
            apiurlprevious.value = sslCheck(res.data.previous)
            apiurlnext.value = sslCheck(res.data.next)
          } else {
            $q.notify({
              type: 'negative',
              message: t('notice.mobile_scan.notice1')
            })
          }
        }).catch(err => {
          $q.notify({
            type: 'negative',
            message: t('notice.mobile_scan.notice3')
          })
      })
    }
    function dataSubmit (e) {
      submitdata.value = JSON.parse(JSON.stringify(e))
    }

    async function submitData (e) {
      apiurl.value = baseurl.value + '/dn/list/?dn_code=' + submitdata.value.dn_code
      return axios.get(apiurl.value,
        {
          headers: {
            "Content-Type": 'application/json, charset="utf-8"',
            "token" : openid.value,
            "language" : lang.value,
            "operator" : operator.value,
            "Authorization": `Bearer ${access_token.value}`,
          }
        }).then(res => {
          if (!res.data.detail) {
            const dnData = res.data.results[0]
            dninfo.value = dnData
            return dnData
          } else {
            $q.notify({
              type: 'negative',
              message: t('notice.mobile_scan.notice1')
            })
          }
        }).catch(err => {
          $q.notify({
            type: 'negative',
            message: t('notice.mobile_scan.notice3')
          })
      })
    }

    async function submitRes (e) {
      if (submitdata.value.picked_qty === '') {
        $q.notify({
          type: 'negative',
          message: t('notice.mobile_dn.notice12')
        })
      } else {
        apiurl.value = baseurl.value + '/dn/picked/' + e.id + '/'
        const resData = {
          creater: login_name.value,
          customer: e.customer,
          dn_code: e.dn_code,
          goodsData: [
            submitdata.value
          ]
        }
        axios.put(apiurl.value, resData,
          {
            headers: {
              "Content-Type": 'application/json',
              "token" : openid.value,
              "language" : lang.value,
              "operator" : operator.value,
              "Authorization": `Bearer ${access_token.value}`,
            }
          }).then(res => {
          if (!res.data.detail) {
            $q.notify({
              message: t('notice.mobile_dn.notice13')
            })
          }

          let filter = ''
          if (dndata.value) {
            filter = `&dn_code=${dndata.value}`
          }
          // InitData(filter)
        }).catch(err => {
          $q.notify({
            message: t('notice.network_error'),
          })
        })
      }
    }

    async function pickGoods (goods_code) {
      const items = tablelist.value.filter(item => item.goods_code === goods_code)
      if (items.length === 0) {
        $q.notify({
          type: 'negative',
          message: t('order.goods_code_not_exist')
        })
        return
      }

      const pickingItem = items[0]
      const currentScannedQtyObj = currentScannedQty.value
      if (currentScannedQtyObj[pickingItem.goods_code] === undefined) {
        currentScannedQtyObj[pickingItem.goods_code] = 0
      }

      if (currentScannedQtyObj[pickingItem.goods_code] < pickingItem.pick_qty){
        currentScannedQtyObj[pickingItem.goods_code] += 1
      }

      if (currentScannedQtyObj[pickingItem.goods_code] >= pickingItem.pick_qty) {
        // have all picked
        dataSubmit(pickingItem)
        await submitData()
        if (dninfo.value) {
          await submitRes(dninfo.value)
        }
      }

      // dispatch if all items are picked.
      const isAllPicked = tablelist.value.every(item => currentScannedQtyObj[item.goods_code] !== undefined && 
        currentScannedQtyObj[item.goods_code] === item.pick_qty)
      if (isAllPicked) {
        if (dninfo.value) {
          dispatchDataSubmit(dninfo.value)
        }
      }
    }

    function dispatchDataSubmit (e) {
      apiurl.value = baseurl.value + '/dn/dispatch/' + e.id + '/'
      const resData = {
        dn_code: e.dn_code,
        driver: '-'
      }
      axios.post(apiurl.value, resData,
        {
          headers: {
            "Content-Type": 'application/json',
            "token" : openid.value,
            "language" : lang.value,
            "operator" : operator.value,
            "Authorization": `Bearer ${access_token.value}`,
          }
        }).then(res => {
        if (!res.data.detail) {
          $q.notify({
            message: t('notice.mobile_dn.notice13')
          })
        }

        $router.push({ name: oldlink.value })
      }).catch(err => {
        $q.notify({
          message: t('notice.network_error'),
        })
      })
    }

    watch (bar_scanned,(newValue,oldValue)=>{
      if (scanmode.value === 'GOODS') {
        pickGoods(scandata.value)
      } else if (scanmode.value === 'DN') {
        InitData('&dn_code=' + scandata.value)
      }
    })

    watch (screenscroll,(newValue, oldValue)=>{
      if (newValue >= 0.95) {
        if (apiurlnext.value !== null) {
          apiurl.value = apiurlnext.value
          requestauth.value = 1
        }
      } else {
        requestauth.value = 0
      }
    })
   watch (requestauth,(newValue,oldValue)=>{
      if (newValue === 1) {
         if (authin.value === '0') {
          $q.notify({
            type: 'negative',
            message: t('notice.mobile_userlogin.notice9')
          })
        } else {
          getTableData('')
        }
      }
    })

    onMounted(() => {
      if (authin.value === '0') {
        $q.notify({
          type: 'negative',
          message: t('notice.mobile_userlogin.notice9')
        })
      } else {
        scanmode.value = 'DN'
        let filter = ''
        if (dndata.value) {
          filter = `&dn_code=${dndata.value}`
        }
        InitData(filter)
      }

      // const fileTransfer = new FileTransfer()
      // const uri = encodeURI(`${baseurl.value}/media/labels/YADE_411145170.pdf`)
      // fileTransfer.download(
      //     uri,
      //     cordova.file.dataDirectory + "file.pdf",
      //     function(entry) {
      //         alert('ddddd')
      //     },
      //     function(error) {
      //         alert('sss')
      //     },
      //     false,
      //     {}
      // );
    })

    return {
      t,
      fab1,
      fab2,
      fab3,
      fab4,
      screenscroll,
      authin,
      login_name,
      openid,
      operator,
      access_token,
      lang,
      requestauth,
      baseurl,
      apiurl,
      apiurlnext,
      apiurlprevious,
      scandata,
      datadetail,
      tablelist,
      asndata,
      dndata,
      bindata,
      scanmode,
      bar_scanned,
      submitdata,
      dataSubmit,
      submitData,
      error1: t('notice.mobile_dn.notice16')
    }
  }
})
</script>
