<template>
  <div>
    <transition appear enter-active-class="animated fadeIn">
      <q-table
        id="table"
        class="my-sticky-header-column-table shadow-24"
        :data="table_list"
        row-key="id"
        :separator="separator"
        :loading="loading"
        :columns="columns"
        selection="multiple"
        :selected.sync="selected"
        hide-bottom
        :pagination.sync="pagination"
        no-data-label="No data"
        no-results-label="No data you want"
        :table-style="{ height: height }"
        flat
        bordered
      >
        <template v-slot:top>
          <q-btn-group push>
            <q-btn :label="$t('back')" icon="arrow_back" @click="back()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('back') }}</q-tooltip>
            </q-btn>
            <q-btn :label="$t('refresh')" icon="refresh" @click="reFresh()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('refreshtip') }}</q-tooltip>
            </q-btn>
            <q-btn :label="$t('shopsync.batch_sync')" icon="ios_share" :disable="selected.length === 0" @click="batchSyncData()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsync.batch_sync_tip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
        </template>
        <template v-slot:header-selection="scope">
          <q-checkbox v-model="scope.selected" />
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td>
              <q-checkbox v-model="props.selected" color="primary" />
            </q-td>
            <q-td key="index" :props="props" style="max-width: 300px; white-space: normal;">{{ props.row.index }}</q-td>
            <q-td key="image" :props="props" style="width: 150px;">
              <q-img
                :src="props.row.image"
                spinner-color="white"
                style="height: 140px; max-width: 150px"
              />
            </q-td>
            <q-td key="name" :props="props" style="max-width: 300px; white-space: normal;">{{ props.row.name }}</q-td>
            <q-td key="shop_name" :props="props">{{ props.row.shop_name }}</q-td>
            <q-td key="platform_sku" :props="props">{{ props.row.platform_sku }}</q-td>
            <q-td key="goods_code" :props="props">{{ props.row.goods_code }}</q-td>
            <q-td key="platform_stock" :props="props">{{ props.row.platform_stock }}</q-td>
            <q-td key="sys_stock" :props="props">{{ props.row.sys_stock }}</q-td>
            <q-td key="sync_status" :props="props">{{ getSyncStatusText(props.row.sync_status) }}</q-td>
            <q-td key="sync_time" :props="props">{{ showLocalTime(props.row.sync_time) }}</q-td>
            <q-td key="sync_message" :props="props">{{ props.row.sync_message }}</q-td>
            <q-td key="action" :props="props" style="width: 175px">
              <q-btn
                round
                flat
                push
                color="dark"
                icon="ios_share"
                :disable="!props.row.sys_id"
                @click="syncData(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsync.sync_tip') }}</q-tooltip>
              </q-btn>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </transition>
    <template>
        <div v-show="max !== 0" class="q-pa-lg flex flex-center">
           <div style="margin-right: 5px;">{{ total }} </div>
          <q-btn-group push>
            <q-btn :label="$t('shopsku.previous')" icon="arrow_back_ios" :disable="curr_last_id_index <= 0" @click="handlePre()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsku.previous_tip') }}</q-tooltip>
            </q-btn>
            <q-btn :label="$t('shopsku.next')" icon="arrow_forward_ios" :disable="curr_last_id_index >= max - 1" @click="handleNext()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsku.next_tip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
        </div>
        <div v-show="max === 0" class="q-pa-lg flex flex-center">
          <q-btn flat push color="dark" :label="$t('no_data')"></q-btn>
        </div>
    </template>
    <q-dialog v-model="syncForm">
      <q-card class="shadow-24">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ $t('shopsync.sync_title') }}</div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip content-class="bg-amber text-black shadow-4">{{ $t('index.close') }}</q-tooltip>
          </q-btn>
        </q-bar>
        <q-card-section style="max-height: 325px; width: 400px" class="scroll">{{ $t('shopsync.sync_confirm_tip') }}</q-card-section>
        <div style="float: right; padding: 15px 15px 15px 0">
          <q-btn color="white" text-color="black" style="margin-right: 25px" @click="syncDataCancel()">{{ $t('cancel') }}</q-btn>
          <q-btn color="primary" @click="syncDataSubmit()">{{ $t('submit') }}</q-btn>
        </div>
      </q-card>
    </q-dialog>
    <q-dialog v-model="progressForm">
      <q-card class="shadow-24">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ $t('shopsync.progress_title') }}</div>
          <q-space />
          <q-btn dense flat icon="close" @click="closeProgressForm()">
            <q-tooltip content-class="bg-amber text-black shadow-4">{{ $t('index.close') }}</q-tooltip>
          </q-btn>
        </q-bar>
        <q-card-section style="max-height: 325px; width: 400px" class="scroll">{{ $t('shopsync.progress_tip') }}</q-card-section>
        <q-linear-progress indeterminate />
      </q-card>
    </q-dialog>
  </div>
</template>
<router-view />

<script>
import { getauth, postauth, patchauth, deleteauth, getfile } from 'boot/axios_request'
import { date, exportFile, LocalStorage } from 'quasar'
const PAGE_SIZE = 100

