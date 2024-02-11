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
              :label="$t('new')"
              icon="add"
              @click="showForm = true"
            >
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('newtip') }}</q-tooltip>
            </q-btn>
            <q-btn :label="$t('refresh')" icon="refresh" @click="reFresh()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('refreshtip') }}</q-tooltip>
            </q-btn>
            <q-btn :label="$t('download')" icon="cloud_download" @click="downloadData()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('downloadtip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
          <q-space />
          <q-input outlined rounded dense debounce="300" color="primary" v-model="filter" :placeholder="$t('search')" @input="getSearchList()" @keyup.enter="getSearchList()">
            <template v-slot:append>
              <q-icon name="search" @click="getSearchList()"/>
            </template>
          </q-input>
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td key="shop_name" :props="props">{{ props.row.shop_name }}</q-td>
            <q-td key="shop_type" :props="props">{{ props.row.shop_type }}</q-td>
            <q-td key="supplier" :props="props">{{ props.row.supplier }}</q-td>
            <q-td key="sync" :props="props">{{ getSyncLabel(props.row.sync) }}</q-td>
            <q-td key="create_time" :props="props">{{ showLocalTime(props.row.create_time) }}</q-td>
            <q-td key="update_time" :props="props">{{ showLocalTime(props.row.update_time) }}</q-td>
            <q-td key="action" :props="props" style="width: 250px">
              <q-btn
                round
                flat
                push
                color="purple"
                icon="warehouse"
                @click="showWarehouse(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopwarehouse.shop_warehouse') }}</q-tooltip>
              </q-btn>
              <q-btn
                round
                flat
                push
                color="purple"
                icon="category"
                @click="showSku(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsku.shop_sku') }}</q-tooltip>
              </q-btn>
              <q-btn
                round
                flat
                push
                color="purple"
                icon="category"
                @click="showSync(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsync.shop_sync') }}</q-tooltip>
              </q-btn>
              <q-btn
                round
                flat
                push
                color="purple"
                icon="edit"
                @click="editData(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('edit') }}</q-tooltip>
              </q-btn>
              <q-btn
                round
                flat
                push
                color="dark"
                icon="delete"
                @click="deleteData(props.row.id)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('delete') }}</q-tooltip>
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
    <q-dialog v-model="showForm">
      <q-card class="shadow-24">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ editid ? $t('edit') : $t('newtip') }}</div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip content-class="bg-amber text-black shadow-4">{{ $t('index.close') }}</q-tooltip>
          </q-btn>
        </q-bar>
        <q-card-section style="max-height: 325px; width: 400px" class="scroll">
          <q-select
            dense
            outlined
            square
            v-model="formData.supplier"
            :options="supplier_name_list"
            transition-show="scale"
            transition-hide="scale"
            :label="$t('shop.supplier')"
            :rules="[val => (val && val.length > 0) || getFieldRequiredMessage('supplier')]"
            @keyup.enter="dataSubmit()"
            style="margin-top: 5px"
          />
          <q-input
            dense
            outlined
            square
            v-model.trim="formData.shop_name"
            :label="$t('shop.shop_name')"
            autofocus
            :rules="[val => (val && val.length > 0) || getFieldRequiredMessage('shop_name')]"
            @keyup.enter="dataSubmit()"
          />
          <q-select
            dense
            outlined
            square
            v-model="formData.sync"
            :options="sync_label_list"
            transition-show="scale"
            transition-hide="scale"
            :label="$t('shop.sync')"
            :rules="[val => (val && val.length > 0) || getFieldRequiredMessage('sync')]"
            @keyup.enter="dataSubmit()"
            style="margin-top: 5px"
          />
          <q-select
            dense
            outlined
            square
            v-model="formData.shop_type"
            :options="shop_type_name_list"
            transition-show="scale"
            transition-hide="scale"
            :label="$t('shoptype.shop_type')"
            :rules="[val => (val && val.length > 0) || getFieldRequiredMessage('shop_type')]"
            @keyup.enter="dataSubmit()"
            style="margin-top: 5px"
          />
          <q-input
            dense
            outlined
            square
            v-for="item in shopTypeFields"
            :key="item.key"
            v-model.trim="formData[item.key]"
            :label="getShopTypeFieldLabel(item)"
            autofocus
            :rules="[val => (val && val.length > 0) || getFieldRequiredMessage(item.key)]"
            @keyup.enter="dataSubmit()"
          />
        </q-card-section>
        <div style="float: right; padding: 15px 15px 15px 0">
          <q-btn color="white" text-color="black" style="margin-right: 25px" @click="dataCancel()">{{ $t('cancel') }}</q-btn>
          <q-btn color="primary" @click="dataSubmit()">{{ $t('submit') }}</q-btn>
        </div>
      </q-card>
    </q-dialog>
    <q-dialog v-model="deleteForm">
      <q-card class="shadow-24">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ $t('delete') }}</div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip content-class="bg-amber text-black shadow-4">{{ $t('index.close') }}</q-tooltip>
          </q-btn>
        </q-bar>
        <q-card-section style="max-height: 325px; width: 400px" class="scroll">{{ $t('deletetip') }}</q-card-section>
        <div style="float: right; padding: 15px 15px 15px 0">
          <q-btn color="white" text-color="black" style="margin-right: 25px" @click="deleteDataCancel()">{{ $t('cancel') }}</q-btn>
          <q-btn color="primary" @click="deleteDataSubmit()">{{ $t('submit') }}</q-btn>
        </div>
      </q-card>
    </q-dialog>
  </div>
