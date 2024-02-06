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
          <div class="col">
            <div class="row items-center relative-position">
              <q-btn-group push>
                <q-btn
                  :label="$t('download_center.reset')"
                  icon="img:statics/downloadcenter/reset.svg"
                  @click="reset()"
                >
                </q-btn>
                <q-btn
                  :label="$t('order.fetch_order')"
                  icon="system_update_alt"
                  @click="fetchOrder()"
                >
                  <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('order.fetch_order_tip') }}</q-tooltip>
                </q-btn>
                <q-btn
                  :label="$t('order.update_order')"
                  icon="cloud_sync"
                  @click="updateOrder()"
                >
                  <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('order.update_order_tip') }}</q-tooltip>
                </q-btn>
                <q-btn :label="$t('order.batch_delete')" icon="delete_sweep" :disable="selected.length === 0" @click="batchDelete()">
                  <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('order.batch_delete_tip') }}</q-tooltip>
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
            </div>
            <div class="row items-center relative-position q-mt-md">
              <div class="col-auto q-mb-md">
                <div class="flex items-center">
                  <div class="q-mr-md">{{ $t("download_center.createTime") }}</div>
                  <q-input
                    readonly
                    outlined
                    dense
                    v-model="createDate2"
                    :placeholder="interval"
                  >
                    <template v-slot:append>
                      <q-icon name="event" class="cursor-pointer">
                        <q-popup-proxy
                          ref="qDateProxy"
                          transition-show="scale"
                          transition-hide="scale"
                          ><q-date v-model="createDate1" range
                        /></q-popup-proxy>
                      </q-icon>
                    </template>
                  </q-input>
                </div>
              </div>
              <div class="col-auto q-mb-md q-ml-md">
                <q-input outlined rounded dense debounce="300" color="primary" v-model="filter_shop_name" :placeholder="$t('order.search_shop_name')" @input="getList()" @keyup.enter="getList()">
                  <template v-slot:append>
                    <q-icon name="search" @click="getList()" />
                  </template>
                </q-input>
              </div>
              <div class="col-auto q-mb-md q-ml-md">
                <q-input outlined rounded dense debounce="300" color="primary" v-model="filter_posting_number" :placeholder="$t('order.search_posting_number')" @input="getList()" @keyup.enter="getList()">
                  <template v-slot:append>
                    <q-icon name="search" @click="getList()" />
                  </template>
                </q-input>
              </div>
              <div class="col-auto q-mb-md q-ml-md">
                <q-input outlined rounded dense debounce="300" color="primary" v-model="filter_dn_code" :placeholder="$t('order.search_dn_code')" @input="getList()" @keyup.enter="getList()">
                  <template v-slot:append>
                    <q-icon name="search" @click="getList()" />
                  </template>
                </q-input>
              </div>
              <div class="col-auto q-mb-md q-ml-md">
                <q-select
                  clearable
                  use-input
                  fill-input
                  hide-selected
                  input-debounce="0"
                  dense
                  outlined
                  v-model="filter_supplier"
                  :options="supplier_list"
                  @filter="filterFnS"
                  @input-value="setSupplierIpt"
                  @input="getList()"
                  :label="$t('baseinfo.view_supplier.supplier_name')"
                  style="margin-bottom: 5px"
                >
                  <template v-slot:Sno-option>
                    <q-item>
                      <q-item-section class="text-grey">
                        No Result
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
              <div class="col-auto q-mb-md q-ml-md">
                <q-select
                  clearable
                  use-input
                  fill-input
                  hide-selected
                  input-debounce="0"
                  dense
                  outlined
                  v-model="filter_handle_status"
                  :options="handle_status_list"
                  @input="getList()"
                  :label="$t('order.handle_status')"
                  style="margin-bottom: 5px"
                >
                  <template v-slot:Sno-option>
                    <q-item>
                      <q-item-section class="text-grey">
                        No Result
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
              </div>
            </div>
            <div class="row items-center relative-position">
              <div class="col-auto q-mb-md">
                <div class="flex items-center">
                  <div class="q-mr-md">{{ $t("order.shipment_time") }}</div>
                  <q-input
                    readonly
                    outlined
                    dense
                    v-model="shipmentDate2"
                    :placeholder="interval"
                  >
                    <template v-slot:append>
                      <q-icon name="event" class="cursor-pointer">
                        <q-popup-proxy
                          ref="qDateProxy"
                          transition-show="scale"
                          transition-hide="scale"
                          ><q-date v-model="shipmentDate1" range
                        /></q-popup-proxy>
                      </q-icon>
                    </template>
                  </q-input>
                </div>
              </div>
              <div class="col-auto q-mb-md q-ml-md">
                <q-btn-toggle
                  v-model="shipmentDate3"
                  push
                  glossy
                  clearable
                  toggle-color="primary"
                  :options="shipmentDate3Options"
                />
              </div>
            </div>
          </div>
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
            <q-td key="shop_type" :props="props">{{ props.row.shop.shop_type }}</q-td>
            <q-td key="shop_name" :props="props">{{ props.row.shop.shop_name }}</q-td>
            <q-td key="platform_warehouse_name" :props="props">{{ props.row.platform_warehouse_name }}</q-td>
            <q-td key="platform_id" :props="props">{{ props.row.platform_id }}</q-td>
            <q-td key="posting_number" :props="props">{{ props.row.posting_number }}</q-td>
            <q-td key="dn_code" :props="props">{{ props.row.dn_code }}</q-td>
            <q-td key="total_weight" :props="props">{{ props.row.total_weight && props.row.total_weight.toFixed(4) }}</q-td>
            <q-td key="order_time" :props="props">{{ showLocalTime(props.row.order_time) }}</q-td>
            <q-td key="shipment_time" :props="props">{{ showLocalTime(props.row.shipment_time) }}</q-td>
            <q-td key="status" :props="props">{{ getStatusMsg(props.row.status) }}</q-td>
            <q-td key="dn_status" :props="props">{{ getDnStatusText(props.row.dn_status) }}</q-td>
            <q-td key="handle_status" :props="props">{{ getHandleStatusMsg(props.row.handle_status) }}</q-td>
            <q-td key="handle_message" :props="props">{{ props.row.handle_message }}</q-td>
            <q-td key="supplier" :props="props">{{ props.row.supplier }}</q-td>
            <q-td key="creater" :props="props">{{ props.row.creater }}</q-td>
            <q-td key="create_time" :props="props">{{ showLocalTime(props.row.create_time) }}</q-td>
            <q-td key="update_time" :props="props">{{ showLocalTime(props.row.update_time) }}</q-td>
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
              <q-btn
                round
                flat
                push
                color="secondary"
                icon="print"
                :disable="!props.row.dn_id"
                @click="PrintPickingList(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('print') }}</q-tooltip>
              </q-btn>
              <q-btn
                round
                flat
                push
                color="dark"
                icon="rv_hookup"
                @click="handleDispatch(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('dispatch') }}</q-tooltip>
              </q-btn>
              <q-btn
                round
                flat
                push
                color="dark"
                icon="delete"
                :disable="props.row.handle_status !== 2"
                @click="deleteData(props.row)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ props.row.handle_status !== 2 ? $t('order.normal_delete_tip') : $t('delete') }}</q-tooltip>
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
          <div>{{ viewNumber }}</div>
          <q-space />
          {{ $t('outbound.dn') }}
        </q-bar>
        <q-markup-table>
          <thead>
            <tr>
              <th class="text-left">{{ $t('shopsku.name') }}</th>
              <th class="text-left">{{ $t('goods.view_goodslist.goods_code') }}</th>
              <th class="text-left">{{ $t('shopsku.platform_sku') }}</th>
              <th class="text-right">{{ $t('order.quantity') }}</th>
              <th class="text-right">Comments</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(view, index) in products_table" :key="index">
              <td class="text-left">{{ view.name }}</td>
              <td class="text-left">{{ view.goods_code }}</td>
              <td class="text-right">{{ view.sku }}</td>
              <td class="text-right">{{ view.quantity }}</td>
              <td class="text-right"></td>
            </tr>
          </tbody>
        </q-markup-table>
      </q-card>
      <div style="float: right; padding: 15px 15px 15px 0"><q-btn color="primary" icon="print" v-print="printObj">print</q-btn></div>
    </q-dialog>
    <q-dialog v-model="viewPLForm">
      <q-card id="printPL">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ $t('print') }}</div>
          <q-space />
        </q-bar>
        <div class="col-4" style="margin-top: 5%;"><img :src="printPickingListData.bar_code" style="width: 21%;margin-left: 70%" /></div>
        <q-markup-table>
          <thead>
            <tr>
              <th class="text-left">{{ $t('outbound.view_dn.dn_code') }}</th>
              <th class="text-left">{{ $t('order.posting_number') }}</th>
              <th class="text-right">{{ $t('shopsku.goods_code') }}</th>
              <th class="text-right">{{ $t('warehouse.view_binset.bin_name') }}</th>
              <th class="text-right">{{ $t('outbound.pickstock') }}</th>
              <th class="text-right">{{ $t('outbound.pickedstock') }}</th>
              <th class="text-left">{{ $t('order.can_order_stock') }}</th>
              <th class="text-right">Comments</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(view, index) in pickinglist_print_table" :key="index">
              <td class="text-left">{{ view.dn_code }}</td>
              <td class="text-left">{{ printPickingListData.posting_number }}</td>
              <td class="text-right">{{ view.goods_code }}</td> 
              <td class="text-right">{{ view.bin_name }}</td>
              <td class="text-right">{{ view.pick_qty }}</td>
              <td class="text-right">{{ picklist_check > 0 ? view.picked_qty : '' }}</td>
              <td class="text-right">{{ view.can_order_stock }}</td>
              <td class="text-right"></td>
            </tr>
          </tbody>
        </q-markup-table>
      </q-card>
      <div style="float: right; padding: 15px 15px 15px 0"><q-btn color="primary" icon="print" v-print="printPL">print</q-btn></div>
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
import { getauth, postauth, deleteauth } from 'boot/axios_request'
import { LocalStorage } from 'quasar'
import dayjs from 'dayjs'

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
      selected: [],
      createDate1: '',
      createDate2: '',
      shipmentDate1: '',
      shipmentDate2: '',
      shipmentDate3: '',
      shipmentDate3Options: [
        { label: this.$t('order.today'), value: 'today' },
        { label: this.$t('order.tomorrow'), value: 'tomorrow' },
        { label: this.$t('order.after_tomorrow'), value: 'after_tomorrow' }
      ],
      columns: [
        { name: 'index', label: '#', field: 'index', align: 'center' },
        { name: 'shop_type', required: true, label: this.$t('shoptype.shop_type'), align: 'center', field: 'shop.shop_type' },
        { name: 'shop_name', required: true, label: this.$t('shop.shop_name'), align: 'center', field: 'shop.shop_name' },
        { name: 'platform_warehouse_name', label: this.$t('order.platform_warehouse_name'), field: 'platform_warehouse_name', align: 'center' },
        { name: 'platform_id', required: true, label: this.$t('order.platform_id'), align: 'center', field: 'platform_id' },
        { name: 'posting_number', label: this.$t('order.posting_number'), field: 'posting_number', align: 'center' },
        { name: 'dn_code', label: this.$t('outbound.view_dn.dn_code'), field: 'dn_code', align: 'center' },
        { name: 'total_weight', label: this.$t('outbound.view_dn.total_weight'), field: 'total_weight', align: 'center' },
        { name: 'order_time', label: this.$t('order.order_time'), field: 'order_time', align: 'center' },
        { name: 'shipment_time', label: this.$t('order.shipment_time'), field: 'shipment_time', align: 'center' },
        { name: 'status', label: this.$t('order.status'), field: 'status', align: 'center' },
        { name: 'dn_status', label: this.$t('outbound.view_dn.dn_status'), field: 'dn_status', align: 'center' },
        { name: 'handle_status', label: this.$t('order.handle_status'), field: 'handle_status', align: 'center' },
        { name: 'handle_message', label: this.$t('order.handle_message'), field: 'handle_message', align: 'center' },
        { name: 'supplier', label: this.$t('baseinfo.view_supplier.supplier_name'), field: 'supplier', align: 'center' },
        { name: 'creater', label: this.$t('creater'), field: 'creater', align: 'center' },
        { name: 'create_time', label: this.$t('createtime'), field: 'create_time', align: 'center' },
        { name: 'update_time', label: this.$t('updatetime'), field: 'update_time', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'center' }
      ],
      filter: '',
      filter_posting_number: '',
      filter_date_range: '',
      filter_shipment_date_range: '',
      filter_shop_name: '',
      filter_dn_code: '',
      filter_supplier: '',
      filter_handle_status: '',
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
      paginationIpt: 1,
      viewNumber: '',
      deleteForm: false,
      deleteid: 0,
      supplier_list: [],
      supplier_list1: [],
      handle_status_list: [],
      handle_status_map: {},
      printPickingListData: {},
      pickinglist_print_table: [],
      picklist_check: 0,
      viewPLForm: false,
      pickFormData: {
        dn_code: '',
        customer: '',
        goodsData: [],
        creater: ''
      },
      pickedid: 0,
      pickedDataSubmitId: 0,
      dispatchid: 0,
      dispatchFormData: {
        dn_code: '',
        driver: ''
      },
      printPL: {
        id: 'printPL',
        popTitle: this.$t('outbound.pickinglist')
      },
    }
  },
  computed: {
    interval () {
      return this.$t('download_center.start') + ' - ' + this.$t('download_center.end')
    }
  },
  watch: {
    createDate1 (val) {
      if (val) {
        if (val.to) {
          this.createDate2 = `${val.from} - ${val.to}`
          this.filter_date_range = `${(new Date(val.from)).toISOString()},${(new Date(val.to + ' 23:59:59')).toISOString()}`
        } else {
          this.createDate2 = `${val}`
          this.filter_date_range = `${(new Date(val)).toISOString()},${(new Date(val + ' 23:59:59')).toISOString()}`
        }
        this.filter_date_range = this.filter_date_range.replace(/\//g, '-')
        this.getList()
        this.$refs.qDateProxy.hide()
      }
    },
    shipmentDate1 (val) {
      if (val) {
        this.shipmentDate3 = ''
        if (val.to) {
          this.shipmentDate2 = `${val.from} - ${val.to}`
          this.filter_shipment_date_range = `${(new Date(val.from)).toISOString()},${(new Date(val.to + ' 23:59:59')).toISOString()}`
        } else {
          this.shipmentDate2 = `${val}`
          this.filter_shipment_date_range = `${(new Date(val)).toISOString()},${(new Date(val + ' 23:59:59')).toISOString()}`
        }
        this.filter_shipment_date_range = this.filter_shipment_date_range.replace(/\//g, '-')
        this.getList()
        this.$refs.qDateProxy.hide()
      }
    },
    shipmentDate3 (val) {
      this.shipmentDate2 = ''
      let start
      let end
      const now = new Date()
      if (!val) {
        // click again, toggle it
        this.filter_shipment_date_range = ''
        this.getList()
        return
      }

      if (val === 'today') {
        start = dayjs(now).set('hour', 0).set('minute', 0).set('second', 0).toISOString()
        end = dayjs(now).set('hour', 23).set('minute', 59).set('second', 59).toISOString()
      } else if (val === 'tomorrow') {
        start = dayjs(now).add(1, 'day').set('hour', 0).set('minute', 0).set('second', 0).toISOString()
        end = dayjs(now).add(1, 'day').set('hour', 23).set('minute', 59).set('second', 59).toISOString()
      } else if (val === 'after_tomorrow') {
        start = dayjs(now).add(2, 'day').set('hour', 0).set('minute', 0).set('second', 0).toISOString()
        end = dayjs(now).add(2, 'day').set('hour', 23).set('minute', 59).set('second', 59).toISOString()
      }

      this.filter_shipment_date_range = `${start},${end}`
      this.getList().then(() => {
        if (val === 'today') {
          this.shipmentDate3Options = [
            { label: `${this.$t('order.today')}(${this.total})`, value: 'today' },
            { label: this.$t('order.tomorrow'), value: 'tomorrow' },
            { label: this.$t('order.after_tomorrow'), value: 'after_tomorrow' }
          ]
        } else if (val === 'tomorrow') {
          this.shipmentDate3Options = [
            { label: this.$t('order.today'), value: 'today' },
            { label: `${this.$t('order.tomorrow')}(${this.total})`, value: 'tomorrow' },
            { label: this.$t('order.after_tomorrow'), value: 'after_tomorrow' }
          ]
        } else if (val === 'after_tomorrow') {
          this.shipmentDate3Options = [
            { label: this.$t('order.today'), value: 'today' },
            { label: this.$t('order.tomorrow'), value: 'tomorrow' },
            { label: `${this.$t('order.after_tomorrow')}(${this.total})`, value: 'after_tomorrow' }
          ]
        }
      })
    }
  },
  methods: {
    getList () {
      var _this = this
      if (!LocalStorage.has('auth')) {
        return
      }

      let url = _this.pathname + '?page=' + '' + _this.current
      if (_this.filter_date_range) {
        url = `${url}&create_time__range=${_this.filter_date_range}`
      }
      if (_this.filter_shipment_date_range) {
        url = `${url}&shipment_time__range=${_this.filter_shipment_date_range}`
      }
      if (_this.filter_posting_number) {
        url = `${url}&posting_number__icontains=${_this.filter_posting_number}`
      }
      if (_this.filter_shop_name) {
        url = `${url}&shop__shop_name__icontains=${_this.filter_shop_name}`
      }
      if (_this.filter_dn_code) {
        url = `${url}&dn_code__icontains=${_this.filter_dn_code}`
      }
      if (_this.filter_supplier) {
        url = `${url}&supplier__icontains=${_this.filter_supplier}`
      }
      if (_this.filter_handle_status) {
        const handle_status = _this.handle_status_map[_this.filter_handle_status]
        url = `${url}&handle_status__iexact=${handle_status}`
      }
      return getauth(url, {})
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
        res.results.forEach((item, index) => {
          item.index = index + 1
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

        throw err
      })
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
    getListPrevious () {
      var _this = this
      if (LocalStorage.has('auth')) {
        getauth(_this.pathname_previous, {})
          .then(res => {
            _this.table_list = []
            res.results.forEach((item, index) => {
              item.index = index + 1
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
            res.results.forEach((item, index) => {
              item.index = index + 1
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
      const order_products = JSON.parse(e.order_products)
      const stockbin_data = JSON.parse(e.stockbin_data)
      for(let i = 0; i < order_products.length; i++) {
        const item = order_products[i]
        const sItem = stockbin_data[i]
        item['goods_code'] = sItem.goods_code || ''
      }
      this.products_table = order_products
      this.viewNumber = e.posting_number
      this.viewForm = true
    },
    deleteData (e) {
      var _this = this
      if (e.handle_status !== 2) {
        _this.$q.notify({
          message: _this.$t('order.normal_delete_tip'),
          icon: 'close',
          color: 'negative'
        })
      } else {
        _this.deleteForm = true
        _this.deleteid = e.id
      }
    },
    deleteDataSubmit () {
      var _this = this
      deleteauth(_this.pathname + '' + _this.deleteid + '/')
        .then(res => {
          _this.table_list = []
          _this.deleteDataCancel()
          _this.getList()
          if (!res.detail) {
            _this.$q.notify({
              message: 'Success Delete',
              icon: 'check',
              color: 'green'
            })
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
    deleteDataCancel () {
      var _this = this
      _this.deleteForm = false
      _this.deleteid = 0
    },
    isSupplier () {
      return LocalStorage.getItem('staff_type') === 'Supplier'
    },
    async fetchOrder () {
      const shopList = await this.drainShopList()
      for(let i = 0; i < shopList.length; i++) {
        const shop = shopList[i]
        await postauth('shoporder/init/', {
          shop_id: shop.id
        })
      }
      this.current = 1;
      this.paginationIpt = 1;
      this.getList()
    },
    async updateOrder () {
      const shopList = await this.drainShopList()
      for(let i = 0; i < shopList.length; i++) {
        const shop = shopList[i]
        await postauth('shoporder/update/', {
          shop_id: shop.id
        })
      }
      this.current = 1;
      this.paginationIpt = 1;
      this.getList()
    },
    getStatusMsg (status) {
      let msg = ''
      if (status === 1) {
        msg = this.$t('order.awaiting_review')
      } else if (status === 2) {
        msg = this.$t('order.awaiting_deliver')
      } else if (status === 3) {
        msg = this.$t('order.delivering')
      } else if (status === 4) {
        msg = this.$t('order.cancelled')
      } else if (status === 5) {
        msg = this.$t('order.delivered')
      } else {
        msg = this.$t('order.other')
      }

      return msg
    },
    getHandleStatusMsg (status) {
      let msg = ''
      if (status === 1) {
        msg = this.$t('order.normal')
      } else if (status === 2) {
        msg = this.$t('order.abnormal')
      } else {
        msg = 'N/A'
      }

      return msg
    },
    async batchDelete () {
      const selected = this.selected
      if (selected.length === 0) {
        return
      }

      try {
        for (let i = 0; i < selected.length; i++) {
          const item = selected[i]
          if (item.handle_status !== 2) {
            continue
          }

          const deleteid = item.id
          const res = await deleteauth(this.pathname + '' + deleteid + '/')
          if (res.detail) {
            throw new Error(res.detail)
          }
        }

        this.$q.notify({
          message: 'Success Delete',
          icon: 'check',
          color: 'green'
        })
      } catch (e) {
        this.$q.notify({
          message: e.message,
          icon: 'close',
          color: 'negative'
        })
      } finally {
        this.selected = []
        this.current = 1
        this.paginationIpt = 1
        this.getList()
      }
    },
    reset () {
      this.current = 1
      this.paginationIpt = 1
      this.createDate1 = ''
      this.createDate2 = ''
      this.shipmentDate1 = '',
      this.shipmentDate2 = ''
      this.filter_date_range = ''
      this.filter_shipment_date_range = ''
      this.filter_dn_code = ''
      this.filter_posting_number = ''
      this.filter_shop_name = ''
      this.filter_supplier = ''
      this.getList()
    },
    filterFnS (val, update, abort) {
      var _this = this
      update(() => {
        const needle = val.toLocaleLowerCase()
        const data_filter = _this.supplier_list1
        _this.supplier_list = data_filter.filter(v => v.toLocaleLowerCase().indexOf(needle) > -1)
      })
    },
    setSupplierIpt (val) {
      const _this = this
      _this.filter_supplier = val
    },
    getSupplierList () {
      var _this = this
      getauth('supplier/' + '?page=1', {})
        .then(res => {
          const suppliers_name = res.results.map(item => {
            return item.supplier_name
          })

          _this.supplier_list = suppliers_name
          _this.supplier_list1 = suppliers_name
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    getHandleStatusList () {
      const normalLabel = this.getHandleStatusMsg(1)
      const abnormalLabel = this.getHandleStatusMsg(2)
      const handleStatus = [
        normalLabel,
        abnormalLabel
      ]
      this.handle_status_list = handleStatus
      this.handle_status_map = {
        [normalLabel]: 1,
        [abnormalLabel]: 2
      }
    },
    getFieldRequiredMessage (field) {
      return this.$t('notice.field_required_error', { field })
    },
    getDnStatusText (dn_status) {
      switch(dn_status) {
        case 1:
          return this.$t('outbound.freshorder')
        case 2:
          return this.$t('outbound.neworder')
        case 3:
          return this.$t('outbound.pickstock')
        case 4:
          return this.$t('outbound.pickedstock')
        case 5:
          return this.$t('outbound.shippedstock')
        case 6:
          return this.$t('outbound.received')
        default:
          return ''
      }
    },
    PrintPickingList (e) {
      var _this = this
      var QRCode = require('qrcode')

      _this.printPickingListData.posting_number = e.posting_number
      QRCode.toDataURL(e.bar_code, [
        {
          errorCorrectionLevel: 'H',
          mode: 'byte',
          version: '2',
          type: 'image/jpeg'
        }
      ])
        .then(url => {
          _this.printPickingListData.bar_code = url
        })
        .catch(err => {
          console.error(err)
        })
      _this.viewPLForm = true
      getauth('dn/pickinglist/' + e.dn_id + '/')
        .then(res => {
          _this.pickinglist_print_table = []
          _this.picklist_check = 0
          res.forEach(item => {
            if (item.picked_qty > 0) {
              _this.picklist_check += 1
            } else {
            }
          })
          _this.pickinglist_print_table = res
          _this.viewPLForm = true
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    async handleDispatch (e) {
      try {
        await this.pickedData(e)
        await this.pickedDataSubmit()
        await this.DispatchDN(e)
        await this.dispatchDataSubmit()
      } catch(e) {
        console.error(e)
      }
    },
    async pickedData (e) {
      var _this = this
      if (_this.getDnStatusText(e.dn_status) !== _this.$t('outbound.pickstock')) {
        _this.$q.notify({
          message: e.dn_code + ' DN Status Is Not ' + _this.$t('outbound.pickstock'),
          icon: 'close',
          color: 'negative'
        })
        throw new Error(e.dn_code + ' DN Status Is Not ' + _this.$t('outbound.pickstock'))
      } else {
        _this.pickedid = 0
        _this.pickFormData = {
          dn_code: '',
          customer: '',
          goodsData: [],
          creater: ''
        }
        _this.pickFormData.dn_code = e.dn_code
        _this.pickFormData.customer = e.customer
        await getauth('dn/pickinglist/' + e.dn_id + '/').then(res => {
          _this.pickedid = e.dn_id
          _this.pickFormData.goodsData = res
        })
      }
    },
    async pickedDataSubmit () {
      var _this = this
      _this.pickFormData.creater = _this.login_name
      _this.pickedDataSubmitId = 0
      await postauth('dn/picked/' + _this.pickedid + '/', _this.pickFormData)
        .then(res => {
          if (!res.detail) {
            _this.pickedDataSubmitId = _this.pickedid
            _this.$q.notify({
              message: 'Success Confirm Picking List',
              icon: 'check',
              color: 'green'
            })
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
    async DispatchDN (e) {
      var _this = this
      if (_this.pickedDataSubmitId !== e.dn_id) {
        _this.$q.notify({
          message: e.dn_code + ' DN Status Is Not ' + _this.$t('outbound.pickedstock'),
          icon: 'close',
          color: 'negative'
        })
        throw new Error(e.dn_code + ' DN Status Is Not ' + _this.$t('outbound.pickedstock'))
      } else {
        _this.dispatchFormData = {
          dn_code: '',
          driver: ''
        }
        _this.dispatchFormData.dn_code = e.dn_code
        _this.dispatchFormData.driver = '-'
        _this.dispatchid = e.dn_id
      }
    },
    async dispatchDataSubmit () {
      var _this = this
      await postauth('dn/dispatch/' + _this.dispatchid + '/', _this.dispatchFormData)
        .then(res => {
          _this.table_list = []
          _this.getList()
          if (!res.detail) {
            _this.dispatchDataClear()
            _this.$q.notify({
              message: 'Success Dispatch',
              icon: 'check',
              color: 'green'
            })
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
    dispatchDataClear () {
      this.pickFormData = {
        dn_code: '',
        customer: '',
        goodsData: [],
        creater: ''
      }
      this.pickedid = 0
      this.pickedDataSubmitId = 0
      this.dispatchid = 0
      this.dispatchFormData = {
        dn_code: '',
        driver: ''
      }
    },
    async drainShopList () {
      let current = 1
      let total = 0
      let table_list = []
      let isDrained = false
      while (!isDrained) {
        const res = await getauth('shop/?page=' + '' + current, {})
        table_list = table_list.concat(res.results)
        total = res.count

        if (total <= table_list.length) {
          isDrained = true
        }
      }

      return table_list
    },
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
      _this.getSupplierList()
      _this.getHandleStatusList()
      _this.getList()
    } else {
      _this.authin = '0'
    }
  },
  mounted () {
    var _this = this
    // if (_this.$q.platform.is.electron) {
    //   _this.height = String(_this.$q.screen.height - 420) + 'px'
    // } else {
    //   _this.height = _this.$q.screen.height - 420 + '' + 'px'
    // }
    // _this.height = '800px'
  },
  updated () {},
  destroyed () {}
}
</script>
