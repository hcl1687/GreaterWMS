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
            <q-btn :label="$t('back')" icon="arrow_back" @click="back()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('back') }}</q-tooltip>
            </q-btn>
            <q-btn :label="$t('refresh')" icon="refresh" @click="reFresh()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('refreshtip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td key="id" :props="props">{{ props.row.id }}</q-td>
            <q-td key="name" :props="props">{{ props.row.name }}</q-td>
            <template v-if="props.row.id === editid">
              <q-td key="sys_name" :props="props">
                <q-select
                  dense
                  outlined
                  v-model="editFormData.warehouse_name"
                  :options="sys_warehouse_name_list"
                  :label="$t('shopwarehouse.sys_name')"
                  :rules="[val => !!val || getFieldRequiredMessage('sys_warehouse')]"
                />
              </q-td>
            </template>
            <template v-else-if="props.row.id !== editid">
              <q-td key="sys_name" :props="props">{{ props.row.sys_name }}</q-td>
            </template>
            <template v-if="!editMode">
              <q-td key="action" :props="props" style="width: 175px">
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
                  :disable="!props.row.sys_id"
                  @click="deleteData(props.row)"
                >
                  <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('delete') }}</q-tooltip>
                </q-btn>
              </q-td>
            </template>
            <template v-else-if="editMode">
              <template v-if="props.row.id === editid">
                <q-td key="action" :props="props" style="width: 150px">
                  <q-btn round flat push color="secondary" icon="check" @click="editDataSubmit()">
                    <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('confirmedit') }}</q-tooltip>
                  </q-btn>
                  <q-btn round flat push color="red" icon="close" @click="editDataCancel()">
                    <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('canceledit') }}</q-tooltip>
                  </q-btn>
                </q-td>
              </template>
              <template v-else-if="props.row.id !== editid"></template>
            </template>
          </q-tr>
        </template>
      </q-table>
    </transition>
    <template>
        <div v-show="max !== 0" class="q-pa-lg flex flex-center">
           <div>{{ total }} </div>
        </div>
        <div v-show="max === 0" class="q-pa-lg flex flex-center">
          <q-btn flat push color="dark" :label="$t('no_data')"></q-btn>
        </div>
    </template>
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
import { getauth, postauth, patchauth, deleteauth, getfile } from 'boot/axios_request'
import { date, exportFile, LocalStorage } from 'quasar'

export default {
  name: 'Pageshopwarehouse',
  data () {
    return {
      openid: '',
      login_name: '',
      authin: '0',
      pathname: 'shopwarehouse/',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      sys_warehouse_list: [],
      sys_warehouse_name_list: [],
      columns: [
        { name: 'id', required: true, label: this.$t('shopwarehouse.id'), align: 'left', field: 'id' },
        { name: 'name', label: this.$t('shopwarehouse.name'), field: 'name', align: 'center' },
        { name: 'sys_name', label: this.$t('shopwarehouse.sys_name'), field: 'sys_name', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'center' }
      ],
      pagination: {
        page: 1,
        rowsPerPage: '30'
      },
      editid: 0,
      editFormData: {},
      editMode: false,
      deleteForm: false,
      deleteid: 0,
      max: 0,
      total: 0,
      shop_id: ''
    }
  },
  methods: {
    getSysWarehouseList () {
      var _this = this
      getauth('warehouse/' + '?page=1', {})
        .then(res => {
          _this.sys_warehouse_list = res.results.map(item => {
            _this.sys_warehouse_name_list.push(item.warehouse_name)
            return {
              name: item.warehouse_name,
              id: item.id
            }
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
    getList () {
      var _this = this
      getauth(_this.pathname + '?shop_id=' + _this.shop_id, {})
        .then(res => {
          _this.table_list = res
          _this.total = res.length
          _this.max = 0
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
    editData (e) {
      var _this = this
      _this.editMode = true
      _this.editid = e.id
      _this.editFormData = {
        id: e.sys_id,
        platform_id: '' + e.id,
        platform_name: e.name,
        warehouse: e.sys_warehouse_id,
        warehouse_name: e.sys_name
      }
    },
    editDataSubmit () {
      var _this = this

      if (!_this.editFormData.warehouse_name) {
        _this.$q.notify({
          message: _this.getFieldRequiredMessage('warehouse'),
          icon: 'close',
          color: 'negative'
        })
        return
      }

      _this.sys_warehouse_list.some(item => {
        if (item.name === _this.editFormData.warehouse_name) {
          _this.editFormData.warehouse = item.id
          return true
        }
      })

      let reqPromise
      if (_this.editFormData.id) {
        // edit
        const data = {
          shop: +_this.shop_id,
          warehouse: _this.editFormData.warehouse
        }
        const editid = _this.editFormData.id
        reqPromise = patchauth(_this.pathname + editid + '/', data)
      } else {
        // create
        const data = {
          shop: +_this.shop_id,
          platform_id: _this.editFormData.platform_id,
          platform_name: _this.editFormData.platform_name,
          warehouse: _this.editFormData.warehouse
        }
        reqPromise = postauth(_this.pathname, data)
      }

      reqPromise
        .then(res => {
          _this.editDataCancel()
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
    editDataCancel () {
      var _this = this
      _this.editMode = false
      _this.editid = 0
      _this.editFormData = {}
    },
    deleteData (e) {
      var _this = this
      if (!e.sys_id) {
        return
      }

      _this.deleteForm = true
      _this.deleteid = e.sys_id
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
    back () {
      this.$router.back()
    },
    getFieldRequiredMessage (field) {
      return this.$t('notice.field_required_error', { field })
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
      _this.getSysWarehouseList()
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
  destroyed () {
  }
}
</script>
