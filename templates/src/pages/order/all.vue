<template>
  <div>
    <transition appear enter-active-class="animated fadeIn">
      <q-table
        class="my-sticky-header-column-table shadow-24"
        :data="table_list"
        row-key="id"
        :separator="separator"
        :loading="loading"
        :filter="filter"
        :columns="columns"
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
            <q-btn
              :label="$t('order.fetch_order')"
              icon="add"
              @click="fetchOrder()"
            >
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('order.fetch_order_tip') }}</q-tooltip>
            </q-btn>
            <q-btn
              v-show="$q.localStorage.getItem('staff_type') !== 'Supplier' && $q.localStorage.getItem('staff_type') !== 'Customer'"
              :label="$t('refresh')"
              icon="refresh"
              @click="reFresh()"
            >
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('refreshtip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
          <q-space />
          <q-input outlined rounded dense debounce="300" color="primary" v-model="filter" :placeholder="$t('search')" @input="getSearchList()" @keyup.enter="getSearchList()">
            <template v-slot:append>
              <q-icon name="search" @click="getSearchList()" />
            </template>
          </q-input>
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td key="platform_id" :props="props">{{ props.row.platform_id }}</q-td>
            <q-td key="platform_warehouse_id" :props="props">{{ props.row.platform_warehouse_id }}</q-td>
            <q-td key="posting_number" :props="props">{{ props.row.posting_number }}</q-td>
            <q-td key="dn_code" :props="props">{{ props.row.dn_code }}</q-td>
            <q-td key="order_time" :props="props">{{ props.row.order_time }}</q-td>
            <q-td key="status" :props="props">{{ props.row.status }}</q-td>
            <q-td key="handle_status" :props="props">{{ props.row.handle_status }}</q-td>
            <q-td key="handle_message" :props="props">{{ props.row.handle_message }}</q-td>
            <q-td key="supplier" :props="props">{{ props.row.supplier }}</q-td>
            <q-td key="creater" :props="props">{{ props.row.creater }}</q-td>
            <q-td key="create_time" :props="props">{{ props.row.create_time }}</q-td>
            <q-td key="update_time" :props="props">{{ props.row.update_time }}</q-td>
            <q-td key="action" :props="props" style="width: 100px">
              <q-btn
                round
                flat
                push
                color="info"
                icon="visibility"
                @click="viewData(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('printthisasn') }}</q-tooltip>
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
    <q-dialog v-model="viewForm">
      <q-card id="printMe">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ viewdn }}</div>
          <q-space />
          {{ $t('outbound.dn') }}
        </q-bar>
        <q-markup-table>
          <thead>
            <tr>
              <th class="text-left">{{ $t('goods.view_goodslist.goods_code') }}</th>
              <th class="text-left">{{ $t('shopsku.platform_sku') }}</th>
              <th class="text-right">{{ $t('order.quantity') }}</th>
              <th class="text-right">Comments</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(view, index) in products_table" :key="index">
              <td class="text-left">{{ view.goods_code }}</td>
              <td class="text-right">{{ view.platform_sku }}</td>
              <td class="text-right">{{ view.quantity }}</td>
              <td class="text-right"></td>
            </tr>
          </tbody>
        </q-markup-table>
      </q-card>
      <div style="float: right; padding: 15px 15px 15px 0"><q-btn color="primary" icon="print" v-print="printObj">print</q-btn></div>
    </q-dialog>
  </div>
</template>
<router-view />

<script>
import { getauth, postauth } from 'boot/axios_request'
import { LocalStorage } from 'quasar'

