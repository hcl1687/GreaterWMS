<template>
  <div class="shadow-24 q-pa-md" :style="{ height: height, background: 'white',borderRadius: '4px' }">
    <q-btn-group push>
      <q-btn :label="$t('upload_center.downloadshopskuskutemplate')" icon="cloud_download" @click="downloadshopskuskutemplate()">
        <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('upload_center.downloadshopskuskutemplate') }}</q-tooltip>
      </q-btn>
      <q-btn :label="$t('upload_center.downloadasntemplate')" icon="cloud_download" @click="downloadasntemplate()">
        <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('upload_center.downloadasntemplate') }}</q-tooltip>
      </q-btn>
    </q-btn-group>
    <div style="display: flex;">
      <div class="q-pt-md q-gutter-md row items-start">
        <q-uploader
          style="width:300px;height:200px"
          :url="shopskuskufile_pathname"
          method="post"
          :headers="headers"
          :field-name="file => 'file'"
          :label="$t('upload_center.uploadshopskuskufile')"
          accept=".xlsx,csv,xls/*"
          @rejected="onRejected"
          @added="getfileinfo"
        />
      </div>

      <div class="q-pa-md q-gutter-md row items-start">
        <q-uploader
          style="width:300px;height:200px"
          :url="asnfile_pathname"
          method="post"
          :headers="headers"
          :field-name="file => 'file'"
          :label="$t('upload_center.uploadasnfile')"
          accept=".xlsx,csv,xls/*"
          @rejected="onRejected"
          @added="getfileinfo"
        />
      </div>

    </div>
  </div>
</template>
<router-view />

<script>
import { baseurl } from 'boot/axios_request';
import { LocalStorage, openURL } from 'quasar';

export default {
  name: 'Pageupdateupload',
  data() {
    return {
      height: '',
      authorization: `Bearer ${LocalStorage.getItem('access_token')}`,
      token: LocalStorage.getItem('openid'),
      lang: LocalStorage.getItem('lang'),
      login_id: LocalStorage.getItem('login_id'),
      shopskuskufile_pathname: baseurl + '/uploadfile/shopskuskufileupdate/',
      asnfile_pathname: baseurl + '/uploadfile/asnfileadd/?mode=diff'
    };
  },
  computed: {
    headers () {
      return [
        { name: 'authorization', value: this.authorization },
        { name: 'token', value: this.token },
        { name: 'language', value: this.lang },
        { name: 'operator', value: this.login_id }
      ]
    }
  },
  methods: {
    checkFileType(files) {
      return files.filter(file => file.type === '.xlsx, xls,csv/*');
    },
    onRejected(rejectedEntries) {
      this.$q.notify({
        type: 'negative',
        message: `${rejectedEntries.length} file(s) did not pass validation constraints`
      });
    },
    getfileinfo(files) {
      console.log(1, files);
    },
    downloadshopskuskutemplate() {
      var _this = this;
      if (LocalStorage.has('auth')) {
        if (LocalStorage.has('lang')) {
          if (LocalStorage.getItem('lang') === 'zh-hans') {
            openURL(baseurl + '/media/upload_example/shopsku_sku_cn.xlsx');
          } else {
            openURL(baseurl + '/media/upload_example/shopsku_sku_en.xlsx');
          }
        } else {
          openURL(baseurl + '/media/upload_example/shopsku_sku_en.xlsx');
        }
      } else {
        _this.$q.notify({
          message: _this.$t('notice.loginerror'),
          color: 'negative',
          icon: 'warning'
        });
      }
    },
    downloadasntemplate() {
      var _this = this;
      if (LocalStorage.has('auth')) {
        if (LocalStorage.has('lang')) {
          if (LocalStorage.getItem('lang') === 'zh-hans') {
            openURL(baseurl + '/media/upload_example/asn_cn.xlsx');
          } else {
            openURL(baseurl + '/media/upload_example/asn_en.xlsx');
          }
        } else {
          openURL(baseurl + '/media/upload_example/asn_en.xlsx');
        }
      } else {
        _this.$q.notify({
          message: _this.$t('notice.loginerror'),
          color: 'negative',
          icon: 'warning'
        });
      }
    }
  },
  mounted() {
    var _this = this;
    if (_this.$q.platform.is.electron) {
      _this.height = String(_this.$q.screen.height - 185) + 'px';
    } else {
      _this.height = _this.$q.screen.height - 185 + '' + 'px';
    }
  },
  updated() {},
  destroyed() {}
};
</script>
