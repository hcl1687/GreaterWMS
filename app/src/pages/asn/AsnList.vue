<template>
  <q-list bordered padding>
      <q-item>
        <q-item-section>
          <q-item-label overline>{{ $t('notice.mobile_asn.notice1') }}</q-item-label>
          <q-item-label caption>{{ $t('notice.mobile_asn.notice2') }}</q-item-label>
        </q-item-section>
      </q-item>
      <q-separator spaced />
      <template v-for="(item, index) in tablelist" :key="index">
        <q-item>
          <q-item-section @click="DetailLine(item.asn_code)">
            <q-item-label>{{ item.asn_code }}</q-item-label>
            <q-item-label caption lines="2">
              {{ $t('notice.mobile_asn.notice3') }}{{ item.supplier }}
            </q-item-label>
          </q-item-section>
          <q-item-section side top>
            <q-item-label caption>{{ $t('notice.mobile_asn.notice4') }}{{ item.total_cost }}</q-item-label>
            <q-item-label caption>{{ $t('notice.mobile_asn.notice5') }}{{ item.asn_status }}</q-item-label>
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
import { useRoute, useRouter } from "vue-router";

export default defineComponent({
  name: 'ASNList',
  data () {
    return {
    }
  },
  setup () {
    const $store = useStore()
    const $router = useRouter()
    const $route = useRoute()
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
    const screenscroll = computed({
      get: () => $store.state.screenchange.screenscroll,
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

    function DetailLine(e) {
      asndata.value = e
      scanmode.value = 'ASN'
      oldlink.value = 'asnlist'
      newlink.value = 'asndetail'
      $router.push({ name: 'asndetail' })
    }

    function getTableData (e) {
      axios.get(apiurl.value + e,
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
            console.log(apiurlnext.value)
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

    watch (screenscroll,(newValue,oldValue)=>{
      if (newValue >= 0.95) {
        if (apiurlnext.value !== null) {
          apiurl.value = apiurlnext.value
          console.log(2, apiurl.value)
          requestauth.value = 1
        }
      } else {
        requestauth.value = 0
      }
    })

    watch (requestauth,(newValue,oldValue)=>{
      if (newValue === 1) {
        getTableData('')
      }
    })

    watch (bar_scanned,(newValue,oldValue)=>{
      if (scanmode.value === 'ASN') {
        DetailLine(scandata.value)
      }
    })

    onMounted(() => {
      if (authin.value === '0') {
        $q.notify({
          type: 'negative',
          message: t('notice.mobile_userlogin.notice9')
        })
      } else {
        scanmode.value = 'ASN'
        apiurl.value = baseurl.value + '/asn/list/'
        asndata.value = ''
        tablelist.value = []
        getTableData('')
      }
    })

    return {
      t,
      fab1,
      fab2,
      fab3,
      fab4,
      oldlink,
      newlink,
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
      DetailLine
    }
  }
})
</script>
