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
            <q-btn :label="$t('shopsku.init_bind')" icon="refresh" @click="initBind()">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsku.init_bind_tip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td key="platform_id" :props="props">{{ props.row.platform_id }}</q-td>
            <q-td key="platform_name" :props="props">{{ props.row.platform_name }}</q-td>
            <template v-if="props.row.id === editid">
              <q-td key="goods_code" :props="props">
                <q-select
                  dense
                  outlined
                  square
                  emit-value
                  v-model="editFormData.goods_code"
                  :options="goods_list"
                  transition-show="scale"
                  transition-hide="scale"
                  :label="$t('shopsku.goods_code')"
                  :rules="[val => (val && val.length > 0) || getFieldRequiredMessage('goods_code')]"
                />
              </q-td>
            </template>
            <template v-else-if="props.row.id !== editid">
              <q-td key="goods_code" :props="props">{{ props.row.goods_code }}</q-td>
            </template>
            <q-td key="image" :props="props">{{ props.row.image }}</q-td>
            <q-td key="width" :props="props">{{ props.row.width }}</q-td>
            <q-td key="height" :props="props">{{ props.row.height }}</q-td>
            <q-td key="depth" :props="props">{{ props.row.depth }}</q-td>
            <q-td key="weight" :props="props">{{ props.row.weight }}</q-td>
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
          <q-pagination
            v-model="current"
            color="black"
            :max="max"
            :max-pages="6"
            boundary-links
            @click="getList()"
          />
          <q-btn-group push>
            <q-btn :label="$t('shopsku.previous')" icon="arrow_back_ios" :disable="curr_last_id_index === 0" @click="getList('pre')">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsku.previous_tip') }}</q-tooltip>
            </q-btn>
            <q-btn :label="$t('shopsku.next')" icon="arrow_forward_ios" :disable="curr_last_id_index = max - 1" @click="getList('next')">
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('shopsku.next_tip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
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
      pathname: 'shopsku/',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      goods_list: [],
      columns: [
        { name: 'id', required: true, label: this.$t('shopsku.id'), align: 'left', field: 'id' },
        { name: 'platform_sku', label: this.$t('shopsku.platform_sku'), field: 'platform_sku', align: 'center' },
        { name: 'goods_code', label: this.$t('shopsku.goods_code'), field: 'goods_code', align: 'center' },
        { name: 'image', label: this.$t('shopsku.image'), field: 'image', align: 'center' },
        { name: 'width', label: this.$t('shopsku.width'), field: 'width', align: 'center' },
        { name: 'height', label: this.$t('shopsku.height'), field: 'height', align: 'center' },
        { name: 'depth', label: this.$t('shopsku.depth'), field: 'depth', align: 'center' },
        { name: 'weight', label: this.$t('shopsku.weight'), field: 'weight', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'right' }
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
      last_id_list: [''],
      curr_last_id_index: 0,
      max: 0,
      total: 0,
      shop_id: ''
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
      
      getauth(`${_this.pathname}?shop_id=${_this.shop_id}&last_id=${last_id}`, {})
        .then(res => {
          _this.table_list = res.results
          _this.total = res.count

          _this.curr_last_id_index = last_id_index
          _this.last_id_list[last_id_index+1] = res.last_id

          if (res.count === 0) {
            _this.max = 0
          } else {
            if (Math.ceil(res.count / 30) === 1) {
              _this.max = 0
            } else {
              _this.max = Math.ceil(res.count / 30)
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
    editData (e) {
      var _this = this
      _this.editMode = true
      _this.editid = e.id
      _this.editFormData = {
        sys_id: e.sys_id,
        platform_id: '' + e.id,
        platform_sku: e.platform_sku,
        goods_code: e.goods_code
      }
    },
    editDataSubmit () {
      var _this = this

      if (!_this.editFormData.goods_code) {
        _this.$q.notify({
          message: _this.getFieldRequiredMessage('goods_code'),
          icon: 'close',
          color: 'negative'
        })
        return
      }

      let reqPromise
      if (_this.editFormData.sys_id) {
        // edit
        const data = {
          goods_code: _this.editFormData.goods_code
        }
        const editid = _this.editFormData.sys_id
        reqPromise = patchauth(_this.pathname + editid + '/', data)
      } else {
        // create
        const data = {
          platform_id: _this.editFormData.platform_id,
          platform_sku: _this.editFormData.platform_sku,
          goods_code: _this.editFormData.goods_code
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