export default {
  name: 'Pageorderlist',
  data () {
    return {
      openid: '',
      login_name: '',
      authin: '0',
      pathname: 'shoporder/',
      pathname_previous: '',
      pathname_next: '',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      products_table: [],
      columns: [
        { name: 'platform_id', required: true, label: this.$t('order.platform_id'), align: 'left', field: 'platform_id' },
        { name: 'platform_warehouse_id', label: this.$t('order.platform_warehouse_id'), field: 'platform_warehouse_id', align: 'center' },
        { name: 'posting_number', label: this.$t('order.posting_number'), field: 'posting_number', align: 'center' },
        { name: 'dn_code', label: this.$t('outbound.view_dn.dn_code'), field: 'dn_code', align: 'center' },
        { name: 'order_time', label: this.$t('order.order_time'), field: 'order_time', align: 'center' },
        { name: 'status', label: this.$t('order.status'), field: 'status', align: 'center' },
        { name: 'handle_status', label: this.$t('order.handle_status'), field: 'handle_status', align: 'center' },
        { name: 'handle_message', label: this.$t('order.handle_message'), field: 'handle_message', align: 'center' },
        { name: 'supplier', label: this.$t('baseinfo.view_supplier.supplier_name'), field: 'supplier', align: 'center' },
        { name: 'creater', label: this.$t('creater'), field: 'creater', align: 'center' },
        { name: 'create_time', label: this.$t('createtime'), field: 'create_time', align: 'center' },
        { name: 'update_time', label: this.$t('updatetime'), field: 'update_time', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'right' }
      ],
      filter: '',
      pagination: {
        page: 1,
        rowsPerPage: '30'
      },
      viewForm: false,
      viewPostingNumber: '',
      viewid: 0,
      printObj: {
        id: 'printMe',
        popTitle: this.$t('inbound.asn')
      },
      devi: window.device,
      current: 1,
      max: 0,
      total: 0,
      paginationIpt: 1
    }
  },
  methods: {
    getList () {
      var _this = this
      if (LocalStorage.has('auth')) {
        getauth(_this.pathname + '?page=' + '' + _this.current, {})
          .then(res => {
            _this.table_list = []
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
            res.results.forEach(item => {
              if (item.status === 1) {
                item.status = _this.$t('order.awaiting_review')
              } else if (item.status === 2) {
                item.status = _this.$t('order.awaiting_deliver')
              } else if (item.status === 3) {
                item.status = _this.$t('order.delivering')
              } else if (item.status === 4) {
                item.status = _this.$t('order.cancelled')
              } else if (item.status === 5) {
                item.status = _this.$t('order.delivered')
              } else {
                item.status = 'N/A'
              }

              if (item.handle_status === 1) {
                item.handle_status = _this.$t('order.normal')
              } else if (item.handle_status === 2) {
                item.handle_status = _this.$t('order.abnormal')
              } else {
                item.handle_status = 'N/A'
              }
              _this.table_list.push(item)
            })
            _this.pathname_previous = res.previous
            _this.pathname_next = res.next
            _this.orderListData = res.results
          })
          .catch(err => {
            _this.$q.notify({
              message: err.detail,
              icon: 'close',
              color: 'negative'
            })
          })
      }
    },
    changePageEnter(e) {
      if (Number(this.paginationIpt) < 1) {
        this.current = 1;
        this.paginationIpt = 1;
      } else if (Number(this.paginationIpt) > this.max) {
        this.current = this.max;
        this.paginationIpt = this.max;
      } else {
        this.current = Number(this.paginationIpt);
      }
      this.getList();
    },
    getSearchList () {
      var _this = this
      if (LocalStorage.has('auth')) {
        getauth(_this.pathname + '?posting_number__icontains=' + _this.filter + '&page=' + '' + _this.current, {})
          .then(res => {
            _this.table_list = []
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
            res.results.forEach(item => {
              if (item.status === 1) {
                item.status = _this.$t('order.awaiting_review')
              } else if (item.status === 2) {
                item.status = _this.$t('order.awaiting_deliver')
              } else if (item.status === 3) {
                item.status = _this.$t('order.delivering')
              } else if (item.status === 4) {
                item.status = _this.$t('order.cancelled')
              } else if (item.status === 5) {
                item.status = _this.$t('order.delivered')
              } else {
                item.status = 'N/A'
              }

              if (item.handle_status === 1) {
                item.handle_status = _this.$t('order.normal')
              } else if (item.handle_status === 2) {
                item.handle_status = _this.$t('order.abnormal')
              } else {
                item.handle_status = 'N/A'
              }
              _this.table_list.push(item)
            })
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
      } else {
      }
    },
    getListPrevious () {
      var _this = this
      if (LocalStorage.has('auth')) {
        getauth(_this.pathname_previous, {})
          .then(res => {
            _this.table_list = []
            res.results.forEach(item => {
              if (item.status === 1) {
                item.status = _this.$t('order.awaiting_review')
              } else if (item.status === 2) {
                item.status = _this.$t('order.awaiting_deliver')
              } else if (item.status === 3) {
                item.status = _this.$t('order.delivering')
              } else if (item.status === 4) {
                item.status = _this.$t('order.cancelled')
              } else if (item.status === 5) {
                item.status = _this.$t('order.delivered')
              } else {
                item.status = 'N/A'
              }

              if (item.handle_status === 1) {
                item.handle_status = _this.$t('order.normal')
              } else if (item.handle_status === 2) {
                item.handle_status = _this.$t('order.abnormal')
              } else {
                item.handle_status = 'N/A'
              }
              _this.table_list.push(item)
            })
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
      } else {
      }
    },
    getListNext () {
      var _this = this
      if (LocalStorage.has('auth')) {
        getauth(_this.pathname_next, {})
          .then(res => {
            _this.table_list = []
            res.results.forEach(item => {
              if (item.status === 1) {
                item.status = _this.$t('order.awaiting_review')
              } else if (item.status === 2) {
                item.status = _this.$t('order.awaiting_deliver')
              } else if (item.status === 3) {
                item.status = _this.$t('order.delivering')
              } else if (item.status === 4) {
                item.status = _this.$t('order.cancelled')
              } else if (item.status === 5) {
                item.status = _this.$t('order.delivered')
              } else {
                item.status = 'N/A'
              }

              if (item.handle_status === 1) {
                item.handle_status = _this.$t('order.normal')
              } else if (item.handle_status === 2) {
                item.handle_status = _this.$t('order.abnormal')
              } else {
                item.handle_status = 'N/A'
              }
              _this.table_list.push(item)
            })
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
      } else {
      }
    },
    reFresh () {
      var _this = this
      _this.table_list = []
      _this.getList()
    },
    getFocus (number) {
      this.listNumber = number
    },
    viewData (e) {
      this.products_table = e.products
      this.view = e.posting_number
      this.viewForm = true
    },
    isSupplier () {
      return LocalStorage.getItem('staff_type') === 'Supplier'
    },
    async fetchOrder () {
      await postauth('shoporder/init/', {})
      this.current = 1;
      this.paginationIpt = 1;
      this.getList()
    }
  },
  created () {
    var _this = this
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
      _this.table_list = []
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
  updated () {},
  destroyed () {}
}
</script>