export default {
  name: 'Pageshopsync',
  data () {
    return {
      openid: '',
      login_name: '',
      authin: '0',
      pathname: 'shopsku/',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      selected: [],
      columns: [
        { name: 'index', label: '#', field: 'index', align: 'center' },
        { name: 'image', label: this.$t('shopsku.image'), field: 'image', align: 'center' },
        { name: 'name', required: true, label: this.$t('shopsku.name'), align: 'center', field: 'name' },
        { name: 'shop_name', label: this.$t('shop.shop_name'), align: 'center', field: 'shop_name' },
        { name: 'platform_sku', label: this.$t('shopsku.platform_sku'), field: 'platform_sku', align: 'center' },
        { name: 'goods_code', label: this.$t('shopsku.goods_code'), field: 'goods_code', align: 'center' },
        { name: 'platform_stock', label: this.$t('shopsku.platform_stock'), field: 'platform_stock', align: 'center' },
        { name: 'sys_stock', label: this.$t('shopsku.sys_stock'), field: 'sys_stock', align: 'center' },
        { name: 'sync_status', label: this.$t('shopsku.sync_status'), field: 'sync_status', align: 'center' },
        { name: 'sync_time', label: this.$t('shopsku.sync_time'), field: 'sync_time', align: 'center' },
        { name: 'sync_message', label: this.$t('shopsku.sync_message'), field: 'sync_message', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'center' }
      ],
      pagination: {
        page: 1,
        rowsPerPage: PAGE_SIZE
      },
      syncForm: false,
      progressForm: false,
      syncGoodscode: [],
      last_id_list: [''],
      curr_last_id_index: 0,
      max: 0,
      total: 0,
      shop_id: '',
      shopDetail: {},
      supplierDetail: {},
      progressTimer: null
    }
  },
  methods: {
    getList (direction) {
      var _this = this
      _this.pathname + '?shop_id=' + _this.shop_id
      const last_id_index = direction === 'next'
        ? _this.curr_last_id_index + 1
        : direction === 'pre'
          ? _this.curr_last_id_index - 1
          : _this.curr_last_id_index
      if (last_id_index < 0 || last_id_index >= _this.last_id_list.length) {
        return
      }

      const last_id = _this.last_id_list[last_id_index]
      getauth(`${_this.pathname}?shop_id=${_this.shop_id}&last_id=${last_id}`, {})
        .then(res => {
          res.results.forEach((item, index) => (item.index = index + 1))
          _this.table_list = res.results
          _this.total = res.count

          _this.curr_last_id_index = last_id_index
          _this.last_id_list[last_id_index+1] = res.last_id

          if (res.count === 0) {
            _this.max = 0
          } else {
            if (Math.ceil(res.count / PAGE_SIZE) === 1) {
              _this.max = 0
            } else {
              _this.max = Math.ceil(res.count / PAGE_SIZE)
            }
          }
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    reFresh () {
      var _this = this
      _this.getList()
    },
    syncData (e) {
      var _this = this

      _this.syncForm = true
      _this.syncGoodscode = [e.goods_code]
    },
    batchSyncData (e) {
      var _this = this
      _this.syncForm = true
      _this.syncGoodscode = this.selected.map(item => item.goods_code).filter(goods_code => goods_code)
    },
    syncDataSubmit () {
      var _this = this

      const data = {
        shop: _this.shop_id,
        goods_code: _this.syncGoodscode
      }
      postauth('shopsku/sync/', data)
        .then(res => {
          _this.syncDataCancel()
          const taskId = res && res.task_id || ''
          this.showProgressForm(taskId)
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    syncDataCancel () {
      var _this = this
      _this.syncForm = false
      _this.syncGoodscode = []
    },
    back () {
      this.$router.back()
    },
    getFieldRequiredMessage (field) {
      return this.$t('notice.field_required_error', { field })
    },
    handlePre () {
      this.selected = []
      this.getList('pre')
    },
    handleNext () {
      this.selected = []
      this.getList('next')
    },
    getSyncStatusText (sync_status) {
      switch(sync_status) {
        case 1:
          return this.$t('shopsync.status_success')
        case 2:
          return this.$t('shopsync.status_failed')
        default:
          return ''
      }
    },
    showProgressForm (taskId) {
      this.progressForm = true
      const handleTimer = async () => {
        const res = await this.getTaskStatus(taskId)
        if (res == 'SUCCESS') {
          this.closeProgressForm()
          this.getList()
          _this.$q.notify({
            message: 'Success Sync Data',
            icon: 'check',
            color: 'green'
          })
        } else {
          this.progressTimer = setTimeout(handleTimer, 1000)
        }
      }
      handleTimer()
    },
    closeProgressForm () {
      if (this.progressTimer) {
        clearTimeout(this.progressTimer)
        this.progressTimer = null
      }
      this.progressForm = false
    },
    async getTaskStatus (taskId) {
      const res = await getauth(`/shopsku/task/?task_id=${taskId}`, {})

      return res && res.state || ''
    }
  },
  created () {
    var _this = this
    _this.shop_id = _this.$route.params.shop_id || ''
    if (LocalStorage.has('openid')) {
      _this.openid = LocalStorage.getItem('openid')
    } else {
      _this.openid = ''
      LocalStorage.set('openid', '')
    }
    if (LocalStorage.has('login_name')) {
      _this.login_name = LocalStorage.getItem('login_name')
    } else {
      _this.login_name = ''
      LocalStorage.set('login_name', '')
    }
    if (LocalStorage.has('auth')) {
      _this.authin = '1'
      _this.getList()
    } else {
      _this.authin = '0'
    }
  },
  mounted () {
    var _this = this
    if (_this.$q.platform.is.electron) {
      _this.height = String(_this.$q.screen.height - 290) + 'px'
    } else {
      _this.height = _this.$q.screen.height - 290 + '' + 'px'
    }
  },
  updated () {
  },
  unmounted () {
    this.closeProgressForm()
  },
  destroyed () {
  }
}
</script>
