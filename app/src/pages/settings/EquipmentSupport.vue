<template>
  <q-list bordered padding>
    <q-item>
      <q-item-section>
        <q-item-label overline>{{ $t('notice.equipment.notice1') }}</q-item-label>
        <q-item-label caption>{{ $t('notice.equipment.notice2') }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator spaced/>
    <q-item clickable v-ripple>
      <q-item-section>IOS</q-item-section>
      <q-item-section thumbnail>
        <img src="statics/equipment/apple.png" style="margin-right: 20px">
      </q-item-section>
    </q-item>
    <q-separator />
    <q-item clickable v-ripple>
      <q-item-section>Android</q-item-section>
      <q-item-section thumbnail>
        <img src="statics/equipment/android.png" style="margin-right: 20px">
      </q-item-section>
    </q-item>
    <q-separator />
    <q-item clickable v-ripple>
      <q-item-section>Zebra</q-item-section>
      <q-item-section thumbnail>
        <img src="statics/equipment/zebra.png" style="margin-right: 20px">
      </q-item-section>
    </q-item>
    <q-separator />
    <q-item clickable v-ripple>
      <q-item-section>iData</q-item-section>
      <q-item-section thumbnail>
        <img src="statics/equipment/idata.jpg" style="margin-right: 20px">
      </q-item-section>
    </q-item>
<!--    <q-separator />-->
<!--    <q-item clickable v-ripple>-->
<!--      <q-item-section>Urovo</q-item-section>-->
<!--      <q-item-section thumbnail>-->
<!--        <img src="statics/equipment/urovo.png" style="margin-right: 20px">-->
<!--      </q-item-section>-->
<!--    </q-item>-->
    <q-separator />
    <q-item clickable v-ripple>
      <q-item-section>Seuic</q-item-section>
      <q-item-section thumbnail>
        <img src="statics/equipment/seuic.jpg" style="margin-right: 20px">
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script>
import { computed, defineComponent, onMounted, ref, watch } from 'vue'
import { useStore } from "vuex";
import { useQuasar } from "quasar";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router/dist/vue-router";

export default defineComponent({
  name: 'EquipmentSupport',
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

    watch (bar_scanned,(newValue,oldValue)=>{

    })

    watch (screenscroll,(newValue,oldValue)=>{
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
      bar_scanned
    }
  }
})
</script>
