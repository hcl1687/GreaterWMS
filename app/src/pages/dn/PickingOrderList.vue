<template>
  <q-list bordered padding>
    <q-item>
      <q-item-section>
        <q-item-label overline>{{ $t('order.pickingorderlist') }}</q-item-label>
        <q-item-label caption>{{ $t('order.pickingorderlist_tip') }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator spaced/>
    <template v-for="(item, index) in tablelist" :key="index">
      <q-item>
        <q-item-section @click="toDetailLine(item)">
          <q-item-label>{{ item.dn_code }}</q-item-label>
          <q-item-label caption lines="2">
            {{ $t('order.posting_number') }}: {{ item.posting_number }}
          </q-item-label>
        </q-item-section>
        <q-item-section side top>
          <q-item-label caption>{{ item.shop?.shop_type }}</q-item-label>
           <q-item-label caption>{{ item.shop?.shop_name }}</q-item-label>
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
  name: 'PickingOrderList',
  data () {
    return {
    }
  },
  setup () {
    const $store = useStore()
    const $router = useRouter()
    const $q = useQuasar()
    const requestauth = ref(0)
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
      const from = new Date()
      from.setHours(0)
      from.setMinutes(0)
      from.setSeconds(0)
      from.setMilliseconds(0)
      const to = new Date()
      to.setHours(23)
      to.setMinutes(59)
      to.setSeconds(59)
      to.setMilliseconds(0)

      const range = `${from.toISOString()},${to.toISOString()}`
      apiurl.value = `${baseurl.value}/shoporder/pickinglistfilter/?shipment_time__range=${range}`
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

    function toDetailLine(e) {
      if (!e.order_label) {
        $q.notify({
          type: 'negative',
          message: t('order.no_order_label')
        })
        return
      }

      dndata.value = e.dn_code
      scanmode.value = 'DN'
      oldlink.value = 'pickingorderlist'
      newlink.value = 'pickingorderdetail'
      $router.push({
        name: 'pickingorderdetail',
        query: {
          order_label: e.order_label
        }
      })
    }

    watch (bar_scanned,(newValue,oldValue)=>{
      if (scanmode.value === 'DN') {
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
        InitData('')
      }
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
      toDetailLine,
      error1: t('notice.mobile_dn.notice16')
    }
  }
})
</script>
