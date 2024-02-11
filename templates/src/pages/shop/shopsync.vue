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
            <q-btn :label="$t('shopsku.batch_sync')" icon="link" :disable="selected.length === 0" @click="batchSyncData()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsku.batch_sync_tip') }}</q-tooltip>
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
            <q-td key="shop_name" :props="props">{{ props.row.shop.shop_name }}</q-td>
            <q-td key="platform_id" :props="props" style="max-width: 300px; white-space: normal;">{{ props.row.platform_id }}</q-td>
            <q-td key="platform_sku" :props="props">{{ props.row.platform_sku }}</q-td>
            <q-td key="goods_code" :props="props">{{ props.row.goods_code }}</q-td>
            <q-td key="action" :props="props" style="width: 175px">
              <q-btn
                round
                flat
                push
                color="dark"
                icon="delete"
                @click="syncData(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('sync_tip') }}</q-tooltip>
              </q-btn>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </transition>
    <template>
        <div v-show="max !== 0" class="q-pa-lg flex flex-center">
           <div>{{ total }} </div>
          <q-pagination
            v-model="current"
            color="black"
            :max="max"
            :max-pages="6"
            boundary-links
            @click="getList()"
          />
          <div>
            <input
              v-model="paginationIpt"
              @blur="changePageEnter"
              @keyup.enter="changePageEnter"
              style="width: 60px; text-align: center"
            />
          </div>
        </div>
        <div v-show="max === 0" class="q-pa-lg flex flex-center">
          <q-btn flat push color="dark" :label="$t('no_data')"></q-btn>
        </div>
    </template>
    <q-dialog v-model="syncForm">
      <q-card class="shadow-24">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ $t('sync_title') }}</div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip content-class="bg-amber text-black shadow-4">{{ $t('index.close') }}</q-tooltip>
          </q-btn>
        </q-bar>
        <q-card-section style="max-height: 325px; width: 400px" class="scroll">{{ $t('sync-confirm-tip') }}</q-card-section>
        <div style="float: right; padding: 15px 15px 15px 0">
          <q-btn color="white" text-color="black" style="margin-right: 25px" @click="syncDataCancel()">{{ $t('cancel') }}</q-btn>
          <q-btn color="primary" @click="syncDataSubmit()">{{ $t('submit') }}</q-btn>
        </div>
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
      pathname: 'shopsku/sync/',
      pathname_previous: '',
      pathname_next: '',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      selected: [],
      columns: [
        { name: 'index', label: '#', field: 'index', align: 'center' },
        { name: 'shop_name', label: this.$t('shop.shop_name'), align: 'center', field: 'shop.shop_name' },
        { name: 'platform_id', label: this.$t('shopsku.platform_id'), field: 'platform_id', align: 'center' },
        { name: 'platform_sku', label: this.$t('shopsku.platform_sku'), field: 'platform_sku', align: 'center' },
        { name: 'goods_code', label: this.$t('shopsku.goods_code'), field: 'goods_code', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'center' }
      ],
      pagination: {
        page: 1,
        rowsPerPage: PAGE_SIZE
      },
      syncForm: false,
      current: 1,
      max: 0,
      total: 0,
      paginationIpt: 1,
      shop_id: ''
    }
  },
  methods: {
    getList (direction) {
      var _this = this
      getauth(`${_this.pathname}?shop_id=${_this.shop_id}&page=${_this.current}`, {})
        .then(res => {
          res.results.forEach((item, index) => (item.index = index + 1))
          _this.table_list = res.results
          _this.total = res.count
          if (res.count === 0) {
            _this.max = 0
          } else {
            if (Math.ceil(res.count / 30) === 1) {
              _this.max = 0
            } else {
              _this.max = Math.ceil(res.count / 30)
            }
          }

          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    changePageEnter (e) {
      if (Number(this.paginationIpt) < 1) {
        this.current = 1
        this.paginationIpt = 1
      } else if (Number(this.paginationIpt) > this.max) {
        this.current = this.max
        this.paginationIpt = this.max
      } else {
        this.current = Number(this.paginationIpt)
      }
      this.getList()
    },
    getListPrevious () {
      var _this = this
      getauth(_this.pathname_previous, {})
        .then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    getListNext () {
      var _this = this
      getauth(_this.pathname_next, {})
        .then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
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
      _this.syncGoodscode = this.selected.map(item => item.goods_code)
    },
    syncDataSubmit () {
      var _this = this

      const data = {
        shop: _this.shop_id,
        goods_code: _this.syncGoodscode
      }
      postauth(_this.pathname, data)
        .then(res => {
          _this.syncDataCancel()
          _this.getList()
          _this.$q.notify({
            message: 'Success Sync Data',
            icon: 'check',
            color: 'green'
          })
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
    // if (_this.$q.platform.is.electron) {
    //   _this.height = String(_this.$q.screen.height - 290) + 'px'
    // } else {
    //   _this.height = _this.$q.screen.height - 290 + '' + 'px'
    // }
  },
  updated () {
  },
  destroyed () {
  }
}
</script>