</template>
<router-view />

<script>
import { getauth, postauth, putauth, deleteauth, getfile } from 'boot/axios_request'
import { date, exportFile, LocalStorage } from 'quasar'

export default {
  name: 'Pageshoplist',
  data () {
    return {
      openid: '',
      login_name: '',
      authin: '0',
      pathname: 'shop/',
      pathname_previous: '',
      pathname_next: '',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      shop_type_list: [],
      columns: [
        { name: 'shop_name', required: true, label: this.$t('shop.shop_name'), align: 'left', field: 'shop_name' },
        { name: 'shop_type', label: this.$t('shoptype.shop_type'), field: 'shop_type', align: 'center' },
        { name: 'supplier', required: true, label: this.$t('shop.supplier'), align: 'center', field: 'supplier' },
        { name: 'sync', label: this.$t('shop.sync'), field: 'sync', align: 'center' },
        { name: 'create_time', label: this.$t('createtime'), field: 'create_time', align: 'center' },
        { name: 'update_time', label: this.$t('updatetime'), field: 'update_time', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'center' }
      ],
      pagination: {
        page: 1,
        rowsPerPage: '30'
      },
      showForm: false,
      formData: {
        shop_name: '',
        shop_type: '',
        shop_data: ''
      },
      editid: 0,
      deleteForm: false,
      deleteid: 0,
      filter: '',
      current: 1,
      max: 0,
      total: 0,
      paginationIpt: 1,
      current_shop_type: '',
      supplier_list: [],
      sync_list: [true, false]
    }
  },
  computed: {
    shop_type_name_list: function() {
      return this.shop_type_list.map(item => item.shop_type)
    },
    shopTypeFields () {
      const currentShopType = this.current_shop_type
      let schema
      this.shop_type_list.some(item => {
        if (item.shop_type === currentShopType) {
          schema = item && item.shop_schema
          return true
        }
      })

      if (!schema) {
        return []
      }

      const shopSchema = JSON.parse(schema) || {}
      return shopSchema.fields || []
    },
    supplier_name_list: function() {
      return this.supplier_list.map(item => item.supplier_name)
    },
    sync_label_list: function() {
      return this.sync_list.map(val => {
        if (val) {
          return this.$t('shop.sync_true')
        }

        return this.$t('shop.sync_false')
      })
    }
  },
  watch: {
    'formData.shop_type': function (val) {
      this.current_shop_type = val
    }
  },
  methods: {
    getShopType () {
      var _this = this
      getauth('shoptype/?page=1', {})
        .then(res => {
          _this.shop_type_list = res.results
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    getSupplier () {
      var _this = this
      getauth('supplier/?page=1', {})
        .then(res => {
          _this.supplier_list = res.results
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    getList () {
      var _this = this
      getauth(_this.pathname + '?page=' + '' + _this.current, {})
        .then(res => {
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
    getSearchList () {
      var _this = this
      _this.filter = _this.filter.replace(/\s+/g, '')
      _this.current = 1
      _this.paginationIpt = 1
      getauth(_this.pathname + '?shop_name__icontains=' + _this.filter + '&page=' + '' + _this.current, {})
        .then(res => {
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
    dataSubmit () {
      var _this = this
      var shops = []
      _this.table_list.forEach(i => {
        shops.push(i.shop_name)
      })

      if (_this.formData.supplier.length === 0) {
        _this.$q.notify({
          message: _this.getFieldRequiredMessage('supplier'),
          icon: 'close',
          color: 'negative'
        })
        return
      }

      if (_this.formData.shop_name.length === 0) {
        _this.$q.notify({
          message: _this.getFieldRequiredMessage('shop_name'),
          icon: 'close',
          color: 'negative'
        })
        return
      }

      if (!_this.editid && shops.indexOf(_this.formData.shop_name) !== -1) {
        // add
        _this.$q.notify({
          message: _this.$t('notice.shoperror'),
          icon: 'close',
          color: 'negative'
        })
        return
      }

      if (!_this.formData.shop_type) {
        _this.$q.notify({
          message: _this.getFieldRequiredMessage('shop_type'),
          icon: 'close',
          color: 'negative'
        })
        return
      }

      if (!_this.formData.sync) {
        _this.$q.notify({
          message: _this.getFieldRequiredMessage('sync'),
          icon: 'close',
          color: 'negative'
        })
        return
      }

      const shopTypeFields = _this.shopTypeFields
      const shop_data = {}
      for (let i = 0; i < shopTypeFields.length; i++) {
        const field = shopTypeFields[i]
        if (!_this.formData[field.key]) {
          _this.$q.notify({
            message: _this.getFieldRequiredMessage(field.key),
            icon: 'close',
            color: 'negative'
          })
          return
        }
        shop_data[field.key] = _this.formData[field.key]
      }

      const data = {
        supplier: _this.formData.supplier,
        shop_name: _this.formData.shop_name,
        sync: _this.formData.sync,
        shop_type: _this.formData.shop_type,
        shop_data: JSON.stringify(shop_data)
      }

      const index = _this.sync_label_list.indexOf(_this.formData.sync)
      if (index >= 0) {
        data.sync = _this.sync_list[index]
      }

      if (!_this.editid) {
        postauth(_this.pathname, data)
          .then(res => {
            _this.getList()
            _this.dataCancel()
            _this.$q.notify({
              message: 'Success Create',
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
      } else {
        putauth(_this.pathname + _this.editid + '/', data)
        .then(res => {
          _this.dataCancel()
          _this.getList()
          _this.$q.notify({
            message: 'Success Edit Data',
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
      }
    },
    dataCancel () {
      var _this = this
      _this.showForm = false
      _this.editid = 0
      _this.formData = {
        shop_name: '',
        shop_type: '',
        shop_data: ''
      }
    },
    editData (e) {
      var _this = this
      _this.showForm = true
      _this.editid = e.id
      _this.formData = {
        supplier: e.supplier,
        shop_name: e.shop_name,
        sync: _this.getSyncLabel(e.sync),
        shop_type: e.shop_type,
        ...JSON.parse(e.shop_data)
      }
    },
    deleteData (e) {
      var _this = this
      _this.deleteForm = true
      _this.deleteid = e
    },
    deleteDataSubmit () {
      var _this = this
      deleteauth(_this.pathname + _this.deleteid + '/')
        .then(res => {
          _this.deleteDataCancel()
          _this.getList()
          _this.$q.notify({
            message: 'Success Edit Data',
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
    deleteDataCancel () {
      var _this = this
      _this.deleteForm = false
      _this.deleteid = 0
    },
    downloadData () {
      var _this = this
      if (LocalStorage.has('auth')) {
        getfile(_this.pathname + 'file/?lang=' + LocalStorage.getItem('lang')).then(res => {
          var timeStamp = Date.now()
          var formattedString = date.formatDate(timeStamp, 'YYYYMMDDHHmmssSSS')
          const status = exportFile(_this.pathname + formattedString + '.csv', '\uFEFF' + res.data, 'text/csv')
          if (status !== true) {
            this.$q.notify({
              message: 'Browser denied file download...',
              color: 'negative',
              icon: 'warning'
            })
          }
        })
      } else {
        _this.$q.notify({
          message: _this.$t('notice.loginerror'),
          color: 'negative',
          icon: 'warning'
        })
      }
    },
    getShopTypeFieldLabel (item) {
      return this.$t(`shoptype.${this.formData.shop_type}.${item.key}`)
    },
    getFieldRequiredMessage (field) {
      return this.$t('notice.field_required_error', { field })
    },
    showWarehouse (e) {
      this.$router.push({
        name: 'shopwarehouse',
        params: {
          shop_id: e.id
        }
      })
    },
    showSku (e) {
      this.$router.push({
        name: 'shopsku',
        params: {
          shop_id: e.id
        }
      })
    },
    showSync (e) {
      this.$router.push({
        name: 'shopsync',
        params: {
          shop_id: e.id
        }
      })
    },
    getSyncLabel (sync) {
      const index = this.sync_list.indexOf(sync)
      return this.sync_label_list[index]
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
      _this.getShopType()
      _this.getSupplier()
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
    if (LocalStorage.getItem('lang') === 'zh-hans') {
      _this.staff_type_list = ['经理', '主管', '收货组', '发货组', '库存控制', '客户', '供应商']
    } else {
      _this.staff_type_list = ['Manager', 'Supervisor', 'Inbount', 'Outbound', 'StockControl', 'Customer', 'Supplier']
    }
  },
  updated () {
  },
  destroyed () {
  }
}
</script>
